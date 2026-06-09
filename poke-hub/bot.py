#!/usr/bin/env python3
"""
Poke Hub v1.0 — All-in-One GitHub Bot
Combines: auto-reply + stale issue closer + auto-labeler + dashboard.
Pure Python stdlib. Zero deps.

Usage: python3 poke-hub/bot.py &
Dashboard: http://localhost:8775/
Webhook: http://localhost:8775/webhook
"""
import http.server, json, hashlib, hmac, os, re, sqlite3, threading, time
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 8775
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_SECRET = os.environ.get("GITHUB_SECRET", "")
DB_PATH = "/tmp/poke-hub.db"
PROCESSED_EVENTS = set()
MAX_EVENTS = 1000

# --- Database ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS replies (event_id TEXT PRIMARY KEY, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS stale_checks (repo TEXT PRIMARY KEY, last_check TEXT)")
    conn.commit()
    conn.close()

def log_reply(event_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO replies VALUES (?, datetime('now'))", (event_id,))
    conn.commit()
    conn.close()

def is_replied(event_id):
    conn = sqlite3.connect(DB_DIR)
    row = conn.execute("SELECT 1 FROM replies WHERE event_id=?", (event_id,)).fetchone()
    conn.close()
    return row is not None

# --- GitHub API ---
def github(method, path, data=None):
    if not GITHUB_TOKEN:
        return None
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }, method=method)
    try:
        r = urlopen(req, timeout=10)
        return json.loads(r.read())
    except Exception as e:
        print(f"GitHub API error: {e}")
        return None

# --- Auto-labeling ---
PRIORITY = {
    "P0": ["crash", "security", "data loss", "outage", "emergency", "critical"],
    "P1": ["bug", "error", "fail", "regression", "urgent"],
    "P2": ["feature", "enhancement", "improve", "request"],
    "P3": ["docs", "typo", "style", "cleanup", "refactor", "chore"],
}

PR_SIZES = [(10, "S"), (50, "M"), (200, "L"), (float("inf"), "XL")]

def get_priority(title, body=""):
    text = (title + " " + body).lower()
    for p, kws in PRIORITY.items():
        for kw in kws:
            if kw in text:
                return p
    return "P2"

def get_pr_size(changed_files):
    for threshold, label in PR_SIZES:
        if changed_files < threshold:
            return label
    return "XL"

