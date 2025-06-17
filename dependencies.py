import sys
import os
import ntpath
import pydot
import re


def getNameHeader(line):
    nameHeader = ""

    # If guillemet in line
    if "\"" in line:
        array = line.split("\"")
        nb = len(array)

        if (nb > 2):
            nameHeader = ntpath.basename(array[1])

    return nameHeader


def getInclude(path):
    print(path)

    # get date of the current file
    with open(path, "r") as f:
        data = f.readlines()

    includes = set()
    sharpInc = "#include"

    # For each lines
    for d in data:
        if sharpInc in d:
            nameHeader = getNameHeader(d)
            if len(nameHeader) > 0:
                includes.add(nameHeader)

    return list(includes)


def exportDepy(dep, name, nameSvg, updateSMD):
    # Two path
    pathSMS = name + ".sms"
    pathSMD = name + ".smd"
    fileSMS = open(pathSMS, "w")
    depNew = {}

    # ------------------------------------
    #             CLEAN DEP
    # ------------------------------------

    # For each file
    for file in dep:

        # For each dependencies
        for name in dep[file]:

            if not (name in dep.keys()):
                depNew[name] = []

        depNew[file] = dep[file]

    # ------------------------------------
    #               SMS
    # ------------------------------------

    # For each file
    for file in depNew:

        # Write header
        fileSMS.write('=' + file + '=')
        fileSMS.write("\n")

        # For each dependencies
        for name in depNew[file]:
            # Write current dependencies
            fileSMS.write("->" + name)
            fileSMS.write("\n")

    # ------------------------------------
    #               SMD
    # ------------------------------------

    # Update SMD from SVG
    if (updateSMD):
        # Create file
        print(pathSMD)
        fileSMD = open(pathSMD, "w")
        # Add header
        fileSMD.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fileSMD.write('    <body>                            \n')
        fileSMD.write('        <diagram>                     \n')

        # get date of the current file
        with open(nameSvg, "r") as f:
            data = f.readlines()

        # Find this into svg
        pattern = "</text>"
        # For each line
        for d in data:
            # If pattern into data
            if pattern in d:
                # Init
                x = 'x="0"'
                y = 'y="0"'
                id = 'NO_ID'

                # Search x="..."
                m = re.search('x="([0-9|.|-]*)"', d)
                if m != None:
                    x = (m.group(0))
                # Search y="..."
                m = re.search('y="([0-9|.|-]*)"', d)
                if m != None:
                    y = (m.group(0))
                # Get id
                m = re.search('>(.*)<\/text>', d)
                if m != None:
                    id = m.group(0)
                    id = id.replace("</text>", "")
                    id = id.replace(">", "")

                width = str(len(id) * 10)

                # Add current vertex
                fileSMD.write(
                    '<vertex id="' + id + '" background="#ffffcc" show_sub="True" show_actions="True" excluded="False">\n')
                fileSMD.write(
                    '  <rect x="0.0" y="0.0" width="' + width + '" height="25.0"/>                                     \n')
                fileSMD.write(
                    '  <pos ' + x + ' ' + y + '/>                                                                          \n')
                fileSMD.write(
                    '</vertex>                                                                                     \n')

        # Add footer
        fileSMD.write('    </diagram>     \n')
        fileSMD.write('</body>            \n')


def clean_file(name):
    name = name.replace(".hpp", "")
    name = name.replace(".h", "")
    name = name.replace("-", "_")
    return name


def is_good_file(root, name, modeFile):
    # If CALIA4 SMP
    if "VSB-CALIA4-SMP" in root:
        return False
    # If library
    if "library" in root:
        return False
    # If LibsSiso
    if "LibsSiso" in root:
        return False

    # Good if header
    answer = ".h" in name and (not ".hap" in name)

    # If mode source
    if modeFile == "source":
        # Good also if source
        answer = answer or ".cpp" in name

    # List of exception
    exception = [
        "ClsGigEVision.cpp"
    ]

    # If ok for this time
    if answer:
        # True only if the current name is not an exception
        answer = not name in exception

    # Return answer
    return answer


class DepBrowse():
    def __init__(self, dependencies):
        self.browsed = False
        self.level = 0
        self.parent = ""
        self.dependencies = dependencies


