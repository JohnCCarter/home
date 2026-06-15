# Start the OpenAI tunnel-client for the Home Agent.
#
# Profile selection (one tunnel per physical computer):
#   .\scripts\start_tunnel_client.ps1                          # default: home-agent (home)
#   .\scripts\start_tunnel_client.ps1 -Profile home-agent-work # work computer
#   $env:TUNNEL_PROFILE="home-agent-work"; .\scripts\start_tunnel_client.ps1
#
# Reads CONTROL_PLANE_API_KEY from the local, gitignored .env and exports it to
# the environment for tunnel-client. The key is NEVER printed (the profile name
# is not secret and is printed). This script does not create .env, does not
# commit anything, and tools/tunnel-client/ stays gitignored.
param(
    [string]$Profile = $env:TUNNEL_PROFILE
)

if (-not $Profile) {
    $Profile = "home-agent"
}

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

Write-Host "Using tunnel profile: $Profile"

Push-Location $tunnelDir
try {
    .\tunnel-client.exe doctor --profile $Profile --explain
    .\tunnel-client.exe run --profile $Profile
}
finally {
    Pop-Location
}
