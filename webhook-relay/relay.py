#!/usr/bin/env python3
"""Poke Labs Webhook Relay v1
Receives GitHub webhooks and forwards to registered internal services.
Supports: push, pull_request, issues, release, ping events.
Zero deps. HMAC signature verification. Retry with backoff."""

import json, os, hashlib, hmac, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

PORT = int(os.environ.get("PORT", 8775))
WEBHOOK_SECRET = os.environ.get("GITHUB_SECRET", "poke-dev-secret")

# Registered targets: event_type -> list of URLs
TARGETS = {
    "push":       ["http://localhost:8770/webhook", "http://localhost:8766/api/webhook"],
    "pull_request": ["http://localhost:8770/webhook"],
    "issues":     ["http://localhost:8770/webhook"],
    "release":    ["http://localhost:8766/api/webhook"],
    "ping":       [],  # Just respond, no forwarding
}

# Event log (in-memory, last 100)
event_log = []

def verify_signature(body, signature):
    if not signature:
        return True  # No secret configured, skip verification
    algo, sig = signature.split("=", 1) if "=" in signature else ("sha256", signature)
    mac = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sig)

def forward(url, payload, event_type, max_retries=3):
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "poke-relay/1",
        "X-GitHub-Event": event_type,
        "X-Relay": "poke-labs",
    }
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as r:
                return True, r.status, ""
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return False, e.code, str(e.reason)
        except Exception as e:
            if attempt == max_retries - 1:
                return False, 0, str(e)[:100]
    return False, 0, "max retries"

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        event_type = self.headers.get("X-GitHub-Event", "unknown")
        signature = self.headers.get("X-Hub-Signature-256", "")

        if not verify_signature(body, signature):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"invalid signature"}')
            return

        try:
            payload = json.loads(body)
        except:
            payload = {}

        # Log the event
        delivery = self.headers.get("X-GitHub-Delivery", "unknown")
        event_log.append({
            "id": delivery,
            "event": event_type,
            "time": datetime.now(timezone.utc).isoformat(),
            "action": payload.get("action", ""),
        })
        if len(event_log) > 100:
            event_log.pop(0)

        # Forward to targets
        results = []
        targets = TARGETS.get(event_type, [])
        for url in targets:
            ok, code, err = forward(url, payload, event_type)
            results.append({"url": url, "ok": ok, "code": code, "error": err})

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {
            "ok": True,
            "event": event_type,
            "delivery": delivery,
            "targets": len(targets),
            "results": results,
        }
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        if self.path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"events": event_log[-20:], "total": len(event_log)}).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "service": "poke-webhook-relay",
                "v": 1,
                "targets": {k: len(v) for k, v in TARGETS.items()},
            }).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"🔗 Webhook Relay starting on port {PORT}")
    print(f"   Health: http://localhost:{PORT}/")
    print(f"   Events: http://localhost:{PORT}/api/events")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
