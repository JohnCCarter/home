"""Dev-only proxy that adds a dark theme to tunnel-client admin UI.

tunnel-client serves http://127.0.0.1:8080/ui with low-contrast gray-on-white CSS.
This proxy listens on :8082 and injects readable dark-theme overrides.

Usage (tunnel-client must already run on :8080):
    uv run python tools/tunnel_ui_proxy.py
Then open: http://127.0.0.1:8082/ui
"""

from __future__ import annotations

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

UPSTREAM = "http://127.0.0.1:8080"
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8082

DARK_CSS = """
:root {
  color-scheme: dark;
  --bg: rgba(255, 255, 255, 0.06);
  --border: #374151;
  --muted: #9ca3af;
  --ok: #34d399;
  --warn: #fbbf24;
  --bad: #f87171;
}
html, body {
  background: #0b1220 !important;
  color: #e5e7eb !important;
}
.card,
.oauth-detail-wrap,
.oauth-detail-row td,
.tab[aria-selected="true"] {
  background: #111827 !important;
  border-color: #374151 !important;
}
.tab {
  color: #e5e7eb !important;
  border-color: #4b5563 !important;
}
.tab[aria-selected="true"] {
  background: #1f2937 !important;
  border-color: #64748b !important;
}
.muted,
.small,
.oauth-table th,
.oauth-detail-title,
.oauth-detail-summary,
.oauth-status,
.kv div:first-child {
  color: #9ca3af !important;
}
.oauth-table th,
.oauth-table td,
.oauth-detail-kv,
.kv {
  border-color: #374151 !important;
}
input,
select,
textarea,
button {
  background: #1f2937 !important;
  color: #e5e7eb !important;
  border-color: #4b5563 !important;
}
a {
  color: #7dd3fc !important;
}
code,
pre,
.mono,
.oauth-url {
  color: #cbd5e1 !important;
}
#app {
  min-height: 100vh;
}
"""

INJECT = '<link rel="stylesheet" href="/assets/home-agent-dark.css" />\n'


async def dark_css(_: Request) -> Response:
    return Response(DARK_CSS, media_type="text/css")


async def proxy(request: Request) -> Response:
    upstream_url = f"{UPSTREAM}{request.url.path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length", "connection"}
    }

    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream = await client.request(
            request.method,
            upstream_url,
            headers=headers,
            content=body if body else None,
        )

    content = upstream.content
    media_type = upstream.headers.get("content-type")

    if (
        request.method == "GET"
        and request.url.path in {"/ui", "/"}
        and media_type
        and "text/html" in media_type
    ):
        html = content.decode("utf-8", errors="replace")
        if "</head>" in html and "home-agent-dark.css" not in html:
            html = html.replace("</head>", f"{INJECT}</head>", 1)
            content = html.encode("utf-8")

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in {"content-encoding", "content-length", "transfer-encoding"}
    }
    return Response(content=content, status_code=upstream.status_code, headers=response_headers, media_type=media_type)


app = Starlette(
    routes=[
        Route("/assets/home-agent-dark.css", dark_css, methods=["GET"]),
        Route("/{path:path}", proxy, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]),
        Route("/", proxy, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]),
    ]
)


def main() -> None:
    print(f"tunnel-client dark UI proxy: http://{LISTEN_HOST}:{LISTEN_PORT}/ui")
    print(f"upstream: {UPSTREAM}")
    uvicorn.run(app, host=LISTEN_HOST, port=LISTEN_PORT, log_level="info")


if __name__ == "__main__":
    main()
