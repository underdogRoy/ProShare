$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$stateFile = Join-Path $repoRoot ".local-run\local-processes.json"

if (-not (Test-Path $stateFile)) {
    Write-Host "No saved local process list found."
    exit 0
}

$saved = Get-Content $stateFile -Raw | ConvertFrom-Json
if ($saved -isnot [System.Array]) {
    $saved = @($saved)
}

foreach ($item in $saved) {
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($item.pid)" -ErrorAction SilentlyContinue
    if (-not $processInfo) {
        Write-Host "Skipped $($item.name): PID $($item.pid) is no longer running."
        continue
    }

    $commandLine = $processInfo.CommandLine
    if ($commandLine -notlike "*scripts\run-service.ps1*" -and $commandLine -notlike "*scripts\run-frontend.ps1*") {
        Write-Host "Skipped $($item.name): PID $($item.pid) is not a ProShare local dev shell."
        continue
    }

    Stop-Process -Id $item.pid -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped $($item.name) (PID $($item.pid))."
}

Remove-Item $stateFile -Force
