# Start QA Copilot API with the project venv (Python 3.11)
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating venv with Python 3.11..."
    py -3.11 -m venv (Join-Path $Root ".venv")
    & $VenvPython -m pip install --upgrade pip
    & (Join-Path $Root ".venv\Scripts\pip.exe") install -r (Join-Path $Root "requirements.txt")
}

Set-Location $Root
Write-Host "API: http://127.0.0.1:8843/  |  Dev UI: run .\start-ui.ps1 -> http://localhost:5173/"
& $VenvPython app.py