# Get structure browse dependencies
def GetDepBrowse(dep, listNode):
    # Init
    depBrowse = {}
    # For each key
    for key in dep.keys():
        # Add a new dep browse
        depBrowse[key] = DepBrowse(dep[key])
    # For each node
    for node in listNode:
        # If node is not into depBrowse
        if not node in depBrowse.keys():
            # Add an empty dep browse
            depBrowse[node] = DepBrowse([])

    # Return dependencies
    return depBrowse


# Get string path
def GetPath(DepBrowse, dep):
    if DepBrowse[dep].parent != "":
        return GetPath(DepBrowse, DepBrowse[dep].parent) + "->" + dep
    else:
        return dep


def AllPath(dependencies, listNode):
    ExcludedFiles = ["dumadll.h", "EDX_LibImage.h", "core_c.h", "wrSbc85xx.h", "EDX_IntCalia.h"]
    longPathActivated = False

    # For each key
    for key in dependencies.keys():

        # Get structure browse dependencies
        DepBrowse = GetDepBrowse(dependencies, listNode)
        ListDep = [key]
        level = 0

        # while not empty
        while len(ListDep) > 0:
            # Swap
            ListDepCur = ListDep
            ListDep = []

            # For each dep
            for dep in ListDepCur:
                # The current node is browsed
                DepBrowse[dep].browsed = True
                DepBrowse[dep].level = level

                # For each dependencies
                for depSon in DepBrowse[dep].dependencies:
                    # if the node is into dep browse
                    if (depSon in DepBrowse.keys()):
                        # if the node is ever browsed
                        if (DepBrowse[depSon].browsed):
                            # If dep and depSon is not equal
                            if (dep != depSon):
                                # If not excluded file
                                if (not depSon in ExcludedFiles):
                                    # Get string path
                                    pathLong = GetPath(DepBrowse, dep)
                                    pathShort = GetPath(DepBrowse, depSon)

                                    # Long path activated
                                    if (longPathActivated):
                                        print("-------------------")
                                        print("----Long path------")
                                        print(dep + "<->" + depSon)
                                        print(pathLong + "->" + depSon)
                                        print(pathShort)
                                        print("-------------------")
                        else:
                            # Add a new son to browse
                            DepBrowse[depSon].parent = dep
                            ListDep.append(depSon)
                    else:
                        # Big mistake
                        print("depSon not into dep browse")
                        print(depSon)
                        os.system.exit(-1)

            # Increment
            level = level + 1


