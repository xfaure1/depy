import os

def GetCLPath(VSDIR):

    #Get msvc directory
    MSVCDIR =  VSDIR + "\\VC\\Tools\\MSVC\\"
    
    #This number can be updated frequently
    DIR_NUMBER = ""
    
    #Get directory
    for root, dirs, files in os.walk(MSVCDIR):
        for mydir in dirs:
            DIR_NUMBER = mydir
            break
        break
    
    #If dir is not found
    if DIR_NUMBER == "":
        print("Error : DIR_NUMBER is not found")
        print("Check this path : ")
        print(VSDIR)
        os.sys.exit(-1)
    
    #Compute the end of path    
    return MSVCDIR + DIR_NUMBER + "\\bin\\HostX64\\x64\\CL.exe"
    
print(GetCLPath(os.sys.argv[1]))