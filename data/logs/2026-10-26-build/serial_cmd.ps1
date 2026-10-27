param([Parameter(Mandatory=$true)][string]$Command, [int]$WaitMs = 2500, [string]$Port = "COM12", [int]$Baud = 115200)
$p = New-Object System.IO.Ports.SerialPort $Port,$Baud,None,8,one
$p.DtrEnable = $true
$p.RtsEnable = $true
$p.ReadTimeout = 500
try {
  $p.Open()
  Start-Sleep -Milliseconds 300
  [void]$p.ReadExisting()
  $p.Write($Command + [char]13)
  Start-Sleep -Milliseconds $WaitMs
  $out = $p.ReadExisting()
  $p.Close()
  Write-Output $out
} catch {
  Write-Output ("SERIAL_FAIL " + $_.Exception.Message)
  try { $p.Close() } catch {}
}