# --- Stale issue closer ---
def check_stale(org, dry_run=True):
    """Find and close stale issues (>120d) and PRs (>90d)."""
    results = {"issues_closed": 0, "prs_closed": 0, "errors": []}
    
    # Get all open issues
    page = 1
    while True:
        issues = github("GET", f"/orgs/{org}/issues?state=open&per_page=100&page={page}")
        if not issues:
            break
        for issue in issues:
            if "pull_request" in issue:
                continue  # Skip PRs from issues endpoint
            age_days = (time.time() - time.mktime(time.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"))) / 86400
            if age_days > 120:
                if dry_run:
                    results["issues_closed"] += 1
                else:
                    github("PATCH", f"/repos/{org}/{issue['repository']['full_name'].split('/')[1]}/issues/{issue['number']}", {"state": "closed"})
                    github("POST", f"/repos/{org}/{issue['repository']['full_name'].split('/')[1]}/issues/{issue['number']}/comments", {"body": "🔒 Closing stale issue (120+ days inactive). Reopen if still relevant."})
                    results["issues_closed"] += 1
        page += 1
        if len(issues) < 100:
            break
    
    return results

# --- Webhook handlers ---
def handle_issue(event):
    action = event.get("action")
    issue = event.get("issue", {})
    repo = event.get("repository", {})
    org = repo.get("owner", {}).get("login", "")
    repo_name = repo.get("name", "")
    num = issue.get("number", 0)
    title = issue.get("title", "")
    body = issue.get("body", "")
    author = issue.get("user", {}).get("login", "")

    if action == "opened":
        # Auto-label
        priority = get_priority(title, body)
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/labels", [priority])

        # Auto-reply based on issue type
        text = (title + " " + body).lower()
        if "bug" in text or "error" in text or "crash" in text:
            reply = f"🐛 Thanks for the bug report @{author}!\n\nTo help us investigate, could you share:\n1. Steps to reproduce\n2. Expected vs actual behavior\n3. Error messages or logs"
        elif "feature" in text or "request" in text:
            reply = f"💡 Thanks for the suggestion @{author}!\n\nCould you share a specific use case? That helps us prioritize."
        elif "help" in text or "how" in text or "question" in text:
            reply = f"📚 Hi @{author}!\n\nCheck our [README](https://github.com/{org}/{repo_name}#readme) and [Discussions](https://github.com/{org}/{repo_name}/discussions). If still stuck, share more details!"
        else:
            reply = f"👋 Thanks @{author}! We'll review this soon."
        
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/comments", {"body": reply})
        print(f"  Replied to issue {org}/{repo_name}#{num}")

def handle_pr(event):
    action = event.get("action")
    pr = event.get("pull_request", {})
    repo = event.get("repository", {})
    org = repo.get("owner", {}).get("login", "")
    repo_name = repo.get("name", "")
    num = pr.get("number", 0)
    changed = pr.get("changed_files", 0)
    author = pr.get("user", {}).get("login", "")

    if action == "opened":
        size = get_pr_size(changed)
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/labels", [size])
        reply = f"🎉 Thanks @{author}! PR size: **{size}** ({changed} files). CI checks will run automatically."
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/comments", {"body": reply})
        print(f"  Replied to PR {org}/{repo_name}#{num}")

def handle_comment(event):
    comment = event.get("comment", {})
    issue = event.get("issue", event.get("pull_request", {}))
    repo = event.get("repository", {})
    org = repo.get("owner", {}).get("login", "")
    repo_name = repo.get("name", "")
    num = issue.get("number", 0)
    body = comment.get("body", "").strip()
    author = comment.get("user", {}).get("login", "")

    if not body.startswith("!poke"):
        return

    cmd = body[5:].strip().split()
    if not cmd or cmd[0] == "status":
        labels = [l["name"] for l in issue.get("labels", [])]
        state = issue.get("state", "unknown")
        msg = f"📊 **Status**: {state}\n🏷️ **Labels**: {', '.join(labels) or 'none'}"
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/comments", {"body": msg})
    elif cmd[0] == "label" and len(cmd) > 1:
        label = " ".join(cmd[1:])
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/labels", [label])
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/comments", {"body": f"🏷️ Added: `{label}`"})
    elif cmd[0] == "ping":
        github("POST", f"/repos/{org}/{repo_name}/issues/{num}/comments", {"body": f"🏓 Pong! @{author}"})

# --- HTTP Server ---
class HubHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send_html(self.dashboard())
        elif path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "events": len(PROCESSED_EVENTS)})
        elif path.startswith("/stale"):
            org = self.path.split("org=")[1].split("&")[0] if "org=" in self.path else "pokelabshq"
            dry = "dry=" in self.path
            results = check_stale(org, dry_run=dry)
            self.send_json({"ok": True, "dry_run": dry, **results})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404); self.end_headers(); return

        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        sig = self.headers.get("X-Hub-Signature-256", "")
        event_id = self.headers.get("X-GitHub-Delivery", "")
        event_type = self.headers.get("X-GitHub-Event", "")

        if GITHUB_SECRET and sig:
            expected = "sha256=" + hmac.new(GITHUB_SECRET.encode(), payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, sig):
                self.send_response(401); self.end_headers(); return

        if event_id in PROCESSED_EVENTS:
            self.send_response(200); self.end_headers(); return
        PROCESSED_EVENTS.add(event_id)
        if len(PROCESSED_EVENTS) > MAX_EVENTS:
            PROCESSED_EVENTS.clear()

        try:
            event = json.loads(payload)
        except:
            self.send_response(400); self.end_headers(); return

        print(f"📨 {event_type} from {event_id[:8]}")
        if event_type == "issues":
            handle_issue(event)
        elif event_type == "pull_request":
            handle_pr(event)
        elif event_type == "issue_comment":
            handle_comment(event)

        self.send_response(200); self.end_headers()

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def dashboard(self):
        return f'''<!DOCTYPE html>
<html><head><title>🐾 Poke Hub</title>
<style>
body{{font-family:system-ui,monospace;max-width:700px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
h1{{color:#a78bfa}}.card{{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:10px 0}}
a{{color:#a78bfa}}code{{background:#333;padding:2px 6px;border-radius:4px}}
</style></head>
<body>
<h1>🐾 Poke Hub v1.0</h1>
<div class="card">
<p>All-in-One GitHub Bot: auto-reply + stale closer + labeler + dashboard</p>
<p>📊 Events: {len(PROCESSED_EVENTS)} | 🔌 Port: {PORT}</p>
</div>
<div class="card">
<h3>Endpoints</h3>
<ul>
<li><code>GET /api/health</code> — Health check</li>
<li><code>GET /stale?org=pokelabshq</code> — Check stale issues</li>
<li><code>GET /stale?org=pokelabshq&dry=1</code> — Dry run</li>
<li><code>POST /webhook</code> — GitHub webhook</li>
</ul>
</div>
<div class="card">
<h3>Auto-labels</h3>
<p>Issues: P0 (crash/security) → P3 (docs/chore)</p>
<p>PRs: S/M/L/XL by changed files</p>
</div>
</body></html>'''

    def log_message(self, *a): pass

if __name__ == "__main__":
    init_db()
    server = http.server.HTTPServer(("0.0.0.0", PORT), HubHandler)
    print(f"🐾 Poke Hub: http://localhost:{PORT}/", flush=True)
    server.serve_forever()
