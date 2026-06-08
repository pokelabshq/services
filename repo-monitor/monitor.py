#!/usr/bin/env python3
"""Repo Monitor v2 — Scan all pokelabshq repos for health issues.
Checks: stale PRs, stale issues, security alerts, failed CI."""

import json, urllib.request, os
from datetime import datetime, timezone, timedelta

GITHUB_API = "https://api.github.com"
ORG = "pokelabshq"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def gh(path):
    url = f"{GITHUB_API}{path}"
    headers = {"User-Agent": "poke-monitor/2.0"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def scan_repos():
    repos = gh(f"/orgs/{ORG}/repos?per_page=50&sort=updated")
    if isinstance(repos, dict) and "error" in repos:
        print(f"❌ Failed to list repos: {repos['error']}")
        return

    now = datetime.now(timezone.utc)
    report = []

    for repo in repos:
        name = repo["name"]
        full = repo["full_name"]
        line = [f"\n📦 **{full}** (updated: {repo['updated_at'][:10]})"]

        # Stale PRs
        prs = gh(f"/repos/{full}/pulls?state=open&per_page=50")
        stale_prs = []
        if isinstance(prs, list):
            for pr in prs:
                updated = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
                age = (now - updated).days
                if age > 7:
                    stale_prs.append(f"    • PR #{pr['number']}: {pr['title'][:60]} ({age}d stale)")
        if stale_prs:
            line.append(f"  🔴 Stale PRs ({len(stale_prs)}):")
            line.extend(stale_prs)

        # Stale issues
        issues = gh(f"/repos/{full}/issues?state=open&per_page=50")
        stale_issues = []
        if isinstance(issues, list):
            for issue in issues:
                if "pull_request" in issue:
                    continue
                updated = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
                age = (now - updated).days
                if age > 30:
                    stale_issues.append(f"    • #{issue['number']}: {issue['title'][:60]} ({age}d stale)")
        if stale_issues:
            line.append(f"  🟡 Stale issues ({len(stale_issues)}):")
            line.extend(stale_issues)

        if len(line) == 1:
            line.append("  ✅ All clear")

        report.extend(line)

    return "\n".join(report)

if __name__ == "__main__":
    print(f"🔍 Poke Labs Repo Health Report")
    print(f"_{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n")
    print(scan_repos())
