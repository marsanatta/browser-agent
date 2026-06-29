<#
.SYNOPSIS
  Build the frontend and run the backend (serving app + SSE + screenshots) on
  http://localhost:8123.

.EXAMPLE
  .\scripts\run-local.ps1                 # build + serve on http://localhost:8123
  .\scripts\run-local.ps1 -Port 9000      # custom port
#>
[CmdletBinding()]
param(
  [int]$Port = 8123,
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"
$backend = Join-Path $root "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw "Backend venv not found at $python. Create it first (see README -> Backend)."
}

# --- Access token: gate the public agent endpoints (fail-closed for exposure) ---
$envFile = Join-Path $backend ".env"
if (Test-Path $envFile) {
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*AGENT_ACCESS_TOKEN\s*=\s*(.+?)\s*$') { $env:AGENT_ACCESS_TOKEN = $Matches[1] }
  }
}
if (-not $env:AGENT_ACCESS_TOKEN) {
  Write-Warning "AGENT_ACCESS_TOKEN not set - agent endpoints fail closed (503). Set one in backend/.env before exposing."
}

if (-not $SkipBuild) {
  Write-Host "==> Building frontend (npm run build)" -ForegroundColor Cyan
  Push-Location $frontend
  if (-not (Test-Path "node_modules")) { npm install }
  npm run build
  Pop-Location
}

Write-Host "==> Serving backend + frontend on http://localhost:$Port" -ForegroundColor Cyan
Push-Location $backend
try {
  & $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
} finally {
  Pop-Location
}
