@ECHO OFF

REM Environment
CALL ../SetEnv.bat

REM Get CL Path
FOR /F "tokens=* USEBACKQ" %%F IN (`C:\Python36\python.exe ../getCL.py "%VSDIR%"`) DO (
SET CLPATH=%%F
)

REM 1] Full Path Include
REM 2] Full Path TR directory
REM 3] Run environment Visual Studio

REM If arg 3 is found Then VsDevCmd.bat
if "%~3"=="" (
	REM do nothing
) ELSE (
	CALL "%VCDIR%\VsDevCmd.bat"
)

SET FILENAME=Test.cpp
ECHO #include "%1" > %FILENAME%
SET TRDIR=%2

echo %TRDIR%

CALL "%CLPATH%" /c /I%TRDIR%Core\bati\WebServer\Cls /I%TRDIR%Core\BaseType /I%TRDIR%Core\..\LibOpenCascade\GlassMetre /I%TRDIR%Core\..\LibOpenCascade\include /I%TRDIR%TestsUnitaires\..\OPC_UA\OPC_All_Projects\OPC_UA_TIAMA\OPC_UA\Src /I%TRDIR%TestsUnitaires\..\Core\bati\Messagerie\OPC\ModelOPC /I%TRDIR%TestsUnitaires\..\OPC_UA\OPC_All_Projects\OPC_UA_TIAMA\OPC_UA\Src\lib /I"C:\Program Files\SiliconSoftware\Runtime5.7.1\include\\" /I%TRDIR%TestsUnitaires\..\OPC_UA\ModelOpcGenere\Include /I%TRDIR%TestsUnitaires\..\Core\bati\LibEdxC3\LIBS\Interface /I%TRDIR%TestsUnitaires\..\Core\bati\LibEdxC3\LIBS\vxWorks\LIBS_C3 /I%TRDIR%TestsUnitaires\..\Core\bati\LibEdxC3\LIBS\vxWorks\DRV_C3 /I%TRDIR%TestsUnitaires\..\Core\bati /I%TRDIR%TestsUnitaires\..\LibDataModel /I%TRDIR%TestsUnitaires\..\Core\ /I..\Core\. /I%TRDIR%TestsUnitaires\..\Core\bati\cls /I%TRDIR%TestsUnitaires\..\Core\CommunDet\cls /I%TRDIR%TestsUnitaires\..\Core\CommunDet\util /I"C:\Program Files\SiliconSoftware\Runtime5.7.1\include" /I"C:\Program Files\SiliconSoftware\Runtime5.7.1\lib\visualc" /I%TRDIR%TestsUnitaires\..\OPC_UA\OPC_All_Projects\OPC_UA_TIAMA\OPC_UA\Src /I%TRDIR%TestsUnitaires\..\OPC_UA\OPC_All_Projects\OPC_UA_TIAMA\OPC_UA\Src\lib /I%TRDIR%TestsUnitaires\..\OPC_UA\ModelOpcGenere\Include /I%TRDIR%TestsUnitaires\..\LibEmulationCalia\Interface /I%TRDIR%TestsUnitaires\..\LibEmulationCalia\Interface\x64\Release /I%TRDIR%TestsUnitaires\..\LibEmulationCalia\Interface\x64\Debug /I%TRDIR%TestsUnitaires\..\Core\bati\libedx /I%TRDIR%TestsUnitaires\..\LibEmulationCalia\vxWorks\WOS_MP\public\include /I%TRDIR%TestsUnitaires\..\MetriquesTR\LibrairieMetrique\src /I%TRDIR%TestsUnitaires\..\MetriquesTR\BDDTiama\CommunBDDTiama\src /Zi /nologo /W3 /WX- /diagnostics:column /MP /Od /D "CURRENT_CONFIGURATION=\"TU_D_G5\"" /D WIN32 /D _DEBUG /D EMULATION_PC /D EDX_EMBARQUE /D _CRT_SECURE_NO_DEPRECATE /D CPPUNIT_NO_MEM_TEST /D TESTS_UNITAIRES /D TIXML_USE_STL /D TIAMA_LIB /D _WINSOCK_DEPRECATED_NO_WARNINGS /D UA_ENABLE_AMALGAMATION /D _VC80_UPGRADE=0x0600 /D WIN32 /D DIRECTIVES_C4 /D UA_ENABLE_AMALGAMATION /D NOMINMAX /D EMULATION_PC /Gm- /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /std:c++17 /external:env:EXTERNAL_INCLUDE /external:W3 /experimental:external /Gd /TP /errorReport:queue %FILENAME% > "CompileOut.txt"

IF %ERRORLEVEL% NEQ 0 GOTO ERR
ECHO Compilation OK %1
EXIT /B 0
:ERR
ECHO Compilation Fail %1
EXIT /B 1