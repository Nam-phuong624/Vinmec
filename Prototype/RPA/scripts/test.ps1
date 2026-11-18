$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$demoPython = if (Test-Path -LiteralPath '.venv\Scripts\python.exe') { '.\.venv\Scripts\python.exe' } else { 'python' }
$env:PYTHONPATH = "$projectRoot\.deps;$projectRoot"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
& $demoPython -m pytest tests -q --junitxml=docs/patient-browser-test-results.xml
if ($LASTEXITCODE -ne 0) { throw 'Tests failed. See output above.' }
