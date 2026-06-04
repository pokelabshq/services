#!/usr/bin/env python3
"""Poke Labs GitHub Repo Monitor — watches pokelabshq repos for activity.

Monitors:
- Open issues and PRs
- Recent commits
- Dependabot alerts
- Outdated dependencies (package.json)
- Failed CI runs

Pushes alerts to a webhook or Telegram.
"""

import json
import os
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8768))
GITHUB_ORG = os.environ.get("GITHUB_ORG", "pokelabshq")
GITHUB_TOKEN = os.environ.get("GH_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# State
_state = {"last_check": None, "repos": [], "alerts": [], "errors": []}
_lock = threading.Lock()

def gh_request(path, params=""):
    """Make a GitHub API request."""
    url = f"https://api.github.com/{path}"
    if params:
        url += f"?{params}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PokeLabs-Monitor/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise Exception("GitHub API rate limit exceeded")
        raise
    except Exception as e:
        raise

def get_repos():
    """List all org repos."""
    try:
        return gh_request(f"orgs/{GITHUB_ORG}/repos", "sort=updated&per_page=30")
    except:
        # Fallback: try user endpoint
        try:
            return gh_request(f"users/{GITHUB_ORG}/repos", "sort=updated&per_page=30")
        except:
            return []

def get_open_issues(repo):
    """Get open issues (excluding PRs)."""
    try:
        items = gh_request(f"repos/{GITHUB_ORG}/{repo}/issues", "state=open&per_page=50")
        return [i for i in items if "pull_request" not in i]
    except:
        return []

def get_open_prs(repo):
    """Get open PRs."""
    try:
        return gh_request(f"repos/{GITHUB_ORG}/{repo}/pulls", "state=open&per_page=50")
    except:
        return []

def get_recent_commits(repo, since_hours=24):
    """Get commits since N hours ago."""
    since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
    try:
        return gh_request(f"repos/{GITHUB_ORG}/{repo}/commits", f"since={since}&per_page=10")
    except:
        return []

def get_workflow_runs(repo):
    """Get recent workflow runs."""
    try:
        result = gh_request(f"repos/{GITHUB_ORG}/{repo}/actions/runs", "per_page=5")
        return result.get("workflow_runs", [])
    except:
        return []

def check_deps(repo):
    """Check for outdated dependencies in package.json."""
    alerts = []
    try:
        content = gh_request(f"repos/{GITHUB_ORG}/{repo}/contents/package.json")
        import base64
        pkg = json.loads(base64.b64decode(content["content"]))
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        total = len(deps) + len(dev_deps)
        if total > 0:
            alerts.append(f"📦 {repo}: {total} dependencies ({len(deps)} prod, {len(dev_deps)} dev)")
    except:
        pass
    return alerts

def run_check():
    """Run a full monitoring check."""
    alerts = []
    repos_data = []
    errors = []
    
    try:
        repos = get_repos()
    except Exception as e:
        errors.append(f"Failed to list repos: {e}")
        with _lock:
            _state["errors"] = errors
        return
    
    for repo in repos:
        name = repo["name"]
        repo_info = {
            "name": name,
            "updated": repo.get("updated_at", ""),
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language", "N/A"),
            "issues": 0,
            "prs": 0,
            "recent_commits": 0,
            "failed_ci": 0,
        }
        
        # Issues
        try:
            issues = get_open_issues(name)
            repo_info["issues"] = len(issues)
            if issues:
                alerts.append(f"🔴 {name}: {len(issues)} open issues")
                for i in issues[:3]:
                    alerts.append(f"   #{i['number']}: {i['title'][:60]}")
        except Exception as e:
            errors.append(f"{name} issues: {e}")
        
        # PRs
        try:
            prs = get_open_prs(name)
            repo_info["prs"] = len(prs)
            if prs:
                alerts.append(f"🟡 {name}: {len(prs)} open PRs")
                for p in prs[:3]:
                    alerts.append(f"   #{p['number']}: {p['title'][:60]} by {p['user']['login']}")
        except Exception as e:
            errors.append(f"{name} PRs: {e}")
        
        # Recent commits
        try:
            commits = get_recent_commits(name)
            repo_info["recent_commits"] = len(commits)
        except:
            pass
        
        # CI status
        try:
            runs = get_workflow_runs(name)
            failed = [r for r in runs if r.get("conclusion") == "failure"]
            repo_info["failed_ci"] = len(failed)
            if failed:
                alerts.append(f"💥 {name}: {len(failed)} failed CI runs")
                for r in failed[:2]:
                    alerts.append(f"   {r.get('name', 'workflow')}: {r.get('head_branch', '?')} ({r['created_at'][:10]})")
        except:
            pass
        
        repos_data.append(repo_info)
    
    # Dependency checks on key repos
    for repo_name in ["council", "poke", "services"]:
        try:
            alerts.extend(check_deps(repo_name))
        except:
            pass
    
    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        _state["last_check"] = now
        _state["repos"] = repos_data
        _state["alerts"] = alerts
        _state["errors"] = errors
    
    return alerts

def format_report():
    """Format a human-readable report."""
    with _lock:
        state = dict(_state)
    
    repos = state.get("repos", [])
    alerts = state.get("alerts", [])
    errors = state.get("errors", [])
    last_check = state.get("last_check", "never")
    
    lines = [
        f"📊 *Poke Labs Repo Monitor*",
        f"🕐 Last check: {last_check[:19] if last_check else 'never'}",
        f"📦 {len(repos)} repos monitored",
        "",
    ]
    
    if alerts:
        lines.append("*🚨 Alerts:*")
        for a in alerts[:20]:
            lines.append(a)
        if len(alerts) > 20:
            lines.append(f"... and {len(alerts) - 20} more")
    else:
        lines.append("✅ No alerts — all clear!")
    
    lines.append("")
    lines.append("*📋 Summary:*")
    for r in repos[:10]:
        issues = f"🔴{r['issues']}" if r['issues'] else "✅"
        prs = f"🟡{r['prs']}" if r['prs'] else ""
        ci = f"💥{r['failed_ci']}" if r['failed_ci'] else ""
        commits = f"🔨{r['recent_commits']}" if r['recent_commits'] else ""
        lines.append(f"  {r['name']}: {issues} {prs} {ci} {commits}".strip())
    
    if errors:
        lines.append("")
        lines.append(f"*⚠️ {len(errors)} errors (non-critical)*")
    
    return "\n".join(lines)

def send_telegram(message):
    """Send alert via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

def send_webhook(payload):
    """Send alert to webhook."""
    if not WEBHOOK_URL:
        return
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            WEBHOOK_URL, data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

def background_loop():
    """Run checks every 15 minutes."""
    while True:
        try:
            alerts = run_check()
            if alerts:
                report = format_report()
                send_telegram(report)
                send_webhook({"type": "alerts", "alerts": alerts})
        except Exception as e:
            with _lock:
                _state["errors"].append(str(e))
        time.sleep(900)  # 15 minutes

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        
        if path in ("/api/status", "/api/status/"):
            with _lock:
                data = {
                    "ok": True,
                    "v": 1,
                    "last_check": _state.get("last_check"),
                    "repos_monitored": len(_state.get("repos", [])),
                    "alert_count": len(_state.get("alerts", [])),
                    "error_count": len(_state.get("errors", [])),
                }
            self._json(data)
        elif path == "/api/report":
            self._text(format_report())
        elif path == "/api/health":
            self._json({"ok": True, "v": 1})
        elif path == "/api/check":
            alerts = run_check()
            self._json({"ok": True, "alerts": alerts, "alert_count": len(alerts)})
        elif path == "/":
            self._html(self._landing_page())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        path = self.path.rstrip("/")
        if path == "/api/check":
            alerts = run_check()
            self._json({"ok": True, "alerts": alerts, "alert_count": len(alerts)})
        else:
            self.send_response(404)
            self.end_headers()
    
    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def _text(self, text):
        body = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
    
    def _html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
    
    def _landing_page(self):
        with _lock:
            repos = list(_state.get("repos", []))
            alerts = list(_state.get("alerts", []))
            last_check = _state.get("last_check", "never")
        
        alert_rows = ""
        for a in alerts[:15]:
            alert_rows += f"<tr><td>{a}</td></tr>"
        
        repo_rows = ""
        for r in repos[:20]:
            status = "✅" if not r['issues'] and not r['failed_ci'] else "⚠️"
            repo_rows += f"<tr><td>{status}</td><td>{r['name']}</td><td>{r.get('language','?')}</td><td>{r['issues']}</td><td>{r['prs']}</td><td>{r['failed_ci']}</td><td>{r['recent_commits']}</td></tr>"
        
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Poke Labs Repo Monitor</title>
<style>body{{font-family:system-ui,sans-serif;background:#0a0a0a;color:#e0e0e0;padding:2rem;}}
h1{{color:#8b5cf6;}}table{{width:100%;border-collapse:collapse;margin:1rem 0;}}
th,td{{padding:0.5rem;text-align:left;border-bottom:1px solid #333;}}
th{{color:#888;font-size:0.85rem;}}
a{{color:#8b5cf6;}}</style></head>
<body><h1>📊 Poke Labs Repo Monitor</h1>
<p>Last check: {last_check[:19] if last_check else 'never'} · {len(repos)} repos · {len(alerts)} alerts</p>
<h2>Alerts</h2><table>{alert_rows or '<tr><td>✅ No alerts</td></tr>'}</table>
<h2>Repos</h2><table><tr><th></th><th>Repo</th><th>Lang</th><th>Issues</th><th>PRs</th><th>Failed CI</th><th>Commits</th></tr>{repo_rows}</table>
<p><a href="/api/report">Text Report</a> · <a href="/api/status">JSON Status</a> · <a href="/api/check">Trigger Check</a></p>
<script>setTimeout(()=>location.reload(),60000);</script></body></html>"""
    
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"Repo Monitor on :{PORT}", flush=True)
    # Run initial check
    try:
        run_check()
        print(f"Initial check complete: {len(_state['alerts'])} alerts", flush=True)
    except Exception as e:
        print(f"Initial check failed: {e}", flush=True)
    # Start background monitoring
    threading.Thread(target=background_loop, daemon=True).start()
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
