param([string]$Port='COM12', [Parameter(Mandatory)][string]$LogPath,
      [Parameter(Mandatory)][string]$RemoteDirectory,
      [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$BitSha256,
      [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$HwhSha256,
      [switch]$CheckOnly)
$ErrorActionPreference='Stop'
if($RemoteDirectory -notmatch '^/home/xilinx/vision_m2/c01-[0-9a-f]{32}$') {throw 'Invalid C01 directory'}
$remote="sudo -n env C01_BIT=$RemoteDirectory/capture.bit C01_BIT_SHA=$BitSha256 C01_HWH_SHA=$HwhSha256 bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && timeout -k 5s 65s python3 -u -X faulthandler $RemoteDirectory/c01_status_onboard.py'"
$marker="; printf '\n__PYNQ_RC_"+('0'*32)+"=%d\n' "+'$?'
$wire=[Text.Encoding]::UTF8.GetByteCount($remote+$marker)
if($wire -gt 3000){throw 'C01 serial command too long'}
if($CheckOnly){Write-Output "PASS: C01 wire bytes=$wire; no port opened"; exit 0}
& (Join-Path $PSScriptRoot 'pynq_serial_command.ps1') -Port $Port -Command $remote -LogPath $LogPath -TimeoutSeconds 85
exit $LASTEXITCODE
