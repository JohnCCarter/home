# Start the OpenAI tunnel-client for the Home Agent (profile: home-agent).
#
# Reads CONTROL_PLANE_API_KEY from the local, gitignored .env and exports it to
# the environment for tunnel-client. The key is NEVER printed. This script does
# not create .env, does not commit anything, and tools/tunnel-client/ stays
# gitignored.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$tunnelDir = Join-Path $repoRoot "tools\tunnel-client"
$envFile = Join-Path $repoRoot ".env"

if (-not (Test-Path $envFile)) {
    throw ".env not found. Add CONTROL_PLANE_API_KEY locally (see .env.example)."
}

if (-not (Test-Path $tunnelDir)) {
    throw "tools\tunnel-client not found. Download the tunnel-client binary first (see docs/llm_wiki/handoff.md)."
}

$prefix = "CONTROL_PLANE_API_KEY="
$line = Get-Content $envFile | Where-Object { $_ -like "$prefix*" } | Select-Object -First 1

if (-not $line) {
    throw "CONTROL_PLANE_API_KEY not found in .env"
}

# Substring (not Split('=')) so keys containing '=' survive; trim quotes/whitespace.
$key = $line.Substring($prefix.Length).Trim().Trim('"').Trim("'")

if (-not $key) {
    throw "CONTROL_PLANE_API_KEY is empty in .env"
}

$env:CONTROL_PLANE_API_KEY = $key

Push-Location $tunnelDir
try {
    .\tunnel-client.exe doctor --profile home-agent --explain
    .\tunnel-client.exe run --profile home-agent
}
finally {
    Pop-Location
}
