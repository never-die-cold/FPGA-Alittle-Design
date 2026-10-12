param([string]$Port = 'COM12')
$ErrorActionPreference = 'Stop'
if (-not ('System.IO.Ports.SerialPort' -as [type])) { Add-Type -AssemblyName System.IO.Ports }
$serial = [IO.Ports.SerialPort]::new($Port, 115200, [IO.Ports.Parity]::None,
    8, [IO.Ports.StopBits]::One)
$serial.Encoding = [Text.UTF8Encoding]::new($false)
$serial.Handshake = [IO.Ports.Handshake]::None
$serial.DtrEnable = $false
$serial.RtsEnable = $false
$token = '__PYNQ_AUTH_' + [Guid]::NewGuid().ToString('N')
$reply = ''
$exitCode = 1
try {
    $serial.Open()
    $serial.ReadExisting() | Out-Null
    $serial.Write("sudo -p 'PYNQ_AUTH_PASSWORD: ' -v; printf '\n" + $token + "=%d\n' `$?`r")
    $timer = [Diagnostics.Stopwatch]::StartNew()
    while ($timer.Elapsed.TotalSeconds -lt 60) {
        $chunk = $serial.ReadExisting()
        if ($chunk) { $reply += $chunk; [Console]::Write($chunk) }
        $done = [regex]::Match($reply, '(?:\r?\n)' + [regex]::Escape($token) + '=(\d+)\r?\n')
        if ($done.Success) { $exitCode = [int]$done.Groups[1].Value; break }
        # Match the real sudo prompt at line end, never its echoed shell command.
        if ($reply -match '(?:^|[\r\n])PYNQ_AUTH_PASSWORD:[ \t]*$') {
            $secret = Read-Host 'Board sudo password (input hidden)' -AsSecureString
            $secretBuffer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
            try {
                $serial.Write([Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretBuffer) + "`r")
            } finally {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretBuffer)
                $secret.Dispose()
            }
            $reply = ''
            $timer.Restart()
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $done.Success) { $exitCode = 124; Write-Output 'ERROR: authentication completion unconfirmed' }
} finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}
if ($exitCode -eq 0) { Write-Output 'PASS: sudo authenticated; COM12 released' }
else { Write-Output ('ERROR: sudo authentication exit=' + $exitCode) }
exit $exitCode
