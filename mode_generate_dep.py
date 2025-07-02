import os.path
import re
import sys
import pydot

from constant_value import MODE_GENERATE_PY, MODE_GENERATE_DOT, ALL_MODES, MODE_GENERATE_CPP_HEADER, \
    MODE_GENERATE_CPP_SRC, MODE_GENERATE_PHP, MODE_GENERATE_XML, MODE_GENERATE_NO


# ---------------------------------------------
# Four Modes :
# -> Cpp Source
# -> Cpp Header
# -> Php
# -> Python
# ---------------------------------------------

class ModeGenerateDep:

    def is_python(self):
        # Return true if python mode
        return self.mode == MODE_GENERATE_PY

    def is_dot(self):
        # Return true if dot mode
        return self.mode == MODE_GENERATE_DOT

    def __init__(self, mode):
        # Init attributes
        self.mode = mode
        self.update_smd = False

        # If mode is not found
        if self.mode not in ALL_MODES:
            # Fatal error
            print("Mode is not found : ")
            print(self.mode)
            print(str(ALL_MODES))
            sys.exit(-1)

        # Init dot name and base
        self.dot_name_prefix = ""
        self.dot_name = "dependencies"

        # If python mode
        if self.is_python():
            # Update prefix
            self.dot_name_prefix = 'classes_'

    def get_dot_name_path(self):
        path_dot = self.dot_name_prefix + self.dot_name + ".dot"
        if self.is_dot():
            path_dot = os.path.join(self.get_dep_path_code(), path_dot)
        return path_dot

    def get_sms_smd_name(self):
        return os.path.join(self.mode, self.mode)

    def get_dep_path_code(self):
        if self.mode == MODE_GENERATE_CPP_HEADER:
            return "/home/xfaure/Desktop/GIT/OMEGA_Embedded_Simu/exec/git/OMEGA_Embedded_SW/inc/ExR/Model/Autotests"
        if self.mode == MODE_GENERATE_CPP_SRC:
            return "C:\\D\\Img\\qt\\img\\"
        if self.is_python():
            return "C:\\D\\Dev\\STB\\src\\"
        if self.is_dot():
            return "/home/xfaure/Bureau/GIT/OMEGA_Embedded_Simu/tools/"
        if self.mode == MODE_GENERATE_PHP or self.mode == MODE_GENERATE_XML:
            return "C:\\D\\Dev\\Mea\\src\\Symbio\\"
        # Return not found
        return "NOT_FOUND_SOURCE_CODE"

    def is_enabled_generator(self):
        return self.mode != MODE_GENERATE_NO

    def generate_sms_smd(self, dep):

        # Get graph from dot
        nameSvg = 'dep.svg'
        (graph,) = pydot.graph_from_dot_file(self.get_dot_name_path())

        try:
            graph.write_svg(nameSvg)
        except FileNotFoundError as mystr:
            print("dot is not installed in your computer")
            print("sudo apt install graphviz")
            print(mystr)
            sys.exit(-1)

        # Two path
        name = self.get_sms_smd_name()
        pathSMS = name + ".sms"
        pathSMD = name + ".smd"
        fileSMS = open(pathSMS, "w")
        depNew = {}

        # ------------------------------------
        #             CLEAN DEP
        # ------------------------------------

        # For each file
        for file in dep:

            # For each dependency
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

            # For each dependency
            for name in depNew[file]:
                # Write current dependencies
                fileSMS.write("->" + name)
                fileSMS.write("\n")

        # Close file
        fileSMS.close()

        # ------------------------------------
        #               SMD
        # ------------------------------------

        # Test if File exist
        is_smd_found = os.path.isfile(pathSMD)
        # Update SMD from SVG
        if self.update_smd or not is_smd_found:
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
                    vertex_str = '<vertex id="'
                    vertex_option = '" background="#ffffcc" show_sub="True" show_actions="True" excluded="False">'
                    fileSMD.write(vertex_str + id + vertex_option + '\n')
                    fileSMD.write('  <rect x="0.0" y="0.0" width="' + width + '" height="25.0"/>\n')
                    fileSMD.write('  <pos ' + x + ' ' + y + '/>\n')
                    fileSMD.write('</vertex>\n')

            # Add footer
            fileSMD.write('    </diagram>     \n')
            fileSMD.write('</body>            \n')

            # Close file
            fileSMD.close()

