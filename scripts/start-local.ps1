param(
    [switch]$NoFrontend
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $repoRoot ".local-run"
$dataDir = Join-Path $repoRoot ".local-data"
$runnerScript = Join-Path $PSScriptRoot "run-service.ps1"
$frontendScript = Join-Path $PSScriptRoot "run-frontend.ps1"
$powershellExe = (Get-Command powershell.exe -ErrorAction Stop).Source
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "Missing .venv\Scripts\python.exe. Run .\scripts\setup-local.ps1 first."
}

New-Item -ItemType Directory -Force -Path $runDir | Out-Null
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

$services = @(
    @{
        Name = "identity"
        Module = "services.identity.app.main:app"
        Port = 8001
        DbEnvName = "IDENTITY_DB_URL"
        DbUrl = "sqlite:///./.local-data/identity.db"
    },
    @{
        Name = "content"
        Module = "services.content.app.main:app"
        Port = 8002
        DbEnvName = "CONTENT_DB_URL"
        DbUrl = "sqlite:///./.local-data/content.db"
    },
    @{
        Name = "engagement"
        Module = "services.engagement.app.main:app"
        Port = 8003
        DbEnvName = "ENGAGEMENT_DB_URL"
        DbUrl = "sqlite:///./.local-data/engagement.db"
    },
    @{
        Name = "summary"
        Module = "services.summary.app.main:app"
        Port = 8004
        DbEnvName = "SUMMARY_DB_URL"
        DbUrl = "sqlite:///./.local-data/summary.db"
        RedisUrl = "memory://local"
    },
    @{
        Name = "gateway"
        Module = "services.gateway.app.main:app"
        Port = 8000
    }
)

$processes = @()

foreach ($service in $services) {
    $arguments = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $runnerScript,
        "-Name",
        $service.Name,
        "-Module",
        $service.Module,
        "-Port",
        $service.Port.ToString()
    )

    if ($service.ContainsKey("DbEnvName")) {
        $arguments += @("-DbEnvName", $service.DbEnvName, "-DbUrl", $service.DbUrl)
    }

    if ($service.ContainsKey("RedisUrl")) {
        $arguments += @("-RedisUrl", $service.RedisUrl)
    }

    $proc = Start-Process -FilePath $powershellExe -ArgumentList $arguments -WorkingDirectory $repoRoot -PassThru
    $processes += [pscustomobject]@{
        name = $service.Name
        pid = $proc.Id
        url = "http://127.0.0.1:$($service.Port)"
    }
}

if (-not $NoFrontend) {
    $frontendProc = Start-Process `
        -FilePath $powershellExe `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", $frontendScript) `
        -WorkingDirectory $repoRoot `
        -PassThru

    $processes += [pscustomobject]@{
        name = "frontend"
        pid = $frontendProc.Id
        url = "http://127.0.0.1:5173"
    }
}

$processes | ConvertTo-Json | Set-Content (Join-Path $runDir "local-processes.json")

Write-Host "Started ProShare local development environment."
Write-Host "Gateway:  http://127.0.0.1:8000"
Write-Host "Identity: http://127.0.0.1:8001"
Write-Host "Content:  http://127.0.0.1:8002"
Write-Host "Engage:   http://127.0.0.1:8003"
Write-Host "Summary:  http://127.0.0.1:8004"
if (-not $NoFrontend) {
    Write-Host "Frontend: http://127.0.0.1:5173"
}
Write-Host ""
Write-Host "Stop everything with: .\scripts\stop-local.ps1"
