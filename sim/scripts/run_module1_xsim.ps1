# Same repository tb/hex/golden as run_iverilog.sh; compare post-optimization counters.
param(
    [string]$VivadoBin = $env:RISCV_VIVADO_BIN,
    [string]$LogDir,
    [string]$IcarusLog
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (!$VivadoBin) { $VivadoBin = 'D:/Vivado_downloads/2026.1/Vivado/bin' }
if (!$LogDir) { $LogDir = Join-Path $repo ('data/logs/' + (Get-Date -Format 'yyyy-MM-dd-HHmmss') + '-module1-xsim') }
if (!$IcarusLog) { $IcarusLog = Join-Path $repo 'data/logs/2026-10-07-partC-postopt/iverilog-all.log' }
foreach ($tool in 'xvlog', 'xelab', 'xsim') {
    if (!(Test-Path (Join-Path $VivadoBin "$tool.bat"))) { throw "Missing tool: $tool in $VivadoBin" }
}
if (Test-Path $LogDir) { throw "Use a new LogDir to preserve previous evidence: $LogDir" }
$reference = Get-Content -Raw $IcarusLog
$expectedPass = [regex]::Matches($reference, '(?m)^PASS: coremark[^\r\n]*')
$expectedBht = [regex]::Matches($reference, '(?m)^BHT:[^\r\n]*')
if ($expectedPass.Count -ne 4 -or $expectedBht.Count -ne 4) { throw 'Reference must contain exactly four CoreMark profiles' }
New-Item -ItemType Directory -Path $LogDir | Out-Null
$LogDir = (Resolve-Path $LogDir).Path
$work = Join-Path $repo 'sim/build/module1-xsim'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$sources = @(Get-ChildItem (Join-Path $repo 'src/riscv/*.v') | Sort-Object Name | ForEach-Object FullName)
$sources += Join-Path $repo 'sim/riscv/tb_core_coremark.v'
@{
    repo_commit = (& git -C $repo rev-parse HEAD)
    sources = @($sources | Get-FileHash -Algorithm SHA256 | Select-Object Path, Hash)
    hex = (Get-FileHash (Join-Path $repo 'src/riscv_fw/coremark.hex')).Hash
    reference = (Get-FileHash $IcarusLog).Hash
    vivado_bin = $VivadoBin
} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $LogDir 'environment.json') -Encoding utf8
function Invoke-XTool([string]$Tool, [string[]]$ToolArgs, [string]$Name) {
    $log = Join-Path $LogDir "$Name.log"
    & (Join-Path $VivadoBin "$Tool.bat") @ToolArgs *> $log
    if ($LASTEXITCODE -ne 0) { throw "$Tool failed ($LASTEXITCODE): $log" }
}
$profiles = @(@('nofwd', 0, 0), @('fwd', 1, 0), @('bht1', 1, 1), @('bht2', 1, 2))
$golden = @('hex=../../../src/riscv_fw/coremark.hex', 'exp_exit=0', 'timer_addr=80008000',
    'max_cycles=50000000', 'exp_tohost=34713', 'exp_iter=32', 'exp_seedcrc=e9f5',
    'exp_crclist=e714', 'exp_crcmatrix=1fd7', 'exp_crcstate=8e3a', 'exp_crcfinal=8799')
Push-Location $work
try {
    Invoke-XTool 'xvlog' (@('-sv') + $sources) 'compile'
    for ($i = 0; $i -lt $profiles.Count; $i++) {
        $profile = $profiles[$i]; $snapshot = 'module1_' + $profile[0]
        Write-Output "== XSim $($profile[0]) =="
        Invoke-XTool 'xelab' @('work.tb_core_coremark', '-generic_top', ('"ENABLE_FORWARDING=' + $profile[1] + '"'),
            '-generic_top', ('"BHT_MODE=' + $profile[2] + '"'), '-s', $snapshot) "$snapshot-elab"
        $runArgs = @($snapshot, '-R')
        foreach ($arg in $golden) { $runArgs += @('-testplusarg', ('"' + $arg + '"')) }
        Invoke-XTool 'xsim' $runArgs $snapshot
        $result = Get-Content -Raw (Join-Path $LogDir "$snapshot.log")
        if ($result -match 'FAIL:|FATAL:') { throw "Simulation rejected: $snapshot" }
        $actualPass = [regex]::Matches($result, '(?m)^PASS: coremark[^\r\n]*')
        $actualBht = [regex]::Matches($result, '(?m)^BHT:[^\r\n]*')
        if ($actualPass.Count -ne 1 -or $actualBht.Count -ne 1 -or
            $actualPass[0].Value -ne $expectedPass[$i].Value -or
            $actualBht[0].Value -ne $expectedBht[$i].Value) { throw "Icarus/XSim counters differ: $snapshot" }
        Write-Output $actualPass[0].Value
        Write-Output $actualBht[0].Value
    }
    'PASS: XSim four profiles match Icarus cycles/retired/bubbles/BHT and CRC golden' |
        Tee-Object -FilePath (Join-Path $LogDir 'summary.txt')
} finally { Pop-Location }
