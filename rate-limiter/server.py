#!/usr/bin/env python3
"""Rate Limiter Service v1 — Sliding window rate limiting as a service.
Other services call this to check if a request should be allowed.
Supports: fixed-window, sliding-window, token-bucket algorithms.
"""
import http.server, json, time, threading, socket, os
from collections import defaultdict

PORT = 8783

# --- Rate Limiter Engine ---

class FixedWindow:
    def __init__(self, limit, window_sec):
        self.limit = limit
        self.window = window_sec
        self.counts = defaultdict(lambda: [0, 0])  # [count, window_start]

    def check(self, key):
        now = int(time.time())
        count, start = self.counts[key]
        if now - start >= self.window:
            self.counts[key] = [1, now]
            return True, self.limit - 1, self.window
        if count < self.limit:
            self.counts[key][0] += 1
            remaining = self.limit - count - 1
            reset = self.window - (now - start)
            return True, remaining, reset
        reset = self.window - (now - start)
        return False, 0, reset

class SlidingWindow:
    def __init__(self, limit, window_sec):
        self.limit = limit
        self.window = window_sec
        self.requests = defaultdict(list)

    def check(self, key):
        now = time.time()
        cutoff = now - self.window
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        if len(self.requests[key]) < self.limit:
            self.requests[key].append(now)
            return True, self.limit - len(self.requests[key]), int(self.window - (now - self.requests[key][0])) if self.requests[key] else self.window
        reset = int(self.requests[key][0] + self.window - now) if self.requests[key] else self.window
        return False, 0, max(1, reset)

class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets = defaultdict(lambda: [capacity, time.time()])  # [tokens, last_refill]

    def check(self, key):
        now = time.time()
        tokens, last = self.buckets[key]
        elapsed = now - last
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)
        self.buckets[key] = [tokens, now]
        if tokens >= 1:
            self.buckets[key][0] -= 1
            return True, int(tokens - 1), int((self.capacity - tokens + 1) / self.refill_rate)
        reset = int((1 - tokens) / self.refill_rate)
        return False, 0, max(1, reset)

# --- Named limiters registry ---
# Pattern: limiters["name"] = (algorithm_instance, {"limit": N, "window": S})
limiters = {}
lock = threading.Lock()

def get_or_create(name, algorithm, limit, window):
    with lock:
        if name not in limiters:
            if algorithm == "fixed":
                limiters[name] = (FixedWindow(limit, window), {"algorithm": "fixed", "limit": limit, "window": window})
            elif algorithm == "sliding":
                limiters[name] = (SlidingWindow(limit, window), {"algorithm": "sliding", "limit": limit, "window": window})
            elif algorithm == "token":
                limiters[name] = (TokenBucket(limit, window), {"algorithm": "token", "capacity": limit, "refill_per_sec": window})
        return limiters[name]

# --- HTTP Server ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><title>Rate Limiter v1 — Poke Labs</title>
<style>
body{font-family:system-ui;background:#0f0f23;color:#e0e0e0;padding:2rem}
h1{color:#00d4ff}table{border-collapse:collapse;width:100%;margin-top:1rem}
th,td{padding:.5rem 1rem;text-align:left;border-bottom:1px solid #2a2a5e}
th{color:#888;font-size:.8rem;text-transform:uppercase}
td{font-family:monospace}
.badge{padding:.2rem .5rem;border-radius:4px;font-size:.75rem}
.badge.active{background:#0a3d0a;color:#4ade80}
</style></head>
<body><h1>🚦 Rate Limiter Service v1</h1>
<p>Active rate limiter configurations</p>
<table><thead><tr><th>Name</th><th>Algorithm</th><th>Limit</th><th>Key Count</th></tr></thead>
<tbody id="rows"></tbody></table>
<script>
fetch("/api/limiters").then(r=>r.json()).then(d=>{
  document.getElementById("rows").innerHTML = Object.entries(d).map(([n,l])=>
    `<tr><td>${n}</td><td><span class="badge active">${l.config.algorithm}</span></td><td>${l.config.limit||l.config.capacity}</td><td>${l.keys}</td></tr>`
  ).join("")||"<tr><td colspan=4 style=color:#555>No limiters configured</td></tr>";
});
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "v": 1, "port": PORT, "limiters": len(limiters)}).encode())
        elif self.path == "/api/limiters":
            with lock:
                data = {name: {"config": info[1], "keys": len(info[0].counts if hasattr(info[0], 'counts') else info[0].requests if hasattr(info[0], 'requests') else info[0].buckets)} for name, info in limiters.items()}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path.startswith("/api/check/"):
            # GET /api/check/<limiter_name>?key=<client_key>
            parts = self.path.split("?")
            name = parts[0].split("/")[-1]
            params = dict(p.split("=", 1) for p in parts[1].split("&") if "=" in p) if len(parts) > 1 else {}
            key = params.get("key", "default")
            with lock:
                if name not in limiters:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"limiter '{name}' not found", "create": f"POST /api/limiters with name={name}"}).encode())
                    return
                limiter, config = limiters[name]
            allowed, remaining, reset = limiter.check(key)
            self.send_response(200 if allowed else 429)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-RateLimit-Remaining", str(remaining))
            self.send_header("X-RateLimit-Reset", str(reset))
            self.end_headers()
            self.wfile.write(json.dumps({"allowed": allowed, "remaining": remaining, "reset_seconds": reset, "limiter": name, "key": key}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/limiters":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            name = body.get("name")
            algorithm = body.get("algorithm", "sliding")
            limit = body.get("limit", 10)
            window = body.get("window", 60)
            if not name:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "name is required"}).encode())
                return
            limiter, config = get_or_create(name, algorithm, limit, window)
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"created": name, "config": config}).encode())
        elif self.path.startswith("/api/check/"):
            parts = self.path.split("?")
            name = parts[0].split("/")[-1]
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            key = body.get("key", "default")
            with lock:
                if name not in limiters:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"limiter '{name}' not found"}).encode())
                    return
                limiter, config = limiters[name]
            allowed, remaining, reset = limiter.check(key)
            self.send_response(200 if allowed else 429)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-RateLimit-Remaining", str(remaining))
            self.send_header("X-RateLimit-Reset", str(reset))
            self.end_headers()
            self.wfile.write(json.dumps({"allowed": allowed, "remaining": remaining, "reset_seconds": reset}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Rate Limiter v1 on :{PORT}")
    s.serve_forever()
