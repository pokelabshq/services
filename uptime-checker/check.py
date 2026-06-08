#!/usr/bin/env python3
"""Poke Labs Uptime Checker v1.
Checks all Poke Labs websites and services. Zero deps. Outputs Markdown."""

import urllib.request, json
from datetime import datetime, timezone

CHECKS = [
    ("Poke Labs Site",    "https://pokelabs.org",           "http"),
    ("Link Preview API",  "http://localhost:8765/api/health","http"),
    ("Poke Bot",          "http://localhost:8770/",         "http"),
    ("Health Dashboard",  "http://localhost:8799/api/health","http"),
    ("GitHub API",        "https://api.github.com",         "http"),
]

def check_http(url, timeout=5):
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "Poke-Uptime/1")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, r.status, ""
    except urllib.error.HTTPError as e:
        return True, e.code, str(e.reason)
    except Exception as e:
        return False, 0, str(e)[:80]

def generate():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"🔍 **Poke Labs Uptime Report**", f"_{now}_", ""]
    up = down = 0

    for name, url, kind in CHECKS:
        ok, code, err = check_http(url)
        if ok and code < 400:
            lines.append(f"  ✅ {name} — HTTP {code}")
            up += 1
        else:
            lines.append(f"  ❌ {name} — {err or f'HTTP {code}'}")
            down += 1

    lines.append(f"\n**{up} up, {down} down**")
    return "\n".join(lines)

if __name__ == "__main__":
    print(generate())
