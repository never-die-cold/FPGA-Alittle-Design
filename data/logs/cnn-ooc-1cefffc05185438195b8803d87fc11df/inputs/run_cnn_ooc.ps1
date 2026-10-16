param([string]$Vivado='D:/Vivado_downloads/2026.1/Vivado/bin/vivado.bat')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if(!(Test-Path -LiteralPath $Vivado)){throw 'Vivado executable missing'}
$evidence=Join-Path $repo ('data/logs/cnn-ooc-'+[guid]::NewGuid().ToString('N'))
$inputs=Join-Path $evidence 'inputs'
New-Item -ItemType Directory $inputs | Out-Null
$records=@()
$sources=@(Get-ChildItem (Join-Path $repo 'src/coprocessor') -Filter '*.v' -File)
$sources+=Get-Item (Join-Path $PSScriptRoot 'synth_coprocessor_ooc.tcl'),$PSCommandPath
foreach($source in $sources){
    Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $inputs $source.Name)
    $records+=@{path=$source.FullName.Substring($repo.Length+1).Replace('\','/');
        file=$source.Name;bytes=$source.Length;sha256=(Get-FileHash $source.FullName -Algorithm SHA256).Hash.ToLower()}
}
Push-Location $repo
try {
    @{git_base=(git rev-parse HEAD);uncommitted=$true;part='xc7z020clg400-1';clock_ns=10;
        kind='CONTROLLER_ONLY_OOC_EXTERNAL_MEMORY_PORTS';files=$records} |
        ConvertTo-Json -Depth 5 | Set-Content (Join-Path $evidence 'manifest.json') -Encoding utf8
    Write-Output "EVIDENCE_DIR=$evidence"
    & $Vivado -mode batch -source (Join-Path $inputs 'synth_coprocessor_ooc.tcl') `
        -log (Join-Path $evidence 'vivado.log') -journal (Join-Path $evidence 'vivado.jou') `
        -tclargs (Join-Path $evidence 'reports') $inputs $repo *> (Join-Path $evidence 'console.txt')
    $rc=$LASTEXITCODE
    Set-Content (Join-Path $evidence 'exit.txt') $rc
    Get-Content (Join-Path $evidence 'console.txt') -Tail 20
    exit $rc
} finally {Pop-Location}
