#!/usr/bin/env python3
"""
Poke Bot v1.0 — GitHub Auto-Triage Bot
Receives GitHub webhooks, auto-labels issues (P0-P3) and PRs (S/M/L/XL).
Responds to !poke commands in comments.
Pure Python stdlib. Zero deps.

Usage: python3 poke-bot/bot.py &
Webhook: http://localhost:8770/webhook
"""
import http.server, json, hashlib, hmac, os, re, threading, time
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 8770
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_SECRET = os.environ.get("GITHUB_SECRET", "")
PROCESSED_EVENTS = set()
MAX_EVENTS = 1000

# Priority keywords for auto-labeling
PRIORITY_LABELS = {
    "P0": ["crash", "security", "data loss", "outage", "emergency", "critical", "broken"],
    "P1": ["bug", "error", "fail", "broken", "regression", "urgent", "important"],
    "P2": ["feature", "enhancement", "improve", "add", "request", "support"],
    "P3": ["docs", "documentation", "typo", "style", "cleanup", "refactor", "chore"],
}

PR_SIZE_LABELS = [
    (10, "S"),
    (50, "M"),
    (200, "L"),
    (float("inf"), "XL"),
]

def get_priority(title, body=""):
    text = (title + " " + body).lower()
    for priority, keywords in PRIORITY_LABELS.items():
        for kw in keywords:
            if kw in text:
                return priority
    return "P2"

def get_pr_size(changed_files):
    for threshold, label in PR_SIZE_LABELS:
        if changed_files < threshold:
            return label
    return "XL"

def verify_signature(payload, signature):
    if not GITHUB_SECRET or not signature:
        return True
    expected = "sha256=" + hmac.new(GITHUB_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def github_api(method, path, data=None):
    if not GITHUB_TOKEN:
        return None
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    req = Request(url, data=body, headers=headers, method=method)
    try:
        r = urlopen(req, timeout=10)
        return json.loads(r.read())
    except Exception as e:
        print(f"GitHub API error: {e}")
        return None

def add_label(org, repo, issue_num, label):
    return github_api("POST", f"/repos/{org}/{repo}/issues/{issue_num}/labels", [label])

def add_comment(org, repo, issue_num, body):
    return github_api("POST", f"/repos/{org}/{repo}/issues/{issue_num}/comments", {"body": body})

def handle_issue(event):
    action = event.get("action")
    issue = event.get("issue", {})
    repo = event.get("repository", {})
    org = repo.get("owner", {}).get("login", "")
    repo_name = repo.get("name", "")
    num = issue.get("number", 0)
    title = issue.get("title", "")
    body = issue.get("body", "")

    if action == "opened":
        priority = get_priority(title, body)
        add_label(org, repo_name, num, priority)
        print(f"  Labeled {org}/{repo_name}#{num} as {priority}")

        # Welcome first-time contributors
        author = issue.get("user", {}).get("login", "")
        if author:
            user_repos = github_api("GET", f"/users/{author}/repos?per_page=1")
            if user_repos is not None and len(user_repos) <= 1:
                welcome = f"👋 Welcome @{author}! Thanks for your first contribution. We'll review this soon."
                add_comment(org, repo_name, num, welcome)

def handle_pr(event):
    action = event.get("action")
    pr = event.get("pull_request", {})
    repo = event.get("repository", {})
    org = repo.get("owner", {}).get("login", "")
    repo_name = repo.get("name", "")
    num = pr.get("number", 0)
    title = pr.get("title", "")
    changed = pr.get("changed_files", 0)

    if action == "opened":
        size = get_pr_size(changed)
        add_label(org, repo_name, num, size)
        print(f"  Labeled PR {org}/{repo_name}#{num} as size {size}")

        author = pr.get("user", {}).get("login", "")
        thanks = f"🎉 Thanks for the PR @{author}! Size: **{size}** ({changed} files). We'll review it soon."
        add_comment(org, repo_name, num, thanks)

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
        add_comment(org, repo_name, num, msg)
    elif cmd[0] == "label" and len(cmd) > 1:
        label = " ".join(cmd[1:])
        add_label(org, repo_name, num, label)
        add_comment(org, repo_name, num, f"🏷️ Added label: `{label}`")
    elif cmd[0] == "ping":
        add_comment(org, repo_name, num, f"🏓 Pong! Bot is alive. @{author}")

class BotHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html(self.dashboard())
        elif self.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "events_processed": len(PROCESSED_EVENTS)})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404); self.end_headers(); return

        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        signature = self.headers.get("X-Hub-Signature-256", "")
        event_id = self.headers.get("X-GitHub-Delivery", "")
        event_type = self.headers.get("X-GitHub-Event", "")

        if not verify_signature(payload, signature):
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

        print(f"📨 {event_type} event from {event_id[:8]}")

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
<html><head><title>🐾 Poke Bot</title>
<style>
body{{font-family:system-ui,monospace;max-width:700px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
h1{{color:#a78bfa}}.card{{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:10px 0}}
code{{background:#333;padding:2px 6px;border-radius:4px}}
a{{color:#a78bfa}}
</style></head>
<body>
<h1>🐾 Poke Bot v1.0</h1>
<div class="card">
<p>GitHub Auto-Triage Bot — auto-labels issues and PRs.</p>
<p>📊 Events processed: {len(PROCESSED_EVENTS)}</p>
<p>🔌 Port: {PORT}</p>
</div>
<div class="card">
<h3>Features</h3>
<ul>
<li>Auto-labels issues: P0 (crash/security) → P3 (docs/chore)</li>
<li>Auto-labels PRs: S/M/L/XL by changed files</li>
<li>Welcome message for first-time contributors</li>
<li><code>!poke status</code> — show issue labels</li>
<li><code>!poke label &lt;name&gt;</code> — add label</li>
<li><code>!poke ping</code> — check bot is alive</li>
</ul>
</div>
<p><a href="/api/health">Health Check</a></p>
</body></html>'''

    def log_message(self, *a): pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), BotHandler)
    print(f"🐾 Poke Bot: http://localhost:{PORT}/", flush=True)
    print(f"   Webhook: http://localhost:{PORT}/webhook", flush=True)
    server.serve_forever()
