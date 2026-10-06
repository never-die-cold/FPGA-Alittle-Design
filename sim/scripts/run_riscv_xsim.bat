@echo off
setlocal EnableExtensions

rem RISC-V v1 XSim cross-check. Run from Windows PowerShell or cmd.exe.
rem Usage: sim\scripts\run_riscv_xsim.bat [muldiv|fwd|nofwd|muldiv_fwd|muldiv_nofwd|all]
set "MODE=%~1"
if not defined MODE set "MODE=all"
set "VIVADO_BIN=%RISCV_VIVADO_BIN%"
if not defined VIVADO_BIN set "VIVADO_BIN=D:\vivado\2026.1\Vivado\bin"

for %%T in (xvlog xelab xsim) do (
    if not exist "%VIVADO_BIN%\%%T.bat" (
        echo ERROR: missing %VIVADO_BIN%\%%T.bat
        exit /b 1
    )
)

rem pushd maps a WSL UNC repository path to a temporary drive for cmd.exe.
pushd "%~dp0\.." || exit /b 1
set "OUT=build\riscv\xsim"
if not exist "%OUT%" mkdir "%OUT%"

echo == xvlog ==
type nul > "%OUT%\compile.log"
for %%F in (..\src\riscv\*.v riscv\tb_muldiv.v riscv\tb_core_fwd.v riscv\tb_core_v1_muldiv_flow.v) do (
    call "%VIVADO_BIN%\xvlog.bat" -sv "%%F" >> "%OUT%\compile.log" 2>&1
    if errorlevel 1 (
        type "%OUT%\compile.log"
        echo ERROR: xvlog failed on %%F
        popd
        exit /b 1
    )
)

if /i "%MODE%"=="muldiv"       call :run tb_muldiv tb_muldiv_xsim "" || goto :fail
if /i "%MODE%"=="fwd"          call :run tb_core_fwd tb_core_fwd_xsim "ENABLE_FORWARDING=1" || goto :fail
if /i "%MODE%"=="nofwd"        call :run tb_core_fwd tb_core_nofwd_xsim "ENABLE_FORWARDING=0" || goto :fail
if /i "%MODE%"=="muldiv_fwd"   call :run tb_core_v1_muldiv_flow tb_muldiv_fwd_xsim "ENABLE_FORWARDING=1" || goto :fail
if /i "%MODE%"=="muldiv_nofwd" call :run tb_core_v1_muldiv_flow tb_muldiv_nofwd_xsim "ENABLE_FORWARDING=0" || goto :fail
if /i "%MODE%"=="all" (
    call :run tb_muldiv tb_muldiv_xsim "" || goto :fail
    call :run tb_core_fwd tb_core_fwd_xsim "ENABLE_FORWARDING=1" || goto :fail
    call :run tb_core_fwd tb_core_nofwd_xsim "ENABLE_FORWARDING=0" || goto :fail
    call :run tb_core_v1_muldiv_flow tb_muldiv_fwd_xsim "ENABLE_FORWARDING=1" || goto :fail
    call :run tb_core_v1_muldiv_flow tb_muldiv_nofwd_xsim "ENABLE_FORWARDING=0" || goto :fail
)
if /i not "%MODE%"=="muldiv" if /i not "%MODE%"=="fwd" if /i not "%MODE%"=="nofwd" if /i not "%MODE%"=="muldiv_fwd" if /i not "%MODE%"=="muldiv_nofwd" if /i not "%MODE%"=="all" (
    echo ERROR: mode must be muldiv, fwd, nofwd, muldiv_fwd, muldiv_nofwd, or all
    goto :fail
)

echo PASS: RISC-V XSim mode %MODE%
popd
exit /b 0

:run
set "TOP=%~1"
set "SNAP=%~2"
set "GENERIC=%~3"
echo == %SNAP% ==
if defined GENERIC (
    call "%VIVADO_BIN%\xelab.bat" work.%TOP% -generic_top "%GENERIC%" -s %SNAP% > "%OUT%\%SNAP%-elab.log" 2>&1
) else (
    call "%VIVADO_BIN%\xelab.bat" work.%TOP% -s %SNAP% > "%OUT%\%SNAP%-elab.log" 2>&1
)
if errorlevel 1 (
    type "%OUT%\%SNAP%-elab.log"
    exit /b 1
)
call "%VIVADO_BIN%\xsim.bat" %SNAP% -R > "%OUT%\%SNAP%.log" 2>&1
if errorlevel 1 (
    type "%OUT%\%SNAP%.log"
    exit /b 1
)
findstr /c:"FAIL:" "%OUT%\%SNAP%.log" >nul
if not errorlevel 1 (
    type "%OUT%\%SNAP%.log"
    exit /b 1
)
findstr /c:"PASS:" "%OUT%\%SNAP%.log" >nul
if errorlevel 1 (
    type "%OUT%\%SNAP%.log"
    exit /b 1
)
findstr /c:"PASS:" "%OUT%\%SNAP%.log"
exit /b 0

:fail
echo ERROR: RISC-V XSim mode %MODE% failed
popd
exit /b 1
