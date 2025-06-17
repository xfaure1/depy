import os
import ntpath

def getNameHeader(line):

    nameHeader = ""
    
    #If guillemet in line
    if "\"" in line:
        array = line.split("\"")
        nb = len(array)
        
        if (nb>2):
            nameHeader = ntpath.basename(array[1])

    return nameHeader
    
def getInclude(path):

    #get date of the current file
    with open(path, "r") as f:
        data = f.readlines()
    
    includes = set()
    sharpInc = "#include"
    
    #For each lines
    for d in data:
        if sharpInc in d:
            nameHeader = getNameHeader(d)
            if len(nameHeader)>0:
                includes.add(nameHeader)
        
    return list(includes)
     
def is_good_file(root, name):

    #If VIP_CALIA4_SMP
    if "VIP_CALIA4_SMP" in root:
        return False
    #If CALIA4 SMP
    if "VSB-CALIA4-SMP" in root:
        return False
    #If library
    if "library" in root:
        return False
    #If LibsSiso
    if "LibsSiso" in root:
        return False
        
    #Good if header
    return ".h" in name and (not ".hap" in name)
    
def GetCmdsErrorFileName():

    return "cmdsError.txt"

def compileHeaders(TR_DIR):

    #Define the commande compile bat
    CMD_COMPILE_BAT = "..\\compileOneHeader.bat"
    
    #File name commands error
    cmdsErrorFileName = GetCmdsErrorFileName()   
    includeErrorFileName = "incsError.txt"       
    cmdsError = {}
    cmds = []
    
    #if file errors exist
    if os.path.exists(cmdsErrorFileName) :
        
        #Read all lines
        with open(cmdsErrorFileName, "r") as f:
            cmds = f.readlines()
    
    else:
        
        #Init
        folder_input = TR_DIR + "Core\\"

        #For each files
        for root, dirs, files in os.walk(folder_input):
            for name in files:
                if is_good_file(root, name):
                    #Read header and get include
                    path = root + "\\" + name
                
                    #Compute commmand / print / execute
                    cmd = CMD_COMPILE_BAT + " " + path + " " + TR_DIR
                    cmds.append(cmd)
        
    #For each cmd
    for cmd in cmds:
    
        #execute command
        cmd = cmd.replace("\n", "")
        status = os.system(cmd)
        
        #If status fail
        if status != 0:
            cmdsError[cmd] = cmd
            
            
    # --------------------------------------
    #           Write compilation
    # --------------------------------------
    
    
    #if command errors is found
    if len(cmdsError)>0:
        #Open file
        f1 = open(cmdsErrorFileName, "w")
        f2 = open(includeErrorFileName, "w")
        
        #For each cmd fail
        for file in cmdsError:
            #Write file
            f1.write(cmdsError[file] + "\n") 
            #Delete path -> " D:"
            CmdPath = file.split("h D:")[0]
            #Delete cmd and add #include
            Path = CmdPath.replace(CMD_COMPILE_BAT + " ", "")
            #Write include line
            f2.write("#include \"" + Path + "h\"\n") 
    else: 
        #if file errors exist
        if os.path.exists(cmdsErrorFileName) :        
            #Remove file errors
            os.remove(cmdsErrorFileName) 
