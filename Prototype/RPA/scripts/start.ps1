$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$demoPython = if (Test-Path -LiteralPath '.venv\Scripts\python.exe') { '.\.venv\Scripts\python.exe' } else { 'python' }
& $demoPython '.\scripts\start.py'
if ($LASTEXITCODE -ne 0) { throw 'Demo startup failed. See output above.' }
