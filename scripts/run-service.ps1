param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [Parameter(Mandatory = $true)]
    [string]$Module,

    [Parameter(Mandatory = $true)]
    [int]$Port,

    [string]$DbEnvName = "",
    [string]$DbUrl = "",
    [string]$RedisUrl = "",
    [string]$JwtSecret = "dev-secret",
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

try {
    $Host.UI.RawUI.WindowTitle = "ProShare - $Name"
} catch {
}

function Get-PythonExecutable {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return $py.Source
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    throw "Python not found. Run .\scripts\setup-local.ps1 first."
}

if ($DbEnvName -and $DbUrl) {
    Set-Item -Path "Env:$DbEnvName" -Value $DbUrl
}

if ($RedisUrl) {
    $env:REDIS_URL = $RedisUrl
}

$env:JWT_SECRET = $JwtSecret

$pythonExe = Get-PythonExecutable
$uvicornArgs = @(
    "-m",
    "uvicorn",
    $Module,
    "--host",
    "127.0.0.1",
    "--port",
    $Port.ToString()
)

if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

Write-Host "[$Name] Starting on http://127.0.0.1:$Port"
Write-Host "[$Name] Module: $Module"

& $pythonExe @uvicornArgs
