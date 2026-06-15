"""Shared HTML styling for browser-facing REST pages."""

BASE_STYLES = """
    :root {
      color-scheme: dark;
      --bg: #0b1220;
      --surface: #111827;
      --surface-2: #1f2937;
      --text: #e5e7eb;
      --muted: #9ca3af;
      --border: #374151;
      --link: #7dd3fc;
      --link-hover: #bae6fd;
      --accent: #2dd4bf;
      --warn: #fbbf24;
    }
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, Segoe UI, sans-serif;
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at top, #172554 0%, var(--bg) 42%);
      color: var(--text);
      line-height: 1.5;
    }
    main {
      max-width: 56rem;
      margin: 0 auto;
      padding: 2rem 1.25rem 3rem;
    }
    h1 {
      margin: 0 0 1rem;
      font-size: 1.75rem;
      color: var(--accent);
    }
    p { margin: 0.75rem 0; color: var(--text); }
    a {
      color: var(--link);
      text-decoration: none;
    }
    a:hover { color: var(--link-hover); text-decoration: underline; }
    .nav {
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
      color: var(--muted);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 0.5rem;
      overflow: hidden;
    }
    th, td {
      padding: 0.75rem 0.9rem;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }
    th {
      background: var(--surface-2);
      color: var(--muted);
      font-weight: 600;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    tr:last-child td { border-bottom: none; }
    .empty {
      background: var(--surface);
      border: 1px dashed var(--border);
      border-radius: 0.5rem;
      padding: 1rem;
      color: var(--muted);
    }
    .warn { color: var(--warn); }
"""

NARROW_MAIN_STYLES = """
    main { max-width: 40rem; }
"""
