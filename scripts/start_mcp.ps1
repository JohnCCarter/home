# Start the Home Agent MCP HTTP (streamable) server on 127.0.0.1:8001.
# Sets OpenAI tunnel dev-mode so the ChatGPT tunnel's origins are allowed.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $env:MCP_DEV_OPENAI_TUNNEL = "1"
    uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
}
finally {
    Pop-Location
}
