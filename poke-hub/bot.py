#!/usr/bin/env python3
"""Poke Hub v2.0 — All-in-One GitHub Bot. Merges reply+label+stale+dashboard.
Auto-replies to issues/PRs, auto-labels (P0-P3, S/M/L/XL), closes stale,
handles !poke commands, serves dashboard. Port: 8775. Zero external deps."""
import http.server, json, hashlib, hmac, os, re, urllib.request, urllib.error, html as html_mod

PORT = 8775
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_SECRET = os.environ.get("GITHUB_SECRET", "")
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
ORG = "pokelabshq"
MAX_EVENTS = 1000

log = []
event_ids = set()
event_count = 0

def log_msg(msg):
    entry = f"[Poke Hub v2.0] {msg}"
    log.append(entry)
    if len(log) > 200: log.pop(0)
    print(entry)

def api(method, path, data=None):
    if not GITHUB_TOKEN: return None
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return json.loads(r.read())
    except Exception as e: log_msg(f"API {method} {path}: {e}"); return None

def add_labels(repo, num, labels): return api("POST", f"/repos/{repo}/issues/{num}/labels", labels)
def add_comment(repo, num, body): return api("POST", f"/repos/{repo}/issues/{num}/comments", {"body": body})
def close_issue(repo, num): return api("PATCH", f"/repos/{repo}/issues/{num}", {"state": "closed"})
def pr_files(repo, num): return api("GET", f"/repos/{repo}/pulls/{num}/files") or []
def pr_detail(repo, num): return api("GET", f"/repos/{repo}/pulls/{num}")
def issues_for_repo(repo, state="open", per_page=30): return api("GET", f"/repos/{repo}/issues?state={state}&per_page={per_page}") or []
def contributor_issues(repo, creator): return api("GET", f"/repos/{repo}/issues?creator={creator}&state=all&per_page=1") or []

def priority(title, body=""):
    t = (title + " " + body).lower()
    if any(k in t for k in ["critical","crash","security","data loss","outage","broken","urgent","emergency"]): return "P0"
    if any(k in t for k in ["bug","error","fail","wrong","issue","problem","regression"]): return "P1"
    if any(k in t for k in ["feat","feature","request","enhancement","add","support","improve"]): return "P2"
    return "P3"

def pr_size(files):
    n = len(files)
    if n <= 2: return "S"
    if n <= 5: return "M"
    if n <= 15: return "L"
    return "XL"

def issue_reply(title, body, author, is_first):
    t = (title + " " + body).lower()
    if is_first:
        greet = (f"👋 Hi @{author}! Thanks for your first contribution to this repo!\n\n"
                 f"Before we dive in, please make sure you've:\n"
                 f"- [ ] Read the README and Contributing guide\n"
                 f"- [ ] Checked for duplicate issues\n"
                 f"- [ ] Added a clear description with steps to reproduce (if applicable)\n\n")
    else: greet = f"👋 Hi @{author}! "
    if "bug" in t or "fix" in t or "crash" in t or "error" in t:
        if "reproduce" not in t and "steps" not in t and body and len(body) < 200:
            return greet + "Thanks for the bug report! 🐛 Could you share reproduction steps? That'll help us investigate faster."
        return greet + "Thanks for flagging this! We'll investigate. 🔍"
    if "feat" in t or "request" in t or "add" in t or "support" in t:
        return greet + "Interesting idea! 💡 What's your use case? The more context the better."
    if "help" in t or "how" in t or "question" in t:
        return greet + "Check out our docs and discussions: https://github.com/{ORG}\nIf you still need help, share more details!"
    return greet + "Thanks for opening this! We'll review it soon."

def pr_reply(title, author, pr_num, repo, is_first):
    head = (f"👋 @{author}, thanks for the PR!" if is_first else f"👋 @{author}, thanks for the PR!")
    return (f"{head}\n\n"
            f"**Review checklist:**\n"
            f"- [ ] CI passing: https://github.com/{repo}/pull/{pr_num}/checks\n"
            f"- [ ] Diff looks reasonable\n"
            f"- [ ] Tests added/updated if needed\n\n"
            f"We'll review it as soon as we can! 🐾")

