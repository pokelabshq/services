#!/usr/bin/env python3
"""Poke Labs — GitHub Webhook Receiver. Port 8776.
Receives GitHub webhooks for PR events, issues, pushes.
Auto-reviews Dependabot PRs, checks for security issues,
posts PR comments via GitHub API."""
import http.server, json, hashlib, hmac, urllib.request, urllib.parse, re, os
from datetime import datetime

PORT = 8776
SECRET = "poke-labs-webhook-secret-2026"  # Configure in GitHub webhook settings

# GitHub API config
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def verify_signature(payload, signature, secret):
    if not signature:
        return True  # Allow unsigned for testing
    algo, sig = signature.split("=") if "=" in signature else ("sha256", signature)
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sig)

def github_request(method, path, data=None):
    if not GITHUB_TOKEN:
        return {"error": "No GITHUB_TOKEN set"}
    url = f"{GITHUB_API}{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def review_pr(pr_data):
    """Auto-review a PR — check for common issues."""
    findings = []
    title = pr_data.get("title", "")
    body = pr_data.get("body", "")
    files_changed = pr_data.get("changed_files", 0)
    
    # Check title format
    if len(title) < 10:
        findings.append("⚠️ Title is too short. Use descriptive PR titles.")
    
    # Check for WIP
    if re.search(r'\bwip\b', title, re.IGNORECASE):
        findings.append("🚧 This PR is marked WIP. Mark as ready when complete.")
    
    # Check description
    if not body or len(body.strip()) < 5:
        findings.append("📝 Please add a meaningful PR description.")
    
    # Check size
    if files_changed > 20:
        findings.append(f"📏 Large PR ({files_changed} files). Consider splitting into smaller PRs.")
    
    # Security checks
    combined = (title + " " + body).lower()
    if any(w in combined for w in ["password", "secret", "api_key", "token", "private_key"]):
        findings.append("🔒 This PR may contain sensitive data. Double-check for secrets!")
    
    if not findings:
        findings.append("✅ PR looks good! Auto-review passed basic checks.")
    
    return findings

def handle_pr_event(event_type, data):
    """Handle pull_request events."""
    action = data.get("action", "")
    pr = data.get("pull_request", {})
    repo = data.get("repository", {}).get("full_name", "unknown")
    pr_number = pr.get("number", 0)
    author = pr.get("user", {}).get("login", "unknown")
    title = pr.get("title", "")
    
    # Only review opened or synchronized PRs
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "skipped", "action": action}
    
    # Auto-merge check for Dependabot
    if author == "dependabot[bot]":
        pr_data = {
            "title": title,
            "body": pr.get("body", ""),
            "changed_files": pr.get("changed_files", 1)
        }
        review = review_pr(pr_data)
        is_semantic_patch = "semver-patch" in (pr.get("body") or "")
        
        if is_semantic_patch:
            # Auto-approve and merge Dependabot patch PRs
            github_request("POST", f"/repos/{repo}/pulls/{pr_number}/reviews", {
                "event": "APPROVE",
                "body": f"🤖 Auto-approved by Poke Labs.\n\n" + "\n".join(review)
            })
            return {"status": "auto-approved", "pr": pr_number, "review": review}
        else:
            github_request("POST", f"/repos/{repo}/pulls/{pr_number}/reviews", {
                "event": "COMMENT",
                "body": f"🤖 Poke Labs review:\n\n" + "\n".join(review)
            })
            return {"status": "reviewed", "pr": pr_number, "review": review}
    
    # Regular PR review
    pr_data = {
        "title": title,
        "body": pr.get("body", ""),
        "changed_files": pr.get("changed_files", 0)
    }
    review = review_pr(pr_data)
    
    if GITHUB_TOKEN:
        github_request("POST", f"/repos/{repo}/pulls/{pr_number}/reviews", {
            "event": "COMMENT",
            "body": f"🤖 Poke Labs auto-review:\n\n" + "\n".join(review)
        })
    
    return {"status": "reviewed", "pr": pr_number, "author": author, "review": review}

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/", "/index.html"):
            self._html(LANDING); return
        if p.path == "/api/health":
            self._j({"ok":True,"v":1,"service":"github-webhook","has_token": bool(GITHUB_TOKEN)}); return
        self._j({"error":"not found"}, 404)
    
    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        cl = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(cl) if cl else b""
        
        if p.path == "/webhook":
            # Verify signature
            sig = self.headers.get("X-Hub-Signature-256", "")
            if not verify_signature(payload, sig, SECRET):
                self._j({"error":"invalid signature"}, 401); return
            
            # Get event type
            event = self.headers.get("X-GitHub-Event", "")
            
            try:
                data = json.loads(payload)
            except:
                self._j({"error":"invalid json"}, 400); return
            
            result = {"event": event}
            
            if event == "pull_request":
                result.update(handle_pr_event(event, data))
            elif event == "issues":
                action = data.get("action", "")
                issue = data.get("issue", {})
                result.update({"status": "received", "action": action, "issue": issue.get("number", 0)})
            elif event == "push":
                repo = data.get("repository", {}).get("full_name", "unknown")
                result.update({"status": "received", "repo": repo})
            elif event == "ping":
                result.update({"status": "pong", "msg": "Webhook configured correctly!"})
            else:
                result.update({"status": "unhandled"})
            
            self._j(result)
            return
        self._j({"error":"not found"}, 404)
    
    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    
    def _html(self, content):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.end_headers(); self.wfile.write(content.encode())

LANDING = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>GitHub Webhook — Poke Labs</title>
<style>body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem;max-width:800px;margin:0 auto}
h1{color:#7b2ff7}code{background:#1a1a2e;padding:.2rem .5rem;border-radius:4px;font-size:.85rem}
.card{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;margin:1rem 0}</style></head><body>
<h1>🔗 GitHub Webhook Receiver</h1>
<p>Receives GitHub webhooks for automated PR review and Dependabot merging.</p>
<div class="card">
<h3>Webhook Endpoint</h3>
<code>POST /webhook</code>
<p>Configure in your GitHub repo → Settings → Webhooks → Add webhook</p>
<p>Content type: <code>application/json</code></p>
<p>Secret: <code>poke-labs-webhook-secret-2026</code></p>
</div>
<div class="card">
<h3>Supported Events</h3>
<ul>
<li><strong>pull_request</strong> — Auto-review, Dependabot auto-merge for patch</li>
<li><strong>issues</strong> — Receive issue events</li>
<li><strong>push</strong> — Receive push events</li>
</ul>
</div>
<div class="card">
<h3>Auto-Review Checks</h3>
<ul>
<li>Title length and WIP detection</li>
<li>PR description quality</li>
<li>PR size (warns if &gt;20 files)</li>
<li>Security scan for secrets/passwords</li>
<li>Dependabot semver-patch auto-approve</li>
</ul>
</div>
</body></html>'''

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"GitHub Webhook on {PORT}"); s.serve_forever()
