param([string]$Vivado = "D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$cross = @("riscv32-unknown-elf-", "riscv64-unknown-elf-") | Where-Object {
    Get-Command "${_}gcc.exe" -ErrorAction SilentlyContinue
} | Select-Object -First 1
if (-not $cross) { throw "Missing riscv32/riscv64 gcc; cop_job.hex was not refreshed" }
$make = Get-Command mingw32-make.exe, make.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $make) { throw "Missing mingw32-make/make" }
& $make.Source -B -C src/riscv_fw "CROSS=$cross" cop_job.hex
if ($LASTEXITCODE -ne 0) { throw "cop_job.hex rebuild failed" }
& $Vivado -mode batch -source build/build_soc.tcl -tclargs 40 fwd
if ($LASTEXITCODE -ne 0) { throw "ENABLE_COP=0 baseline failed; production build not started" }
& $Vivado -mode batch -source build/build_pynq_cop_gate.tcl
exit $LASTEXITCODE
