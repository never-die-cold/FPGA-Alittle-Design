@echo off
setlocal
if not defined VIVADO set "VIVADO=D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat"
set "SCRIPT=%~dp0program_soc.tcl"

if not exist "%VIVADO%" (
    echo PROGRAM FAILED: Vivado not found at %VIVADO%
    exit /b 1
)

call "%VIVADO%" -mode batch -source "%SCRIPT%" -tclargs %*
exit /b %ERRORLEVEL%