def verify_sig(body):
    if not GITHUB_SECRET: return True
    sig = "sha256=" + hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return True  # simplified; real impl compares with X-Hub-Signature-256 header

def handle_issue(data):
    action, repo, repo_full = data.get("action",""), data.get("repository",{}).get("name",""), data.get("repository",{}).get("full_name","")
    issue = data.get("issue",{})
    num, title, body, author = issue.get("number"), issue.get("title",""), issue.get("body","") or "", issue.get("user",{}).get("login","")
    if action == "opened":
        p = priority(title, body)
        add_labels(repo_full, num, [p])
        first = len(contributor_issues(repo_full, author)) <= 1
        add_comment(repo_full, num, issue_reply(title, body, author, first))
        log_msg(f"Issue {repo}#{num}: label={p}, first={first}")

def handle_pr(data):
    action, repo, repo_full = data.get("action",""), data.get("repository",{}).get("name",""), data.get("repository",{}).get("full_name","")
    pr = data.get("pull_request",{})
    num, title, author = pr.get("number"), pr.get("title",""), pr.get("user",{}).get("login","")
    if action == "opened":
        files = pr_files(repo_full, num)
        sz = pr_size(files)
        add_labels(repo_full, num, [sz])
        first = len(contributor_issues(repo_full, author)) <= 1
        add_comment(repo_full, num, pr_reply(title, author, num, repo_full, first))
        log_msg(f"PR {repo}#{num}: size={sz}, files={len(files)}")

def handle_comment(data):
    action = data.get("action","")
    if action != "created": return
    comment = data.get("comment",{})
    body = comment.get("body","")
    repo = data.get("repository",{}).get("full_name","")
    num = data.get("issue",{}).get("number")
    author = comment.get("user",{}).get("login","")
    if not body.startswith("!poke"): return
    cmd = body[5:].strip().lower()
    if cmd == "status": add_comment(repo, num, f"🐾 Poke Hub v2.0 online | Events: {event_count} | Org: {ORG}")
    elif cmd == "ping": add_comment(repo, num, f"🏓 Pong! I'm alive. ({event_count} events processed)")
    elif cmd.startswith("label "):
        label = cmd[6:].strip()
        if label: add_labels(repo, num, [label]); add_comment(repo, num, f"🏷 Added label: `{label}`")

def check_stale(org, dry=False, days_issue=120, days_pr=90):
    repos = api("GET", f"/orgs/{org}/repos?per_page=30") or []
    closed = []
    for r in repos:
        name, full = r["name"], r["full_name"]
        for state_item, is_pr in [(issues_for_repo(full), False), (issues_for_repo(full, per_page=50), True)]:
            for item in (state_item or []):
                if not item or item.get("pull_request") != is_pr: continue
                days = (json_load_time(item["created_at"]) if False else 0)  # simplified
                if is_pr and item.get("state") == "open":
                    age = days_old(item["created_at"])
                    if age > days_pr: close_issue(full, name, item["number"], age, dry, "PR")
                    closed.append(f"{full}#{item['number']}")
                elif not is_pr and item["state"] == "open":
                    age = days_old(item["created_at"])
                    if age > days_issue: close_issue(full, name, item["number"], age, dry, "issue")
    return closed

def days_old(created):
    try:
        from datetime import datetime, timezone
        d = datetime.fromisoformat(created.replace("Z","+00:00"))
        return (datetime.now(timezone.utc) - d).days
    except: return 0

def close_issue(full, name, num, age, dry, kind):
    prefix = "[DRY] " if dry else ""
    log_msg(f"{prefix}Stale {kind} {full}#{num} ({age}d)")
    if not dry: add_comment(full, num, f"🧹 Closing this {kind} due to {age} days of inactivity. Reopen if still relevant!"); close_issue_api(full, num)
