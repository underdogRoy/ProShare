param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Get-PythonBootstrapCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return $py.Source
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    throw "Python 3.10+ not found. Install Python first."
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $pythonBootstrap = Get-PythonBootstrapCommand
    Write-Host "Creating .venv ..."
    & $pythonBootstrap -m venv ".venv"
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

Write-Host "Installing Python dependencies ..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install `
    -r "services\identity\requirements.txt" `
    -r "services\content\requirements.txt" `
    -r "services\engagement\requirements.txt" `
    -r "services\summary\requirements.txt" `
    -r "services\gateway\requirements.txt"

if (-not $SkipFrontend) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm not found. Install Node.js 18+ first."
    }

    Write-Host "Installing frontend dependencies ..."
    Set-Location (Join-Path $repoRoot "frontend")
    npm install
}

Write-Host ""
Write-Host "Local environment is ready."
Write-Host "Start everything with: .\scripts\start-local.ps1"
