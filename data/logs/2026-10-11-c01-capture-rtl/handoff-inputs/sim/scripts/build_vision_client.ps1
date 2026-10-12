param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "../..")
$dependencyPath = Join-Path (Get-Location) "sim/build/vision-client-deps"
$oldPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = "$dependencyPath;$oldPythonPath"
    & $Python -c "import cv2, PyInstaller, PIL; assert cv2.__version__ == '4.12.0'; assert PyInstaller.__version__ == '6.16.0'; assert PIL.__version__ == '12.3.0'"
    if ($LASTEXITCODE -ne 0) {
        & $Python -m pip install --target $dependencyPath -r src/vision_client/requirements.txt
        if ($LASTEXITCODE -ne 0) { throw "client dependency installation failed" }
    }
    New-Item -ItemType Directory -Force sim/build/vision-client | Out-Null
    $assetsPath = Join-Path (Get-Location) "src/vision_client/assets"
    & $Python -m PyInstaller --noconfirm --onedir --console --name vision_preview `
        --paths src/pynq_host --add-data "$assetsPath;assets" `
        --distpath sim/build/vision-client/dist `
        --workpath sim/build/vision-client/build --specpath sim/build/vision-client src/vision_client/preview.py
    if ($LASTEXITCODE -ne 0) { throw "EXE packaging failed" }
    & sim/build/vision-client/dist/vision_preview/vision_preview.exe --selftest
    if ($LASTEXITCODE -ne 0) { throw "packaged runtime test failed" }
    & $Python sim/vision/test_vision_client.py
    if ($LASTEXITCODE -ne 0) { throw "packaged HTTP integration failed" }
    & $Python sim/vision/test_inspection_viewer.py --exe sim/build/vision-client/dist/vision_preview/vision_preview.exe
    if ($LASTEXITCODE -ne 0) { throw "packaged FILE REPLAY failed" }
    Write-Output "PASS: Windows M2 preview EXE build + packaged renderer test"
} finally {
    $env:PYTHONPATH = $oldPythonPath
}
