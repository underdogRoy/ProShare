param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"

try {
    $Host.UI.RawUI.WindowTitle = "ProShare - frontend"
} catch {
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm not found. Install Node.js 18+ first."
}

Set-Location $frontendDir
$env:VITE_API_URL = "http://127.0.0.1:8000"

Write-Host "[frontend] Starting on http://127.0.0.1:$Port"

npm run dev -- --host 127.0.0.1 --port $Port
