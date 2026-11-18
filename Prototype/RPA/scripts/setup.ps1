$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python environment.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& '.\.venv\Scripts\python.exe' -m scripts.generate_demo
if ($LASTEXITCODE -ne 0) { throw 'Demo data generation failed.' }
& '.\.venv\Scripts\python.exe' -c 'from oh_desktop.launcher import build; print(build())'
if ($LASTEXITCODE -ne 0) { throw 'OH Desktop build failed.' }
Write-Host 'Setup complete. Run .\scripts\start.ps1 to open OH Desktop and RPA.'
