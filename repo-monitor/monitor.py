#!/usr/bin/env python3
"""Repo Monitor v1 — Scan all pokelabshq repos for health issues."""
import json, urllib.request, urllib.parse, time, sys, os
from datetime import datetime, timedelta

GITHUB_API = "https://api.github.com"
ORG = "pokelabshq"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def gh(path):
    url = f"{GITHUB_API}{path}"
    headers = {"User-Agent": "poke-monitor/1.0"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def scan_repo(name):
    issues = {"stale_prs": [], "stale_issues": [], "failed_ci": [], "security": []}
    
    # PRs
    prs = gh(f"/repos/{ORG}/{name}/pulls?state=open&per_page=30") or []
    if isinstance(prs, list):
        cutoff = datetime.utcnow() - timedelta(days=7)
        for pr in prs:
            updated = pr.get("updated_at", "")
            if updated:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if dt.replace(tzinfo=None) < cutoff:
                    issues["stale_prs"].append(f"  #{pr['number']} {pr['title'][:60]} (updated {updated[:10]})")
    
    # Issues
    iss = gh(f"/repos/{ORG}/{name}/issues?state=open&per_page=50") or []
    if isinstance(iss, list):
        cutoff = datetime.utcnow() - timedelta(days=30)
        for i in iss:
            if "pull_request" in i:
                continue
            updated = i.get("updated_at", "")
            if updated:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if dt.replace(tzinfo=None) < cutoff:
                    issues["stale_issues"].append(f"  #{i['number']} {i['title'][:60]} (updated {updated[:10]})")
    
    # CI runs
    runs = gh(f"/repos/{ORG}/{name}/actions/runs?per_page=10") or {}
    if isinstance(runs, dict):
        for run in runs.get("workflow_runs", []):
            if run.get("conclusion") == "failure":
                issues["failed_ci"].append(f"  {run.get('name','?')} — {run.get('created_at','')[:10]}")
    
    return issues

def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"# 📊 Poke Labs Repo Health Report — {now}")
    print()
    
    repos = gh(f"/users/{ORG}/repos?per_page=50&sort=updated") or []
    if isinstance(repos, dict) and "error" in repos:
        print(f"Error: {repos['error']}")
        sys.exit(1)
    
    total_stale_prs = 0
    total_stale_issues = 0
    total_failed_ci = 0
    
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        name = repo["name"]
        print(f"## {name}")
        print(f"  ⭐ {repo.get('stargazers_count', 0)} — Updated {repo.get('updated_at','')[:10]}")
        
        issues = scan_repo(name)
        
        sp = len(issues["stale_prs"])
        si = len(issues["stale_issues"])
        fc = len(issues["failed_ci"])
        total_stale_prs += sp
        total_stale_issues += si
        total_failed_ci += fc
        
        if sp:
            print(f"  ⚠️  {sp} stale PRs:")
            for p in issues["stale_prs"][:5]:
                print(p)
        if si:
            print(f"  ⚠️  {si} stale issues:")
            for i in issues["stale_issues"][:5]:
                print(i)
        if fc:
            print(f"  ❌ {fc} failed CI:")
            for c in issues["failed_ci"][:3]:
                print(c)
        if not sp and not si and not fc:
            print("  ✅ All clear")
        print()
    
    print("---")
    print(f"## Summary")
    print(f"  Repos scanned: {len([r for r in repos if not r.get('fork') and not r.get('archived')])}")
    print(f"  Stale PRs (>7d): {total_stale_prs}")
    print(f"  Stale issues (>30d): {total_stale_issues}")
    print(f"  Failed CI runs: {total_failed_ci}")

if __name__ == "__main__":
    main()
