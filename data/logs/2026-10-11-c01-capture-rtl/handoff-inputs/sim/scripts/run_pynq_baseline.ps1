param([string]$Port = 'COM12', [Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$outputRoot = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outputRoot) { throw 'Output directory already exists' }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (-not $outputRoot.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be inside repository' }
$steps = [ordered]@{
    system = 'uname -a'
    uptime = 'uptime'
    identity = 'id'
    network = 'ip -br address'
    os = 'cat /etc/os-release'
    artifacts = 'sha256sum /home/xilinx/vision_m2/vision.bit /home/xilinx/vision_m2/vision.hwh /home/xilinx/vision_m2/m2_onboard.py /home/xilinx/vision_m2/vision_regs.py'
    environment = 'bash -c ''source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 /home/xilinx/vision_m2/m2_onboard.py env'''
    loaded = 'bash -c ''source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && python3 -c "from pynq import PL; print(PL.bitfile_name); print(PL.timestamp); print(list(PL.ip_dict))"'''
}
foreach ($step in $steps.GetEnumerator()) {
    & (Join-Path $PSScriptRoot 'pynq_serial_command.ps1') -Port $Port -Command $step.Value `
        -LogPath (Join-Path $outputRoot ($step.Key + '.txt')) -TimeoutSeconds 30
    if ($LASTEXITCODE -ne 0) {
        Write-Output ('ERROR: baseline query failed: ' + $step.Key)
        exit $LASTEXITCODE
    }
}
Write-Output 'PASS: baseline queries complete; hardware functionality is not inferred'
