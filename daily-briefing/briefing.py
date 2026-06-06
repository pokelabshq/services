#!/usr/bin/env python3
"""Poke Labs Daily Briefing Generator v2.
Generates a morning briefing with repo health, open issues, and service status.
Outputs Markdown. Zero deps."""

import json, subprocess, socket, os
from datetime import datetime, timezone

REPOS = ["pokelabshq/council", "pokelabshq/services", "pokelabshq/cli"]
SERVICES = [("Site", 8766), ("Link Preview", 8765), ("Poke Bot", 8770),
            ("Telegram Bot", 8777), ("Dashboard", 8799)]

def gh_json(args):
    try:
        r = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout) if r.returncode == 0 else []
    except: return []

def check_port(port):
    try:
        s = socket.socket(); s.settimeout(1)
        s.connect(("127.0.0.1", port)); s.close(); return True
    except: return False

def generate():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = [f"☀️ **Poke Labs Daily Briefing**", f"_{now}_", ""]

    for repo in REPOS:
        name = repo.split("/")[-1]
        L.append(f"**📦 {name}**")
        issues = gh_json(["issue", "list", "-R", repo, "--state", "open", "--limit", "5",
                          "--json", "number,title,updatedAt"])
        prs = gh_json(["pr", "list", "-R", repo, "--state", "open", "--limit", "5",
                       "--json", "number,title,updatedAt"])
        if issues:
            L.append(f"  Issues ({len(issues)}):")
            for i in issues:
                L.append(f"    • #{i['number']} {i['title'][:60]}")
        else:
            L.append(f"  Issues: none ✅")
        if prs:
            L.append(f"  PRs ({len(prs)}):")
            for p in prs:
                L.append(f"    • #{p['number']} {p['title'][:60]}")
        else:
            L.append(f"  PRs: none ✅")
        L.append("")

    L.append("**🔧 Services**")
    up = down = 0
    for name, port in SERVICES:
        if check_port(port): L.append(f"  ✅ {name}"); up += 1
        else: L.append(f"  ❌ {name}"); down += 1
    L.append(f"\n_{up} up, {down} down_")
    return "\n".join(L)

if __name__ == "__main__":
    print(generate())
