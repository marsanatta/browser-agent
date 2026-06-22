<#
.SYNOPSIS
  Build the frontend, run the backend (serving app + SSE + screenshots), and
  optionally expose it via a Cloudflare quick tunnel (no Cloudflare account).

.EXAMPLE
  .\scripts\run-local.ps1                 # build + serve on http://localhost:8123
  .\scripts\run-local.ps1 -Port 9000      # custom port
  .\scripts\run-local.ps1 -Tunnel         # also start a *.trycloudflare.com tunnel
#>
[CmdletBinding()]
param(
  [int]$Port = 8123,
  [switch]$Tunnel,
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

if (-not $SkipBuild) {
  Write-Host "==> Building frontend (npm run build)" -ForegroundColor Cyan
  Push-Location $frontend
  if (-not (Test-Path "node_modules")) { npm install }
  npm run build
  Pop-Location
}

if ($Tunnel) {
  $cf = (Get-Command cloudflared -ErrorAction SilentlyContinue)?.Source
  if (-not $cf) {
    Write-Warning "cloudflared not found. Install: winget install --id Cloudflare.cloudflared"
  } else {
    Write-Host "==> Starting Cloudflare quick tunnel -> http://localhost:$Port" -ForegroundColor Cyan
    Start-Process -FilePath $cf -ArgumentList @("tunnel", "--url", "http://localhost:$Port")
    Write-Host "    (watch that window for the https://<random>.trycloudflare.com URL)" -ForegroundColor DarkGray
  }
}

Write-Host "==> Serving backend + frontend on http://localhost:$Port" -ForegroundColor Cyan
Push-Location $backend
try {
  & $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
} finally {
  Pop-Location
}
