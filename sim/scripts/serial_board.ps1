# Send one command to the PYNQ PROG/UART console and capture its output.
# Board-only helper for the no-Ethernet fallback; not part of the off-board gate.
# Usage: powershell -ExecutionPolicy Bypass -File sim/scripts/serial_board.ps1 `
#          -CommandFile <file-with-one-line-command> [-Port COM4] [-Wait 5]
param(
    [Parameter(Mandatory=$true)][string]$CommandFile,
    [string]$Port = "COM4",
    [int]$Wait = 5,
    [int]$Baud = 115200,
    [string]$OutFile = ""
)
$p = New-Object System.IO.Ports.SerialPort $Port,$Baud,None,8,one
$p.DtrEnable = $true
$p.RtsEnable = $true
$p.ReadTimeout = 1000
try {
    $p.Open()
    Start-Sleep -Milliseconds 200
    $p.ReadExisting() | Out-Null
    $cmd = (Get-Content -Raw $CommandFile).TrimEnd("`r", "`n")
    $p.Write($cmd + "`r")
    Start-Sleep -Seconds $Wait
    $s = $p.ReadExisting()
    if ($s) {
        if ($OutFile) { $s | Out-File -FilePath $OutFile -Encoding utf8 }
        $s
    } else {
        '<no output>'
    }
    $p.Close()
} catch {
    'SERIAL ERROR: ' + $_.Exception.Message
    if ($p.IsOpen) { $p.Close() }
}
