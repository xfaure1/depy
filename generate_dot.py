import os
import ntpath
import re

from browse_dep import display_dependencies
from mode_generate_dep import ModeGenerateDep


# -----------------------------------------------
#            MODE CPP / PHP
# -----------------------------------------------


def get_dependencies_line_cpp(line):
    nameHeader = ""

    # If guillemot in line
    if "\"" in line:
        array = line.split("\"")
        nb = len(array)

        if nb > 2:
            nameHeader = ntpath.basename(array[1])

    return nameHeader


def get_dependencies_file_cpp(path):
    print(path)

    # get date of the current file
    with open(path, "r") as f:
        data = f.readlines()

    includes = set()
    sharpInc = "#include"

    # For each lines
    for d in data:
        if sharpInc in d:
            nameHeader = get_dependencies_line_cpp(d)
            if len(nameHeader) > 0:
                includes.add(nameHeader)

    return list(includes)


# -------------- PHP Mode ----------------------


def get_dependencies_line_php(line):
    nameSpace = ""

    # Split with \\
    anti_slash = "\\"
    array_line = line.split(anti_slash)

    # If almost two element
    if len(array_line) > 1:
        # Get last one with semi col
        nameSpace = array_line[len(array_line) - 1].split(";")[0]

    return nameSpace


def get_dependencies_file_php(path):
    # get date of the current file
    with open(path, "r", encoding='utf-8') as f:
        data = f.readlines()

    includes = set()
    sharpInc = "use "

    # For each lines
    for d in data:
        if sharpInc in d:
            nameHeader = get_dependencies_line_php(d)
            if len(nameHeader) > 0:
                includes.add(nameHeader)

    return list(includes)


# -------------- XML Mode ----------------------


def get_dependencies_file_xml(path):
    # get data of the current file
    with open(path, "r", encoding='utf-8') as f:
        data = f.readlines()

    # Regular expression
    regexp_service = ".*<service.*id=\"(.*)\".*class=\"(.*)\".*"
    regexp_dependency = ".*<argument.*id=\"(.*)\".*"
    current_name = "NOT_FOUND"
    all_dependencies = {}
    dependencies = []

    # For each lines
    for d in data:
        # search if service is found
        search_service = re.search(regexp_service, d)
        # If new services is found
        if search_service is not None:
            # If dependencies are found
            if len(dependencies) > 0:
                # Add couple name <-> dependencies
                all_dependencies[current_name] = dependencies
                dependencies = []
            # Update name of the current service
            current_name = search_service[1].replace(".","-")
        else:
            # search if dependency is found
            search_dependency = re.search(regexp_dependency, d)
            # If new dependency is found
            if search_dependency is not None:
                # Add new dependency
                dependencies.append(search_dependency[1].replace(".","-"))

    # If dependencies are found
    if len(dependencies) > 0:
        # Add couple name <-> dependencies
        all_dependencies[current_name] = dependencies
        dependencies = []

    # Return all dependencies
    return all_dependencies


# --------- For each mode -----------------------


def get_nb_line(path):
    # get date of the current file
    with open(path, "r", encoding='utf-8') as f:
        data = f.readlines()

    return len(data)


def get_dependencies_file(path, mode_file):
    if mode_file == ModeGenerateDep.MODE_GENERATE_PHP:
        return get_dependencies_file_php(path)
    if mode_file == ModeGenerateDep.MODE_GENERATE_XML:
        return get_dependencies_file_xml(path)
    if mode_file == ModeGenerateDep.MODE_GENERATE_CPP_SRC or mode_file == ModeGenerateDep.MODE_GENERATE_CPP_HEADER:
        return get_dependencies_file_cpp(path)
    return {}


def clean_file(name):
    name = name.replace(".hpp", "")
    name = name.replace(".h", "")
    name = name.replace("-", "_")
    return name


def is_good_file(root, name, mode_file):
    # If CALIA4 SMP
    if "VSB-CALIA4-SMP" in root:
        return False
    # If library
    if "library" in root:
        return False
    # If LibsSiso
    if "LibsSiso" in root:
        return False

    # If mode XML
    if mode_file == ModeGenerateDep.MODE_GENERATE_XML:
        # PHP in name
        return "manager.xml" in name or "admin-sonata.xml" in name

    # If mode PHP
    if mode_file == ModeGenerateDep.MODE_GENERATE_PHP:
        # PHP in name
        return ".php" in name

    # Good if header
    answer = ".h" in name and (not ".hap" in name)

    # If mode source
    if mode_file == ModeGenerateDep.MODE_GENERATE_CPP_SRC:
        # Good also if source
        answer = answer or ".cpp" in name

    # List of exception
    exception = [
        "ClsGigEVision.cpp"
    ]

    # If ok for this time
    if answer:
        # True only if the current name is not an exception
        answer = name not in exception

    # Return answer
    return answer


# -------------------------------
#   Main function from source
# -------------------------------


