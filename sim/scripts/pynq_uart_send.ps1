# Send only the prepared diagnostic ZIP through the authorized COM port.
param([Parameter(Mandatory=$true)][string]$Archive,
      [Parameter(Mandatory=$true)][string]$Log,
      [string]$Port='COM12')
$ErrorActionPreference='Stop'
$uartRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$uartBlob=[System.IO.File]::ReadAllBytes((Resolve-Path $Archive).Path)
$uartHash=(Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
$uartReceiver=[System.IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'pynq_uart_receive.py'))
$uartEncoded=[Convert]::ToBase64String($uartReceiver)
if($uartEncoded.Length -gt 3900){throw 'Receiver exceeds terminal canonical line limit'}
$uartSerial=[System.IO.Ports.SerialPort]::new($Port,115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
$uartSerial.Encoding=[System.Text.Encoding]::UTF8
$uartSerial.DtrEnable=$true;$uartSerial.RtsEnable=$true;$uartSerial.WriteTimeout=5000
$uartOutput=''
try {
    $uartSerial.Open();$uartSerial.Write("`r");Start-Sleep -Milliseconds 500
    $uartOutput=$uartSerial.ReadExisting()
    if($uartOutput -notmatch 'xilinx@pynq:'){throw 'Expected PYNQ login shell not available'}
    $uartSerial.Write("printf '%s' '$uartEncoded' | base64 -d > /home/xilinx/pynq_uart_receive.py`r")
    $uartResponse='';$uartWatch=[System.Diagnostics.Stopwatch]::StartNew()
    do {Start-Sleep -Milliseconds 100;$uartResponse+=$uartSerial.ReadExisting()} while($uartResponse -notmatch 'xilinx@pynq:.*\$' -and $uartWatch.Elapsed.TotalSeconds -lt 8)
    $uartOutput+=$uartResponse
    if($uartResponse -notmatch 'xilinx@pynq:.*\$'){throw 'Receiver installation did not return a shell'}
    $uartSerial.Write("python3 /home/xilinx/pynq_uart_receive.py $($uartBlob.Length) $uartHash`r")
    $uartResponse='';$uartWatch.Restart()
    do {Start-Sleep -Milliseconds 100;$uartResponse+=$uartSerial.ReadExisting()} while($uartResponse -notmatch 'UART-READY' -and $uartWatch.Elapsed.TotalSeconds -lt 8)
    $uartOutput+=$uartResponse
    if($uartResponse -notmatch 'UART-READY'){throw 'Binary receiver not ready'}
    for($uartOffset=0;$uartOffset -lt $uartBlob.Length;$uartOffset+=4096){
        $uartCount=[Math]::Min(4096,$uartBlob.Length-$uartOffset)
        $uartSerial.Write($uartBlob,$uartOffset,$uartCount)
        if($uartOffset%131072 -eq 0){Write-Output "UART sent=$uartOffset total=$($uartBlob.Length)"}
    }
    $uartResponse='';$uartWatch.Restart()
    do {Start-Sleep -Milliseconds 250;$uartResponse+=$uartSerial.ReadExisting()} while($uartResponse -notmatch 'xilinx@pynq:.*\$' -and $uartWatch.Elapsed.TotalSeconds -lt 25)
    $uartOutput+=$uartResponse
    Write-Output $uartResponse
    if($uartResponse -notmatch 'PASS: UART package' -or $uartResponse -notmatch $uartHash){throw 'UART package acceptance missing'}
} finally {
    [System.IO.File]::WriteAllText((Join-Path $uartRoot $Log),$uartOutput,[System.Text.UTF8Encoding]::new($false))
    if($uartSerial.IsOpen){$uartSerial.Close()};$uartSerial.Dispose()
}
