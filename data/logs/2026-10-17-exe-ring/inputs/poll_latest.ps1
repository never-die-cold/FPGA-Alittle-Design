$ErrorActionPreference = 'Stop'
try {
    $p = Invoke-RestMethod -Uri 'http://192.168.50.99:8765/v1/latest' -Method Get -TimeoutSec 10
    $p | ConvertTo-Json -Depth 5 -Compress
    Write-Output ("verdict=" + $p.decision.verdict + " targets=" + $p.targets.Count)
} catch {
    Write-Output ('ERR: ' + $_.Exception.Message)
}
