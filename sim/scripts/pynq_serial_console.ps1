param([string]$Port = 'COM12')
$ErrorActionPreference = 'Stop'
if (-not ('System.IO.Ports.SerialPort' -as [type])) { Add-Type -AssemblyName System.IO.Ports }
$consoleSerial = [IO.Ports.SerialPort]::new($Port, 115200, [IO.Ports.Parity]::None,
    8, [IO.Ports.StopBits]::One)
$consoleSerial.Encoding = [Text.UTF8Encoding]::new($false)
$consoleSerial.Handshake = [IO.Ports.Handshake]::None
$consoleSerial.DtrEnable = $false
$consoleSerial.RtsEnable = $false
Write-Host 'PYNQ serial console: enter login credentials, then run sudo -v.'
Write-Host 'No local input echo or file log. Remote shell controls password echo.'
Write-Host 'After returning to the shell prompt, press Escape to release the port.'
try {
    $consoleSerial.Open()
    $consoleSerial.Write("`r")
    while ($true) {
        $consoleChunk = $consoleSerial.ReadExisting()
        if ($consoleChunk) { [Console]::Write($consoleChunk) }
        if ([Console]::KeyAvailable) {
            $consoleKey = [Console]::ReadKey($true)
            if ($consoleKey.Key -eq [ConsoleKey]::Escape) { break }
            if ($consoleKey.Key -eq [ConsoleKey]::Enter) { $consoleSerial.Write("`r") }
            elseif ($consoleKey.Key -eq [ConsoleKey]::Backspace) { $consoleSerial.Write("`b") }
            elseif ($consoleKey.KeyChar -ne [char]0) { $consoleSerial.Write([string]$consoleKey.KeyChar) }
            $consoleKey = $null
        }
        Start-Sleep -Milliseconds 30
    }
} finally {
    if ($consoleSerial.IsOpen) { $consoleSerial.Close() }
    $consoleSerial.Dispose()
}
Write-Host 'Serial console closed; COM port released.'