def analyseDependencies(folderInput, folderDepy, modeFile, updateSMD):
    # Init
    dep = {}
    listNode = set()

    # For each files
    for root, dirs, files in os.walk(folderInput):
        for name in files:
            if is_good_file(root, name, modeFile):
                # Read header and get include
                path = root + "\\" + name
                incs = getInclude(path)

                # if source
                if ".cpp" in name:
                    # replace source to header
                    name = name.replace(".cpp", ".h")
                    # If name into incs
                    if name in incs:
                        # remove from the list
                        incs.remove(name)

                # For each incs
                for inc in incs:
                    # Add current inc
                    listNode.add(inc)
                # Add current name
                listNode.add(name)

                # If dependencies
                if len(incs) > 0:
                    # If not first file
                    if name in dep:
                        for inc in incs:
                            dep[name].add(inc)
                    else:
                        dep[name] = set(incs)

    # Display all path from a node to an other
    AllPath(dep, listNode)

    # -------------- Error Analyse -------------------

    print("--------------------")
    print("file include himself")
    # For each file
    for file in dep:
        for name in dep[file]:
            if name == file:
                print(name)

    print("")
    print("------------------------------------")
    print("file A include file B and vice versa")
    # For each file
    for file in dep:
        for name in dep[file]:
            if name in dep.keys():
                if file in dep[name]:
                    print(name + "<->" + file)

    print("")
    print("------------------------------------")
    print("file A include file B include file C but file A include file C")

    # For each fileA in list of file
    for fileA in dep:

        # For each fileB in fileA dep
        for fileB in dep[fileA]:

            # dep in fileB
            if fileB in dep.keys():

                # For each fileC in fileB dep
                for fileC in dep[fileB]:

                    # For each fileD in fileA dep
                    for fileD in dep[fileA]:

                        # If fileD equal fileC
                        if (fileD == fileC):

                            # If A B C all different
                            if (fileA != fileB and fileA != fileC and fileB != fileC):
                                print("dependencies")
                                print(fileA + "<->" + fileB + "<->" + fileC)
                                print(fileA + "<->" + fileC)

    # -------------- Expor Graph -------------------

    # Output
    pathOutput = "dep.dot"
    out = open(pathOutput, "w")

    # Header
    out.write("digraph G {" + "\n")

    # Init
    depNew = {}

    # For each file
    for file in dep:

        # Init tab
        arrayFile = []
        fileOnly = clean_file(file)

        # For each dependencies
        for name in dep[file]:
            if name in dep.keys():
                if len(dep[name]) > 0:
                    # Compute name and store into new dependencies
                    nameOnly = clean_file(name)
                    out.write("\"" + fileOnly + "\" -> \"" + nameOnly + "\"\n")
                    arrayFile.append(nameOnly)

        # If not empty
        if (len(arrayFile) > 0):
            # Add the current file
            depNew[fileOnly] = arrayFile

    print("TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
    print("TOTOTO")
    print(str(depNew))
    # Footer
    out.write("}" + "\n")
    out.close()

    # Get graph from dot
    graphSvgName = 'dep.svg'
    (graph,) = pydot.graph_from_dot_file(pathOutput)
    graph.write_svg(graphSvgName)

    # -------------- Expor Graph depy -------------------

    exportDepy(depNew, folderDepy, graphSvgName, updateSMD)


def dependMain(folderInput):

    # Mode file
    folderDepy = "Img\\Img"
    modeFile = "source"
    modeFile = "header"

    updateSMD = False

    # Change this variable to reset SMD
    analyseDependencies(folderInput, folderDepy, modeFile, updateSMD)

# Test function
def dependMainPy(folderInput):

    # 0) Define variables
    dot_name = "ManagerGuiSimple"
    dot_name_class_ext = 'classes_' + dot_name + '.dot'
    folder_itb = 'STB/STB'

    # 1) Generate file class_ManagerGuiSimple.dot
    cmd = "Pyreverse -o dot -p " + dot_name + " -A -my -S -k -f ALL " + folderInput + "manager_gui.py"
    os.system(cmd)

    # 2) Update sms smd
    update_sms_smd_from_dot(dot_name_class_ext, folder_itb)

def GetDependenciesPathCode():
    str = "D:\\Dev\\TR_TU4\\Core\\"
    str = "C:\\D\\Img\\qt\\img\\"
    str = "C:\\D\\Dev\\STB\\src\\"
    return str

# Clean class name to have just the right part of the class name
def clean_class_name(class_name):
    # split with '.'
    array = class_name.split('.')
    # Return last value
    return array[len(array) - 1]


# Get dependencies from dot file
def get_dependencies_from_dot(dot_name):
    # Init
    dependencies = {}
    dep_str = '" -> "'

    # get date of the current file
    with open(dot_name, "r") as f:
        data = f.readlines()

    # For each line
    for line in data:
        # Split line
        a_dep_b = line.split(dep_str)
        # If exactly two values
        if len(a_dep_b) == 2:
            # Get class name A
            class_a = clean_class_name(a_dep_b[0].replace('"', ''))
            # Get class name B
            class_b = clean_class_name(a_dep_b[1].split('"')[0])
            # If first occurency of class A
            if class_a not in dependencies.keys():
                # Create new item
                dependencies[class_a] = [class_b]
            else:
                # Add new dependency
                dependencies[class_a].append(class_b)

    # Return answer
    return dependencies


def update_sms_smd_from_dot(dot_name, folder_depy):
    # Get dependencies from dot file
    dependencies = get_dependencies_from_dot(dot_name)

    # Get graph from dot
    graph_svg_name = 'dep.svg'
    (graph,) = pydot.graph_from_dot_file(dot_name)
    graph.write_svg(graph_svg_name)

    # Export SMS and SMD
    update_smd = False
    exportDepy(dependencies, folder_depy, graph_svg_name, update_smd)


# -----------------------------------------
#           Old using
# -----------------------------------------

def main_dep_cpp():
    if len(sys.argv) > 1:
        folderInput = sys.argv[1]

    folderInput = GetDependenciesPathCode()
    print("Arguments ", folderInput)
    dependMain(folderInput)


# Test function
def test_update_from_dot():

    folderInput = GetDependenciesPathCode()
    dependMainPy(folderInput)

# Call test function
test_update_from_dot()
# main_dep_cpp()