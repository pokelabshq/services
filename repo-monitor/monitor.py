#!/usr/bin/env python3
import json, os, subprocess, sys
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
os.makedirs(DATA_DIR, exist_ok=True)

def gh_api(path):
    try:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception as e:
        print(f"Error: {e}")
    return None

def scan_repos():
    repos = gh_api("users/PokeLabshq/repos?per_page=100&sort=updated") or []
    report = {"scanned_at": datetime.now(timezone.utc).isoformat(), "total_repos": len(repos), "repos": [], "total_issues": 0, "total_prs": 0}
    for repo in repos:
        name = repo["name"]
        info = {"name": name, "desc": repo.get("description",""), "lang": repo.get("language",""), "stars": repo.get("stargazers_count",0), "forks": repo.get("forks_count",0), "open_issues": repo.get("open_issues_count",0), "updated": repo.get("updated_at","")}
        if info["open_issues"] > 0:
            issues = gh_api(f"repos/PokeLabshq/{name}/issues?state=open&per_page=20") or []
            info["issue_list"] = [{"num": i["number"], "title": i["title"], "by": i["user"]["login"]} for i in issues if "pull_request" not in i]
            report["total_issues"] += len(info["issue_list"])
        pulls = gh_api(f"repos/PokeLabshq/{name}/pulls?state=open&per_page=20") or []
        if pulls:
            info["pr_list"] = [{"num": p["number"], "title": p["title"], "by": p["user"]["login"]} for p in pulls]
            report["total_prs"] += len(info["pr_list"])
        report["repos"].append(info)
    with open(STATE_FILE, "w") as f:
        json.dump(report, f, indent=2)
    return report

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        result = scan_repos()
        for r in result["repos"]:
            issues = len(r.get("issue_list", []))
            prs = len(r.get("pr_list", []))
            print(f"{r['name']} [{r['lang']}] {r['stars']}stargazers {issues}issues {prs}PRs")
            for i in r.get("issue_list", []):
                print(f"  #{i['num']} {i['title']} (@{i['by']})")
            for p in r.get("pr_list", []):
                print(f"  PR#{p['num']} {p['title']} (@{p['by']})")
        print(f"\nTotal: {result['total_repos']} repos, {result['total_issues']} issues, {result['total_prs']} PRs")
    elif cmd == "json":
        print(json.dumps(scan_repos(), indent=2))
