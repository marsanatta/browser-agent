<#
.SYNOPSIS
  Run the M3 eval harness (real agent vs budget-matched baseline) and regenerate
  eval/REPORT.md. Needs Copilot auth available for the planner (gh login / token).

.EXAMPLE
  .\scripts\run-eval.ps1              # full set (~12 tasks, a few dozen Copilot calls)
  .\scripts\run-eval.ps1 -Limit 3     # smoke run on first 3 tasks
#>
[CmdletBinding()]
param(
  [int]$Limit = 0,
  [int]$K = 3
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw "Backend venv not found at $python. Create it first (see README -> Backend)."
}

# eval/ imports app.* (backend on path) and is itself a top-level package (root on path).
$env:PYTHONPATH = $backend
$argsList = @("-m", "eval.harness", "--k", "$K")
if ($Limit -gt 0) { $argsList += @("--limit", "$Limit") }

Push-Location $root
try {
  & $python @argsList
} finally {
  Pop-Location
}
