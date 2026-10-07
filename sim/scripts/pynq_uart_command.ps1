# Execute a board command and keep COM open until exit marker + shell prompt.
param([Parameter(Mandatory=$true)][string]$Command,
      [Parameter(Mandatory=$true)][string]$Log,
      [string]$Port='COM12',[int]$TimeoutSeconds=35,
      [System.Security.SecureString]$SudoPassword)
$ErrorActionPreference='Stop'
$uartRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$uartSerial=[System.IO.Ports.SerialPort]::new($Port,115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
$uartSerial.Encoding=[System.Text.Encoding]::UTF8
$uartSerial.DtrEnable=$true;$uartSerial.RtsEnable=$true
$uartResponse='';$uartPasswordSent=$false
try {
    $uartSerial.Open();$uartSerial.Write("`r");Start-Sleep -Milliseconds 500
    $uartInitial=$uartSerial.ReadExisting()
    if($uartInitial -notmatch 'xilinx@pynq:'){throw 'PYNQ shell unavailable'}
    $uartWrapped='{ '+$Command+'; }; uart_rc=$?; printf ''\nUART-CMD-EXIT=%s\n'' "$uart_rc"'
    $uartSerial.Write($uartWrapped+"`r")
    $uartWatch=[System.Diagnostics.Stopwatch]::StartNew()
    do {
        Start-Sleep -Milliseconds 250
        $uartResponse+=$uartSerial.ReadExisting()
        if(!$uartPasswordSent -and $uartResponse -match '\[sudo\] password for xilinx:'){
            if(!$SudoPassword){throw 'Sudo password required'}
            $uartSecret=[System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SudoPassword)
            try {$uartSerial.Write([System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($uartSecret)+"`r")}
            finally {[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($uartSecret)}
            $uartPasswordSent=$true
        }
    } while(!($uartResponse -match 'UART-CMD-EXIT=\d+' -and $uartResponse -match 'xilinx@pynq:[^\r\n]*\$') -and $uartWatch.Elapsed.TotalSeconds -lt $TimeoutSeconds)
    Write-Output $uartResponse
    $uartExit=[regex]::Match($uartResponse,'UART-CMD-EXIT=(\d+)')
    if(!$uartExit.Success){throw 'Board command timeout'}
    if([int]$uartExit.Groups[1].Value -ne 0){throw "Board command failed, exit=$($uartExit.Groups[1].Value)"}
} finally {
    [System.IO.File]::WriteAllText((Join-Path $uartRoot $Log),$uartResponse,[System.Text.UTF8Encoding]::new($false))
    if($uartSerial.IsOpen){$uartSerial.Close()};$uartSerial.Dispose()
}
