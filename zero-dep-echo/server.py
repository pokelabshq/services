#!/usr/bin/env python3
"""Zero-Dep Echo & Health Checker v1.0
A completely dependency-free service that:
1. Echoes requests (standard)
2. Checks health of ALL other Poke services on their known ports
3. Returns a unified JSON status report
No pip install needed. Pure stdlib. Zero dependencies."""

import http.server
import json
import socket
import time
import os

PORT = 8800

# All known Poke services and their ports
SERVICES = {
    "link-preview": 8765,
    "feedback-tracker": 8766,
    "url-shortener": 8767,
    "email": 8768,
    "status-page": 8769,
    "poke-bot": 8770,
    "poke-connect": 8771,
    "poke-cast": 8772,
    "poke-forge": 8773,
    "poke-lab": 8774,
    "poke-hub": 8775,
    "telegram-bot": 8777,
    "stats-tracker": 8778,
    "doc-gen": 8779,
    "skills-hub": 8780,
    "skills-marketplace": 8781,
    "agent-cast": 8782,
    "mesh-hub": 8783,
    "data-forge": 8784,
    "agent-registry": 8785,
    "health-check": 8786,
    "task-queue": 8787,
    "cron-scheduler": 8788,
    "inbox": 8789,
    "api-gateway": 8790,
    "poke-status": 8791,
    "billing": 8795,
    "health-aggregator": 8799,
}

def check_port(port, timeout=1.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self.send_dashboard()
        elif path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "service": "zero-dep-echo"})
        elif path == "/api/echo":
            self.send_json({
                "echo": True,
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime_seconds": int(time.time() - START_TIME),
            })
        elif path == "/api/unify":
            # Check all services in parallel-ish (sequential but fast)
            running = {}
            down = {}
            for name, port in SERVICES.items():
                if check_port(port):
                    running[name] = port
                else:
                    down[name] = port
            self.send_json({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "running_count": len(running),
                "down_count": len(down),
                "total_known": len(SERVICES),
                "running": running,
                "down": down,
            })
        elif path.startswith("/api/check/"):
            # Check a single service by name
            svc = path.split("/")[-1]
            if svc in SERVICES:
                port = SERVICES[svc]
                ok = check_port(port)
                self.send_json({"service": svc, "port": port, "running": ok})
            else:
                self.send_json({"error": f"unknown service: {svc}", "known": list(SERVICES.keys())}, 404)
        else:
            self.send_json({"error": "not found", "endpoints": ["/api/health", "/api/echo", "/api/unify", "/api/check/<name>"]}, 404)

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_dashboard(self):
        running = sum(1 for p in SERVICES.values() if check_port(p))
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poke Unified Status</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg, #161b22 0%, #21262d 100%); padding: 2rem; text-align: center; border-bottom: 1px solid #30363d; }}
.header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; .accent {{ color: #58a6ff; }}
.stats {{ display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; }}
.stat {{ text-align: center; .stat .num {{ font-size: 2rem; font-weight: bold; .green {{ color: #3fb950; }}
.red {{ color: #f85149; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 1.5rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.5rem; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 0.75rem; font-size: 0.85rem; }}
.card.up {{ border-left: 3px solid #3fb950; }}
.card.down {{ border-left: 3px solid #f85149; opacity: 0.7; }}
.card .name {{ font-weight: 600; margin-bottom: 0.25rem; }}
.card .port {{ color: #8b949e; }}
</style>
</head>
<body>
<div class="header">
    <h1><span class="accent">🐾</span> Poke Unified Status</h1>
    <p>All services, one view</p>
    <div class="stats">
        <div class="stat"><div class="num green">{running}</div><div>Running</div></div>
        <div class="stat"><div class="num red">{len(SERVICES) - running}</div><div>Down</div></div>
        <div class="stat"><div class="num" style="color:#58a6ff">{len(SERVICES)}</div><div>Total</div></div>
    </div>
</div>
<div class="container">
    <div class="grid" id="grid">Loading...</div>
</div>
<script>
const SERVICES = {json.dumps(SERVICES)};
const grid = document.getElementById('grid');
async function refresh() {{
    try {{
        const r = await fetch('/api/unify');
        const d = await r.json();
        grid.innerHTML = '';
        for (const [name, port] of Object.entries(SERVICES)) {{
            const isUp = d.running.hasOwnProperty(name);
            const cls = isUp ? 'up' : 'down';
            const icon = isUp ? '🟢' : '🔴';
            grid.innerHTML += `<div class="card ${{cls}}"><div class="name">${{icon}} ${{name}}</div><div class="port">:${{port}}</div></div>`;
        }}
    }} catch(e) {{ grid.innerHTML = 'Error: ' + e; }}
}}
refresh();
setInterval(refresh, 10000);
</script>
</body>
</html>"""
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

START_TIME = time.time()

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Zero-Dep Echo running on :{PORT}")
    server.serve_forever()
