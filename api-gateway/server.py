#!/usr/bin/env python3
"""Poke Labs Unified API v1.0 — Single entry point for all microservices."""
import http.server, json, urllib.request, urllib.parse, os, sqlite3, hashlib, time, re

PORT = int(os.environ.get("PORT", 8700))
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

# Service routing table
ROUTES = {
    "/v1/preview":    {"port": 8765, "desc": "Link Preview",    "path": "/api/preview"},
    "/v1/streak":    {"port": 8785, "desc": "Streak Tracker",  "path": "/"},
    "/v1/github":    {"port": 8812, "desc": "GitHub Stats",    "path": "/api/stats"},
    "/v1/sentiment": {"port": 8849, "desc": "Sentiment",       "path": "/api/analyze"},
    "/v1/weather":   {"port": 8868, "desc": "Weather",         "path": "/api/weather"},
    "/v1/trending":  {"port": 8790, "desc": "Trending",        "path": "/api/trending"},
}

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/", ""):
            self.send_html(self.landing_page())
        elif p.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "routes": list(ROUTES.keys())})
        elif p.path == "/v1/services":
            self.send_json({"services": {k: v["desc"] for k, v in ROUTES.items()}})
        elif p.path in ROUTES:
            self.proxy_request(p.path, "GET")
        else:
            self.send_json({"error": "not found", "routes": list(ROUTES.keys())}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ROUTES:
            self.proxy_request(p.path, "POST")
        else:
            self.send_json({"error": "not found"}, 404)

    def proxy_request(self, route_key, method):
        route = ROUTES[route_key]
        target = f"http://localhost:{route['port']}{route['path']}"
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))) if method == "POST" else None
            content_type = self.headers.get("Content-Type", "application/json")
            req = urllib.request.Request(target, data=body, method=method)
            req.add_header("Content-Type", content_type)
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_json({"error": "service unavailable", "service": route["desc"], "detail": str(e)}, 503)

    def landing_page(self):
        routes_html = "".join(
            f'<tr><td><code>{k}</code></td><td>{v["desc"]}</td><td><code>:{v["port"]}</code></td></tr>'
            for k, v in ROUTES.items()
        )
        return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Poke Labs Unified API</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a14;color:#c8c8d8;padding:40px;max-width:800px;margin:0 auto}}
h1{{background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2rem}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{padding:10px;text-align:left;border-bottom:1px solid #30363d}}
th{{color:#8b949e;font-size:.85rem}}
code{{background:#161b22;padding:2px 8px;border-radius:4px;font-size:.85rem;color:#00d4ff}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin:16px 0}}
pre{{background:#0a0a14;padding:12px;border-radius:6px;overflow-x:auto;font-size:.85rem}}
a{{color:#00d4ff}}
</style></head><body>
<h1>🫧 Poke Labs Unified API</h1>
<p>Single entry point for all Poke Labs microservices.</p>
<div class="card">
<h2 style="color:#00d4ff;margin-top:0">Endpoints</h2>
<table><tr><th>Route</th><th>Service</th><th>Origin Port</th></tr>{routes_html}</table>
</div>
<div class="card">
<h2 style="color:#00d4ff;margin-top:0">Quick Start</h2>
<pre>curl -X POST http://api.pokelabs.org/v1/preview \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://github.com"}}'</pre>
</div>
<p style="color:#6e7681;font-size:.85rem">v1.0 · {len(ROUTES)} services routed · <a href="/api/health">health</a></p>
</body></html>'''

    def send_html(self, h):
        b = h.encode(); self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def send_json(self, d, c=200):
        b = json.dumps(d).encode(); self.send_response(c)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"Poke Labs Unified API v1.0 on port {PORT}")
    http.server.HTTPServer(("", PORT), H).serve_forever()
