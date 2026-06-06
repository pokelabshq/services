#!/usr/bin/env python3
"""Milestone Tracker v1 — Scans pokelabshq repos for milestone progress. Zero deps."""

import json, subprocess, urllib.request, urllib.error
from datetime import datetime, timezone

REPOS = ["pokelabshq/council", "pokelabshq/poke", "pokelabshq/services", "pokelabshq/cli"]

def gh_list(path, limit=100):
    try:
        r = subprocess.run(
            ["gh", "api", path,
             "-H", "Accept: application/vnd.github+json",
             "-H", "X-GitHub-Api-Version: 2022-11-28",
             "--paginate"],
            capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    except: return []

def bar(pct, w=20):
    f = int(w * pct / 100)
    return "█" * f + "░" * (w - f)

def generate():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = [f"🏁 **Poke Labs Milestone Report**", f"_{now}_", ""]
    total_ms = total_done = total_all = 0

    for repo in REPOS:
        ms_list = gh_list(f"repos/{repo}/milestones?state=open&per_page=10")
        name = repo.split("/")[-1]
        if not ms_list:
            L.append(f"**📦 {name}** — _No open milestones_\n")
            continue
        L.append(f"**📦 {name}**")
        for ms in ms_list:
            total_ms += 1
            o, c = ms.get("open_issues",0), ms.get("closed_issues",0)
            t = o + c
            total_done += c; total_all += t
            pct = round(c/t*100) if t else 0
            due = (ms.get("due_on","") or "No due")[:10]
            L.append(f"  `{ms.get('title','?')}`")
            L.append(f"  {bar(pct)} {pct}% ({c}/{t}) | Due: {due} | Open: {o}")
        L.append("")

    if total_ms == 0:
        L.append("_No open milestones found._")
    else:
        ov = round(total_done/total_all*100) if total_all else 0
        L.append(f"**Overall: {ov}% ({total_done}/{total_all} across {total_ms} milestones)**")
    return "\n".join(L)

if __name__ == "__main__":
    print(generate())
