$ErrorActionPreference = 'Stop'
$process = Start-Process -FilePath powershell.exe -ArgumentList '-NoProfile -Command "exit 7"' -PassThru -WindowStyle Hidden
[void]$process.Handle
if (-not $process.WaitForExit(5000)) { throw 'Probe timeout' }
if ($process.ExitCode -ne 7) { throw 'ExitCode was not retained' }
'PASS: pinned process handle retains ExitCode=7'
