param()
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$output=Join-Path $repo ('data/evidence/cnn-ddr-offline-'+[guid]::NewGuid().ToString('N'))
$sources=@()
foreach($folder in @('src/coprocessor','sim/coprocessor')){
    $sources+=Get-ChildItem (Join-Path $repo $folder) -File | Where-Object {$_.Extension -in '.v','.py'}
}
foreach($path in @('src/pynq_host/c01_capture.py','sim/vision/test_c01_capture.py',
    'sim/scripts/c01_ddr_onboard.py','sim/scripts/c01_status_onboard.py','sim/scripts/pynq_file_receiver.py',
    'sim/scripts/send_pynq_file.ps1','sim/scripts/pynq_serial_command.ps1','sim/scripts/vision_gate.sh',
    'sim/scripts/run_coprocessor_iverilog.sh','sim/scripts/run_coprocessor_python.sh',
    'sim/scripts/run_iverilog.sh','sim/scripts/run_vision_python.sh','sim/scripts/run_cnn_ooc.ps1',
    'sim/scripts/synth_coprocessor_ooc.tcl','sim/scripts/archive_cnn_ddr_offline.ps1')){
    $sources+=Get-Item (Join-Path $repo $path)
}
$goldens=Join-Path $repo 'sim/build/coprocessor/network-vectors'
$manifest=Get-Content (Join-Path $goldens 'manifest.json') -Raw | ConvertFrom-Json
if($manifest.kind -ne 'DIAGNOSTIC_INTEGER_NETWORK_NOT_TRAINED'){throw 'unexpected golden kind'}
function Check-Hash($path,$expected){
    if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower() -ne $expected){throw "hash mismatch: $path"}
}
foreach($entry in $manifest.model_files_sha256.PSObject.Properties){Check-Hash (Join-Path $goldens $entry.Name) $entry.Value}
foreach($case in $manifest.cases.PSObject.Properties){
    foreach($entry in $case.Value.files_sha256.PSObject.Properties){
        Check-Hash (Join-Path (Join-Path $goldens $case.Name) $entry.Name) $entry.Value
    }
}
foreach($entry in $manifest.source_sha256.PSObject.Properties){Check-Hash (Join-Path $repo $entry.Name) $entry.Value}
$sources+=Get-ChildItem $goldens -File -Recurse
$records=@()
foreach($source in $sources){
    $relative=$source.FullName.Substring($repo.Length+1).Replace('\','/')
    $destination=Join-Path (Join-Path $output 'inputs') $relative
    New-Item -ItemType Directory ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
    $hash=(Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash.ToLower()
    Copy-Item -LiteralPath $source.FullName -Destination $destination
    Check-Hash $destination $hash
    $records+=@{path=$relative;bytes=$source.Length;sha256=$hash}
}
Push-Location $repo
try {
    @{kind='OFFLINE_CNN_DDR_SOURCE_AND_DIAGNOSTIC_GOLDEN_NOT_BOARD_ACCEPTANCE';
        git_base=(git rev-parse HEAD);uncommitted=$true;files=$records;
        commands=@('bash sim/scripts/run_iverilog.sh all','bash sim/scripts/run_coprocessor_python.sh all',
                   'powershell.exe -NoProfile -File sim/scripts/run_cnn_ooc.ps1')} |
        ConvertTo-Json -Depth 8 | Set-Content (Join-Path $output 'manifest.json') -Encoding utf8
} finally {Pop-Location}
Write-Output "EVIDENCE_DIR=$output"
Write-Output "PASS: $($records.Count) source/golden files archived; every SHA256 verified"
