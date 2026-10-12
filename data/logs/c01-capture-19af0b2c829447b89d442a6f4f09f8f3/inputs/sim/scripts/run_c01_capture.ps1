param([ValidateSet('validate','bitstream')][string]$Stage='validate',
      [string]$Vivado='D:\Vivado_downloads\2026.1\Vivado\bin\vivado.bat')
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Push-Location $taskRoot
try {
    foreach($needed in @($Vivado,'sim/build/hdmi-source/ps7_config.tcl',
        'sim/build/hdmi-source/hdmi_pins.xdc','sim/build/hdmi-library-full/ip/dvi2rgb/component.xml')) {
        if(!(Test-Path -LiteralPath $needed)){throw "Missing prerequisite: $needed (prepare pinned HDMI inputs first)"}
    }
    $evidence=Join-Path $taskRoot ('data/logs/c01-capture-'+[Guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($evidence) | Out-Null
    $files=@(Get-ChildItem src/vision -File | Where-Object {$_.Extension -in '.v','.xdc'})+
        @(Get-Item sim/scripts/create_hdmi_bd.tcl,sim/scripts/create_capture_hdmi_bd.tcl,
            sim/scripts/build_capture_hdmi.tcl,sim/scripts/validate_vision_cdc.tcl,
            sim/scripts/run_c01_capture.ps1,sim/scripts/fetch_hdmi_ip.sh,sim/scripts/prepare_hdmi_sources.py,
            sim/build/hdmi-source/ps7_config.tcl,sim/build/hdmi-source/hdmi_pins.xdc)
    foreach($folder in @('ip/dvi2rgb','ip/rgb2dvi','if','module')) {
        $files+=@(Get-ChildItem (Join-Path 'sim/build/hdmi-library-full' $folder) -Recurse -File)
    }
    $records=@()
    foreach($file in $files) {
        $relative=$file.FullName.Substring($taskRoot.Length+1)
        $copy=Join-Path (Join-Path $evidence 'inputs') $relative
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($copy)) | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $copy
        $records+=@{path=$relative;bytes=$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()}
    }
    [IO.File]::WriteAllText((Join-Path $evidence 'manifest.json'),
        (@{stage=$Stage;git_base=(git rev-parse HEAD);uncommitted=$true;files=$records}|ConvertTo-Json -Depth 5),
        (New-Object Text.UTF8Encoding $false))
    Write-Output "EVIDENCE_DIR=$evidence"
    $arguments=@('-mode','batch','-source','sim/scripts/build_capture_hdmi.tcl',
        '-log',(Join-Path $evidence 'vivado.log'),'-journal',(Join-Path $evidence 'vivado.jou'),
        '-tclargs',$Stage)
    & $Vivado @arguments *> (Join-Path $evidence 'console.txt')
    $rc=$LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $evidence 'exit.txt'),"$rc`n")
    Get-Content (Join-Path $evidence 'console.txt') -Tail 15
    if($rc -ne 0){throw "Vivado failed: exit=$rc; see $evidence"}
    Write-Output "PASS: C01 $Stage (offline; board acceptance pending)"
} finally {Pop-Location}
