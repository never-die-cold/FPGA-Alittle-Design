param([string]$Port = 'COM12', [Parameter(Mandatory)][string]$LogPath, [switch]$InputOnly, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'n03_board_capture.py'
$bytes = [IO.File]::ReadAllBytes($source)
$buffer = [IO.MemoryStream]::new()
$zip = [IO.Compression.GZipStream]::new($buffer, [IO.Compression.CompressionMode]::Compress, $true)
$zip.Write($bytes, 0, $bytes.Length)
$zip.Dispose()
$payload = [Convert]::ToBase64String($buffer.ToArray())
$buffer.Dispose()
$python = 'import base64,gzip;exec(gzip.decompress(base64.b64decode(\"' + $payload + '\")))'
$captureMode = if ($InputOnly) { "N03_CAPTURE_ONLY=1 " } else { "" }
$remote = "sudo -n bash -c 'source /etc/profile.d/xrt_setup.sh && source /etc/profile.d/pynq_venv.sh && ${captureMode}timeout -k 5s 90s python3 -X faulthandler -c `"$python`"'"
$marker = "; printf '\n__PYNQ_RC_" + ('0' * 32) + "=%d\n' " + '$?'
$wireBytes = [Text.Encoding]::UTF8.GetByteCount($remote + $marker)
if ($wireBytes -gt 3000) {
    throw 'Compressed script exceeds serial command limit'
}
if ($CheckOnly) { Write-Output ('PASS: serial wire bytes=' + $wireBytes + ' limit=3000; no serial opened'); exit 0 }
& (Join-Path $PSScriptRoot 'pynq_serial_command.ps1') -Port $Port `
    -Command $remote -LogPath $LogPath -TimeoutSeconds 120
exit $LASTEXITCODE
