import os


class DepBrowse:
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


def display_dependencies(dependencies, listNode):
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

