param(
    [ValidatePattern('^COM[0-9]+$')][string]$Port = 'COM12',
    [Parameter(Mandatory)][string]$OutputDirectory,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$BitSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$HwhSha256,
    [Parameter(Mandatory)][ValidatePattern('^/home/xilinx/vision_m2/c01-[0-9a-f]{32}$')][string]$RemoteDirectory
)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$runDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (-not $runDirectory.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $runDirectory)) {
    throw 'OutputDirectory must be a new directory inside the repository'
}
[IO.Directory]::CreateDirectory($runDirectory) | Out-Null
$boardLog = Join-Path $runDirectory 'board.txt'
$statusLog = Join-Path $runDirectory 'host-status.txt'
$boardRunner = Join-Path $PSScriptRoot 'run_c01_status.ps1'
$boardArguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $boardRunner +
    '" -Port ' + $Port + ' -LogPath "' + $boardLog + '" -RemoteDirectory ' + $RemoteDirectory + ' -BitSha256 ' + $BitSha256 + ' -HwhSha256 ' + $HwhSha256
$board = Start-Process -FilePath 'powershell.exe' -ArgumentList $boardArguments -PassThru `
    -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDirectory 'board-console.txt') `
    -RedirectStandardError (Join-Path $runDirectory 'board-stderr.txt')
[void]$board.Handle # Keep the process handle so Windows PowerShell retains ExitCode.
$timer = [Diagnostics.Stopwatch]::StartNew()
$windowSeen = $false
while ($timer.Elapsed.TotalSeconds -lt 125) {
    if (Test-Path -LiteralPath $boardLog) {
        $logText = Get-Content -LiteralPath $boardLog -Raw
        if ($logText -match '(?m)^WINDOW: C01 HDMI direct display') { $windowSeen = $true; break }
    }
    if ($board.HasExited) { break }
    Start-Sleep -Milliseconds 200
}
$captureExit = 1
$overlapConfirmed = $false
if ($windowSeen) {
    Set-Content -LiteralPath $statusLog ('COEXIST_SEEN_UTC=' + [DateTime]::UtcNow.ToString('o'))
    Add-Content -LiteralPath $statusLog ('UVC_START_UTC=' + [DateTime]::UtcNow.ToString('o'))
    & python (Join-Path $PSScriptRoot 'capture_uvc_raw.py') `
        --output-dir (Join-Path $runDirectory 'uvc') *> (Join-Path $runDirectory 'uvc-console.txt')
    $captureExit = $LASTEXITCODE
    Add-Content -LiteralPath $statusLog ('UVC_END_UTC=' + [DateTime]::UtcNow.ToString('o'))
    $overlapConfirmed = (Get-Content -LiteralPath $boardLog -Raw) -notmatch '(?m)^CLEANUP:'
} else {
    Set-Content -LiteralPath $statusLog 'ERROR: no coexist window observed; no UVC capture started'
}
while (-not $board.HasExited -and $timer.Elapsed.TotalSeconds -lt 135) {
    Start-Sleep -Milliseconds 200
}
if (-not $board.HasExited) { throw 'Board runner completion unconfirmed; inspect board log' }
$board.WaitForExit()
Add-Content -LiteralPath $statusLog ('BOARD_EXIT=' + $board.ExitCode)
Add-Content -LiteralPath $statusLog ('UVC_EXIT=' + $captureExit)
Add-Content -LiteralPath $statusLog ('UVC_FINISHED_BEFORE_CLEANUP=' + $overlapConfirmed)
$logText = Get-Content -LiteralPath $boardLog -Raw
if ($board.ExitCode -ne 0 -or $captureExit -ne 0 -or -not $overlapConfirmed -or
        $logText -notmatch '(?m)^CLEANUP: original vision load and smoke completed' -or $logText -notmatch '(?m)^HOST_EXIT_CODE=0') {
    Get-Content -LiteralPath $statusLog
    throw 'C01 display/status check failed; preserve logs and plan recovery'
}
Get-Content -LiteralPath $statusLog
Write-Output 'PASS: C01 display/status, UVC within diagnostic window, and original vision restored; DDR capture untested'
