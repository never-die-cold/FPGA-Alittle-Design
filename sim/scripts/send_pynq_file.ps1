param([Parameter(Mandatory)][string]$File,
      [Parameter(Mandatory)][string]$RemotePath,
      [string]$Port='COM12', [string]$LogPath, [switch]$CheckOnly)
$ErrorActionPreference='Stop'
if($RemotePath -notmatch '^/home/xilinx/vision_m2/c01-[0-9a-f]{32}/[A-Za-z0-9._-]+$') {
    throw 'Target must be a new C01 artifact path under /home/xilinx/vision_m2'
}
function Pack([byte[]]$Bytes) {
    $out=[IO.MemoryStream]::new()
    $zip=[IO.Compression.GZipStream]::new($out,[IO.Compression.CompressionLevel]::Optimal,$true)
    try { $zip.Write($Bytes,0,$Bytes.Length) } finally { $zip.Dispose() }
    $result=[Convert]::ToBase64String($out.ToArray()); $out.Dispose(); return $result
}
$raw=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $File).Path)
$sha=(Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLower()
$encoded=Pack $raw
$token='__UART_'+[Guid]::NewGuid().ToString('N')
$receiver=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'pynq_file_receiver.py'))
$code='import base64,gzip;exec(gzip.decompress(base64.b64decode("'+(Pack ([Text.Encoding]::UTF8.GetBytes($receiver)))+'")));receive('+$encoded.Length+','+$raw.Length+',"'+$sha+'","'+$RemotePath+'","'+$token+'")'
$command='saved=$(stty -g); (trap ''stty "$saved"'' EXIT; stty raw -echo; timeout --foreground -k 3s 180s python3 -c '''+$code+'''); printf ''\n'+$token+'_EXIT=%d\n'' $?'
if([Text.Encoding]::UTF8.GetByteCount($command) -gt 2800){throw 'UART bootstrap exceeds command limit'}
Write-Output "TRANSFER: bytes=$($raw.Length) base64=$($encoded.Length) sha256=$sha target=$RemotePath"
if($CheckOnly){Write-Output 'PASS: transfer packaging and command length (no port opened)'; exit 0}
if(!$LogPath -or (Test-Path -LiteralPath $LogPath)){throw 'Provide a new LogPath'}
if(-not ('System.IO.Ports.SerialPort' -as [type])){Add-Type -AssemblyName System.IO.Ports}
$serial=[IO.Ports.SerialPort]::new($Port,115200,[IO.Ports.Parity]::None,8,[IO.Ports.StopBits]::One)
$serial.Handshake=[IO.Ports.Handshake]::None; $serial.DtrEnable=$false; $serial.RtsEnable=$false
$serial.Encoding=[Text.Encoding]::ASCII; $serial.WriteTimeout=10000
$reply=''; $offset=0; $sent=$false; $nextProgress=65536
$timer=[Diagnostics.Stopwatch]::StartNew()
try {
    $serial.Open(); $serial.ReadExisting() | Out-Null; $serial.Write($command+"`r")
    while($timer.Elapsed.TotalSeconds -lt 15) {
        $reply+=$serial.ReadExisting()
        if($reply -match ('(?:^|[\r\n])'+[regex]::Escape($token)+'_READY[\r\n]')){break}
        Start-Sleep -Milliseconds 50
    }
    if($reply -notmatch ('(?:^|[\r\n])'+[regex]::Escape($token)+'_READY[\r\n]')){throw 'Receiver ready timeout'}
    while($offset -lt $encoded.Length) {
        $count=[Math]::Min(4096,$encoded.Length-$offset)
        $serial.Write($encoded.Substring($offset,$count)); $offset+=$count
        if($offset -ge $nextProgress){Write-Output "TRANSFER_PROGRESS=$offset/$($encoded.Length)"; $nextProgress+=65536}
    }
    $sent=$true
    while($timer.Elapsed.TotalSeconds -lt 200) {
        $reply+=$serial.ReadExisting()
        $done=[regex]::Match($reply,'(?:^|[\r\n])'+[regex]::Escape($token)+'_EXIT=(\d+)[\r\n]')
        if($done.Success){break}
        Start-Sleep -Milliseconds 100
    }
    if(!$done.Success -or $done.Groups[1].Value -ne '0' -or !$reply.Contains('PASS: UART file')) {
        throw 'Transfer completion or saved SHA256 unconfirmed'
    }
    Write-Output 'PASS: board file transferred and SHA256 verified; UART terminal mode restored'
} finally {
    try {
        [IO.File]::WriteAllText($LogPath,"SOURCE=$File`nTARGET=$RemotePath`nSHA256=$sha`nBASE64_SENT=$offset`n"+$reply,(New-Object Text.UTF8Encoding $false))
    } finally {
        if($serial.IsOpen){$serial.Close()}; $serial.Dispose()
        if(!$sent){Write-Warning 'Partial raw UART transfer: wait for the 180-second remote timeout before reusing COM12'}
    }
}
