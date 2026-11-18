$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$demoPython = if (Test-Path -LiteralPath '.venv\Scripts\python.exe') { '.\.venv\Scripts\python.exe' } else { 'python' }
& $demoPython '.\scripts\reset.py'
if ($LASTEXITCODE -ne 0) { throw 'Demo reset failed. See output above.' }
