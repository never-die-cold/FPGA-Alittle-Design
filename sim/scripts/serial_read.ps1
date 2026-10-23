param(
    [string]$Port = "COM4",
    [int]$Seconds = 25,
    [int]$Baud = 115200,
    [string]$OutFile = ""
)
$p = New-Object System.IO.Ports.SerialPort $Port,$Baud,None,8,one
$p.DtrEnable = $true
$p.RtsEnable = $true
$p.ReadTimeout = 500
$sb = New-Object System.Text.StringBuilder
try {
    $p.Open()
    $end = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $end) {
        if ($p.BytesToRead -gt 0) {
            [void]$sb.Append($p.ReadExisting())
        }
        Start-Sleep -Milliseconds 100
    }
    $s = $sb.ToString()
    if ($OutFile) { $s | Out-File -FilePath $OutFile -Encoding utf8 }
    if (-not $s) { '<no serial output>' }
    elseif ($s.Length -gt 6000) { $s.Substring($s.Length - 6000) }
    else { $s }
    $p.Close()
} catch {
    'SERIAL ERROR: ' + $_.Exception.Message
    if ($p.IsOpen) { $p.Close() }
}