def generate_dot_from_source(folder_input, dot_name_path, mode_file):
    # Init
    dep = {}
    listNode = set()
    nb_line_tot = 0
    nb_files = 0
    nb_dir = 0

    # For each files
    for root, dirs, files in os.walk(folder_input):
        nb_dir = nb_dir + len(dirs)
        # For each file into current folder
        for name in files:
            # If the file matches with current mode
            if is_good_file(root, name, mode_file):
                # Read header and get include
                path = os.path.join(root, name)
                dependencies = get_dependencies_file(path, mode_file)

                # Statistics
                nb_line = get_nb_line(path)
                nb_line_tot = nb_line_tot + nb_line
                nb_files = nb_files + 1

                # Clean name
                name = name.replace(".php", "")

                # if source
                if ".cpp" in name:
                    # replace source to header
                    name = name.replace(".cpp", ".h")
                    # If name into incs
                    if name in dependencies:
                        # remove from the list
                        dependencies.remove(name)

                # If XML mode
                if mode_file == ModeGenerateDep.MODE_GENERATE_XML:
                    # Variables dependencies is already a dictionary
                    # It's build into get_dependencies_file_xml
                    all_dependencies = dependencies
                else:
                    # Create a dictionary with just one element to be homogenous
                    all_dependencies = {name: dependencies}

                # For each couple current_name <-> dependencies
                for current_name, dependencies in all_dependencies.items():
                    # For each incs
                    for my_dependency in dependencies:
                        # Add current inc
                        listNode.add(my_dependency)
                    # Add current name
                    listNode.add(current_name)

                    # If dependencies
                    if len(dependencies) > 0:
                        # If not first file
                        if current_name in dep:
                            for my_dependency in dependencies:
                                dep[current_name].add(my_dependency)
                        else:
                            dep[current_name] = set(dependencies)

    # Display all path from a node to an other
    display_dependencies(dep, listNode)

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
                        if fileD == fileC:

                            # If A B C all different
                            if fileA != fileB and fileA != fileC and fileB != fileC:
                                print("dependencies")
                                print(fileA + "<->" + fileB + "<->" + fileC)
                                print(fileA + "<->" + fileC)

    # -------------- Export Graph -------------------

    # Output
    out = open(dot_name_path, "w")

    # Header
    out.write("digraph G {" + "\n")

    # Init
    depNew = {}

    # For each file
    for file in dep:

        # Init tab
        array_file = []
        fileOnly = clean_file(file)

        # For each dependency
        for name in dep[file]:
            if name in dep.keys():
                if len(dep[name]) > 0:
                    # Compute name and store into new dependencies
                    nameOnly = clean_file(name)
                    out.write("\"" + fileOnly + "\" -> \"" + nameOnly + "\"\n")
                    array_file.append(nameOnly)

        # If not empty
        if len(array_file) > 0:
            # Add the current file
            depNew[fileOnly] = array_file

    # Footer
    out.write("}" + "\n")
    out.close()

    # Information
    print("Nb Lines = ", nb_line_tot)
    print("Nb Files = ", nb_files)
    print("Nb Folders = ", nb_dir)

    # Return the dependencies
    return depNew


# -----------------------------------------------
#            MODE PYTHON
# -----------------------------------------------


# Clean class name to have just the right part of the class name
def clean_class_name(class_name):
    # split with '.'
    array = class_name.split('.')
    # Return last value
    return array[len(array) - 1].replace("-", "_")


# Get dependencies from dot file
# Used if the dot is generated by PyReverse
def get_dep_from_dot(dot_name):
    # Init
    dependencies = {}
    dep_str = '" -> "'

    # get date of the current file
    with open(dot_name, "r") as f:
        data = f.readlines()

    # Output
    file_dot_name = open(dot_name, "w")

    # For each line
    for line in data:
        # Split line
        a_dep_b = line.split(dep_str)
        # If exactly two values
        if len(a_dep_b) == 2:
            # Get class name A
            class_a_orig = a_dep_b[0].split('"')[1]
            class_a = clean_class_name(class_a_orig)
            # Get class name B
            class_b_orig = a_dep_b[1].split('"')[0]
            class_b = clean_class_name(class_b_orig)
            # If first occurrence of class A
            if class_a not in dependencies.keys():
                # Create new item
                dependencies[class_a] = [class_b]
            else:
                # Add new dependency
                dependencies[class_a].append(class_b)

            line = line.replace(class_a_orig, class_a)
            line = line.replace(class_b_orig, class_b)

        # Write line
        file_dot_name.write(line)

    # Return answer
    return dependencies


def generate_dot_from_pyreverse(folder_input, dot_name_path, dot_name):
    # 1) Generate dot file from source python
    cmd = "Pyreverse -o dot -p " + dot_name + " -A -my -S -k -f ALL " + folder_input + "gui\\gui_manager.py"
    os.system(cmd)
    # 2) Return the dependencies
    return get_dep_from_dot(dot_name_path)
