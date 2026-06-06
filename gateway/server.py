#!/usr/bin/env python3
"""
Poke Labs API Gateway v1
Single entry point for all Poke Labs services.
Routes requests to backend services based on path.
"""

import http.server, json, urllib.request, urllib.error, os, time, threading
from datetime import datetime

PORT = 8700

# Service registry: path prefix -> (host, port, name)
SERVICES = {
    "/api/preview":    ("127.0.0.1", 8766, "link-preview"),
    "/api/skills":     ("127.0.0.1", 8781, "skills-marketplace"),
    "/api/pricing":    ("127.0.0.1", 8790, "pricing-api"),
    "/api/registry":   ("127.0.0.1", 8785, "registry"),
}

# Service health cache
health_cache = {}
health_lock = threading.Lock()

def check_service(name, host, port):
    try:
        req = urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=3)
        data = json.loads(req.read())
        return {"status": "up", "details": data}
    except Exception as e:
        return {"status": "down", "error": str(e)}

def refresh_health():
    while True:
        for prefix, (host, port, name) in SERVICES.items():
            result = check_service(name, host, port)
            with health_lock:
                health_cache[name] = result
        time.sleep(30)

class GatewayHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet logs

    def do_GET(self):
        if self.path == "/" or self.path == "/gateway":
            self.send_json(200, {
                "service": "poke-labs-gateway",
                "v": 1,
                "routes": {p: f"http://localhost:{port}" for p, (_, port, _) in SERVICES.items()},
                "docs": "https://pokelabs.org/docs"
            })
            return

        if self.path == "/api/health":
            with health_lock:
                cache = dict(health_cache)
            all_up = all(v["status"] == "up" for v in cache.values())
            self.send_json(200, {
                "ok": all_up,
                "gateway": "up",
                "ts": datetime.utcnow().isoformat(),
                "services": cache
            })
            return

        if self.path == "/api/status":
            # Detailed status page
            with health_lock:
                cache = dict(health_cache)
            html = self.render_dashboard(cache)
            self.send_html(200, html)
            return

        # Route to backend service
        matched = False
        for prefix, (host, port, name) in SERVICES.items():
            if self.path.startswith(prefix):
                matched = True
                backend_path = self.path[len(prefix):] or "/"
                if "?" in self.path:
                    backend_path += "?" + self.path.split("?", 1)[1]
                try:
                    url = f"http://{host}:{port}{backend_path}"
                    req = urllib.request.urlopen(url, timeout=10)
                    body = req.read()
                    self.send_response(200)
                    self.send_header("Content-Type", req.headers.get("Content-Type", "application/json"))
                    self.send_header("X-Gateway", "poke-labs")
                    self.send_header("X-Backend", name)
                    self.end_headers()
                    self.wfile.write(body)
                except urllib.error.HTTPError as e:
                    self.send_json(e.code, {"error": e.reason, "backend": name})
                except Exception as e:
                    self.send_json(502, {"error": f"Backend {name} unreachable: {e}"})
                break

        if not matched:
            self.send_json(404, {
                "error": "No route matched",
                "available_routes": list(SERVICES.keys())
            })

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        for prefix, (host, port, name) in SERVICES.items():
            if self.path.startswith(prefix):
                backend_path = self.path[len(prefix):] or "/"
                try:
                    url = f"http://{host}:{port}{backend_path}"
                    req = urllib.request.Request(url, data=body, method="POST")
                    req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))
                    resp = urllib.request.urlopen(req, timeout=10)
                    resp_body = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                    self.send_header("X-Gateway", "poke-labs")
                    self.send_header("X-Backend", name)
                    self.end_headers()
                    self.wfile.write(resp_body)
                except Exception as e:
                    self.send_json(502, {"error": f"Backend {name} unreachable: {e}"})
                return

        self.send_json(404, {"error": "No route matched"})

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def send_html(self, code, html):
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def render_dashboard(self, cache):
        services_html = ""
        for prefix, (host, port, name) in SERVICES.items():
            info = cache.get(name, {"status": "unknown"})
            status_color = "#22c55e" if info["status"] == "up" else "#ef4444" if info["status"] == "down" else "#f59e0b"
            status_text = info["status"].upper()
            services_html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td><code>{prefix}</code></td>
                <td><span style="color:{status_color};font-weight:bold;">● {status_text}</span></td>
                <td><a href="http://localhost:{port}" target="_blank">:{port}</a></td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html><head><title>Poke Labs Gateway</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
h1{{color:#a78bfa}}table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{padding:12px 16px;text-align:left;border-bottom:1px solid #333}}
th{{color:#a78bfa;background:#1a1a2e}}
code{{background:#1a1a2e;padding:2px 8px;border-radius:4px;font-size:0.9em}}
a{{color:#a78bfa}}
</style></head>
<body>
<h1>🐾 Poke Labs API Gateway</h1>
<p>Single entry point for all Poke Labs services. <code>:{PORT}</code></p>
<h2>Service Status</h2>
<table>
<tr><th>Service</th><th>Route</th><th>Status</th><th>Direct</th></tr>
{services_html}
</table>
<p><small>Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC · Auto-refreshes every 30s</small></p>
<script>setTimeout(()=>location.reload(),30000)</script>
</body></html>"""

if __name__ == "__main__":
    # Start health checker in background
    t = threading.Thread(target=refresh_health, daemon=True)
    t.start()
    # Initial health check
    time.sleep(1)
    for prefix, (host, port, name) in SERVICES.items():
        health_cache[name] = check_service(name, host, port)

    server = http.server.HTTPServer(("0.0.0.0", PORT), GatewayHandler)
    print(f"Gateway running on :{PORT}")
    server.serve_forever()
