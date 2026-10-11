param(
    [Parameter(Mandatory)][string]$Command,
    [Parameter(Mandatory)][string]$LogPath,
    [string]$Port = 'COM12',
    [ValidateRange(1, 300)][int]$TimeoutSeconds = 20
)
$ErrorActionPreference = 'Stop'
if (-not ('System.IO.Ports.SerialPort' -as [type])) { Add-Type -AssemblyName System.IO.Ports }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$logFile = [IO.Path]::GetFullPath($LogPath)
if (-not $logFile.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) { throw 'LogPath must be inside repository' }
if (Test-Path -LiteralPath $logFile) { throw 'Log already exists; preserve earlier evidence' }
if ($Command -match '[\r\n]') { throw 'Command must be a single shell line' }
$token = '__PYNQ_RC_' + [Guid]::NewGuid().ToString('N')
$wireCommand = $Command + "; printf '\n" + $token + "=%d\n' `$?"
if ([Text.Encoding]::UTF8.GetByteCount($wireCommand) -gt 3000) { throw 'Serial command too long' }
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($logFile)) | Out-Null
$logStream = [IO.File]::Open($logFile, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$writer = [IO.StreamWriter]::new($logStream, [Text.UTF8Encoding]::new($false))
$serial = [IO.Ports.SerialPort]::new($Port, 115200, [IO.Ports.Parity]::None,
    8, [IO.Ports.StopBits]::One)
$serial.Encoding = [Text.UTF8Encoding]::new($false)
$serial.Handshake = [IO.Ports.Handshake]::None
$serial.DtrEnable = $false
$serial.RtsEnable = $false
$exitCode = 1
$reply = ''
try {
    $writer.WriteLine('HOST_STARTED_UTC=' + [DateTime]::UtcNow.ToString('o'))
    $writer.WriteLine('PORT=' + $Port + ' BAUD=115200 8N1 NO_FLOW')
    $writer.WriteLine('COMMAND=' + $Command)
    $writer.Flush()
    $serial.Open()
    $serial.Write($wireCommand + "`r")
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $pattern = '(?:\r?\n)' + [regex]::Escape($token) + '=(\d+)\r?\n'
    while ($timer.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        $chunk = $serial.ReadExisting()
        if ($chunk) {
            $reply += $chunk
            $writer.Write($chunk)
            $writer.Flush()
        }
        $match = [regex]::Match($reply, $pattern)
        if ($match.Success) { $exitCode = [int]$match.Groups[1].Value; break }
        Start-Sleep -Milliseconds 100
    }
    if (-not $match.Success) {
        $exitCode = 124
        $writer.WriteLine("`nERROR: timeout; remote completion unconfirmed; no interrupt sent")
    }
} catch {
    $writer.WriteLine("`nERROR: " + $_.Exception.Message)
    Write-Error $_ -ErrorAction Continue
} finally {
    $writer.WriteLine("`nHOST_EXIT_CODE=" + $exitCode)
    $writer.Dispose()
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}
Write-Output $reply
Write-Output ('SERIAL_COMMAND_EXIT=' + $exitCode)
exit $exitCode
