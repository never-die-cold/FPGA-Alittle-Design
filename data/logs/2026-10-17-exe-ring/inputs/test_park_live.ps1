# PC-side EXE-ring smoke test: hit the board LIVE service over 192.168.50.99.
# Run AFTER the board server is up (sudo + nohup on board).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File sim\scripts\test_park_live.ps1
# /v1/check blocks one full capture+locate+classify round (~40-70 s).
$ErrorActionPreference = 'Stop'
$base = 'http://192.168.50.99:8765'
Write-Output "== /v1/status =="
Invoke-RestMethod -Uri "$base/v1/status" -Method Get -TimeoutSec 10 | ConvertTo-Json -Compress
Write-Output "== /v1/check (one full round, blocking) =="
$watch = [Diagnostics.Stopwatch]::StartNew()
$packet = Invoke-RestMethod -Uri "$base/v1/check" -Method Post -Body '{}' -ContentType 'application/json' -TimeoutSec 600
$watch.Stop()
Write-Output ("round_seconds=" + [math]::Round($watch.Elapsed.TotalSeconds, 1))
$packet | ConvertTo-Json -Depth 6 -Compress
Write-Output ("verdict=" + $packet.decision.verdict + " targets=" + $packet.targets.Count +
              " prototype=" + $packet.prototype + " frame_id=" + $packet.frame_id)