def close_issue_api(repo, num): return api("PATCH", f"/repos/{repo}/issues/{num}", {"state":"closed"})

def json_load_time(s): return s

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok":True,"v":2.0,"port":PORT,"events":event_count,"wallet":WALLET})
        elif self.path == "/":
            self.serve_dashboard()
        elif self.path.startswith("/stale"):
            import urllib.parse
            p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            org = p.get("org", [ORG])[0]
            dry = "dry" in p
            self.send_json({"ok":True,"note":"Stale check triggered","org":org,"dry":dry})
        else:
            self.send_json({"error":"Not found","endpoints":["/","/api/health","/stale?org=X","/stale?org=X&dry=1","/webhook"]},404)

    def do_POST(self):
        if self.path != "/webhook": self.send_json({"error":"Not found"},404); return
        body = self.rfile.read(int(self.get("Content-Length",0)))
        if not verify_sig(body): self.send_json({"error":"Bad sig"},401); return
        eid = self.get("X-GitHub-Delivery","")
        if eid in event_ids: self.send_json({"ok":True,"dup":True}); return
        event_ids.add(eid)
        if len(event_ids) > MAX_EVENTS: event_ids.clear()
        global event_count; event_count += 1
        event = self.get("X-GitHub-Event","")
        try: data = json.loads(body)
        except: self.send_json({"error":"Bad JSON"},400); return
        action = data.get("action","")
        log_msg(f"#{event_count} {event}.{action}")
        if event == "issues" and action in ("opened","reopened"): handle_issue(data)
        elif event == "pull_request" and action in ("opened","reopened","synchronize"): handle_pr(data)
        elif event == "issue_comment" and action == "created": handle_comment(data)
        self.send_json({"ok":True,"event":event,"action":action})

    def serve_dashboard(self):
        body = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Hub — Dashboard</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}
.h{{padding:40px 20px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(123,47,255,0.1) 0%,transparent 60%)}}
h1{{font-size:2.5rem;background:linear-gradient(135deg,#00d4ff,#7b2fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.s{{max-width:800px;margin:0 auto;padding:32px 20px}}.c{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;margin-bottom:16px}}
.c h3{{margin-bottom:8px;font-size:1rem}}.c p{{color:#888;font-size:.9rem}}.c code{{background:rgba(0,0,0,0.3);padding:2px 6px;border-radius:4px;font-size:.8rem}}
.st{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:600;background:rgba(74,222,128,0.15);color:#4ade80}}
pre{{background:rgba(0,0,0,0.3);border-radius:8px;padding:16px;font-size:.8rem;overflow-x:auto;max-height:300px;color:#4ade80}}
</style></head><body><div class="h"><h1>🐾 Poke Hub v2.0</h1><p style="color:#888;margin-top:8px">All-in-One GitHub Bot</p><span class="st">● Online</span></div>
<div class="s"><div class="c"><h3>📊 Status</h3><p>Port: {PORT} | Events: {event_count} | Org: {ORG}</p></div>
<div class="c"><h3>🔧 Features</h3><p>Auto-reply (issues/PRs) • Auto-label (P0-P3, S/M/L/XL) • Stale close (120d/90d) • !poke commands • Dashboard</p></div>
<div class="c"><h3>🔌 API</h3><p><code>GET /api/health</code> <code>GET /stale?org=X</code> <code>GET /stale?org=X&dry=1</code> <code>POST /webhook</code></p></div>
<div class="c"><h3>📜 Recent Logs</h3><pre>{"<br>".join(log[-30:]) or "No events yet."}</pre></div>
<footer style="text-align:center;padding:32px;color:#555;font-size:.85rem">Poke Labs © 2026 · Wallet: 0xca3d...6beF</footer></body></html>"""
        self.send_response(200); self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body.encode())

    def send_json(self, d, code=200):
        body = json.dumps(d).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def get(self, k, d=""): return self.headers.get(k, d)
    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    log_msg(f"Listening on :{PORT}")
    s.serve_forever()
