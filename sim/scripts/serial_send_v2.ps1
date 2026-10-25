# Serial base64 transfer v2: `cat > file` + Ctrl+D instead of a heredoc so the
# board drains with a block read loop (no per-line readline overhead).
param(
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [string]$Port = "COM4",
    [int]$Baud = 115200,
    [string[]]$Files = @(
        "payload/tools/cop_payload_loader.py",
        "payload/provisional-model/manifest.json",
        "payload/provisional-model/payload.bin",
        "payload/pynq_cop_40mhz.hwh",
        "golden/zero/input.hex",
        "golden/pattern/input.hex",
        "EXPECTED_OUTPUTS.tsv"
    ),
    [string]$OutFile = ""
)
$report = New-Object System.Collections.Generic.List[string]
$p = New-Object System.IO.Ports.SerialPort $Port,$Baud,None,8,one
$p.DtrEnable = $true
$p.RtsEnable = $true
$p.WriteTimeout = 15000
$p.ReadTimeout = 500
$p.Open()
function Drain([int]$ms) {
    Start-Sleep -Milliseconds $ms
    return $p.ReadExisting()
}
[void](Drain 300)
$p.Write("stty -echo`r")
Start-Sleep -Milliseconds 300
[void](Drain 200)
$p.Write("mkdir -p ~/cop-pkg/payload/tools ~/cop-pkg/payload/provisional-model ~/cop-pkg/golden/zero ~/cop-pkg/golden/pattern /tmp`r")
Start-Sleep -Milliseconds 400
[void](Drain 200)
foreach ($rel in $Files) {
    $src = Join-Path $PackageRoot ($rel -replace '/', '\')
    $dest = "~/cop-pkg/" + $rel
    $tmp = "/tmp/tx.b64"
    $bytes = [IO.File]::ReadAllBytes($src)
    $b64 = [Convert]::ToBase64String($bytes)
    $report.Add("SEND $rel bytes=$($bytes.Length)")
    $p.Write("cat > $tmp`r")
    Start-Sleep -Milliseconds 150
    for ($i = 0; $i -lt $b64.Length; $i += 304) {
        $len = [Math]::Min(304, $b64.Length - $i)
        $p.Write($b64.Substring($i, $len) + "`n")
        Start-Sleep -Milliseconds 3
    }
    Start-Sleep -Milliseconds 150
    $p.Write("`n" + [string][char]4)
    Start-Sleep -Milliseconds 600
    [void](Drain 200)
    $p.Write("base64 -d $tmp > $dest && sha256sum $dest`r")
    $report.Add((Drain 2000))
}
$p.Write("stty echo`r")
Start-Sleep -Milliseconds 300
$report.Add((Drain 300))
$p.Close()
$text = ($report -join "`r`n") + "`r`n"
if ($OutFile) { [IO.File]::WriteAllText($OutFile, $text) }
$text
