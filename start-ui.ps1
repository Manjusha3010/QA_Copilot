# Start QA Copilot React UI (Vite dev server) — always from this project root
$Root = $PSScriptRoot
Set-Location (Join-Path $Root "frontend")

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

Write-Host "UI: http://localhost:5173/  (Chat · RAG Explorer · Status · KT Doc)"
Write-Host "API must be running: .\start.ps1  (http://127.0.0.1:8843)"
npm run dev
