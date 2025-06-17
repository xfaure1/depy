@ECHO OFF

REM init folder TR
set rootFolderTR=

REM If arg 1 is found Then 
if "%~1"=="" (
	REM do nothing
) ELSE (
	set rootFolderTR=%1
)

REM Environment
CALL SetEnv.bat
CALL "%VCDIR%\VsDevCmd.bat"

REM IF %ERRORLEVEL% NEQ 0 GOTO ERR
ECHO Environment is ready

REM Create subdirectory
MKDIR Tmp
CD Tmp
DEL *.obj

REM Run compaign compilation for all headers
echo C:\Python36\python.exe ..\compileHeaders.py %rootFolderTR%
CALL C:\Python36\python.exe ..\compileHeaders.py %rootFolderTR%

REM Go back directory
CD ..
ECHO Environment is clean
EXIT /B 0

:ERR
ECHO Environment is in error
EXIT /B 1