# Start the Home Agent REST / OAuth backend (FastAPI) on port 8000.
# Read-only: serves /calendar, /mail, /health, /status and Microsoft OAuth.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    uv run uvicorn app.main:app --port 8000
}
finally {
    Pop-Location
}
