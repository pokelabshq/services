#!/usr/bin/env python3
"""
Poke Labs Status Page v1.0
Public-facing status dashboard showing health and uptime of all services.
Pure Python stdlib. Zero deps.

Usage: python3 status-page/server.py &
Dashboard: http://localhost:8792/
API: http://localhost:8792/api/status
"""
import http.server, json, os, time, threading
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError

PORT = 8792
CHECK_INTERVAL = 30  # seconds

SERVICES = [
    {"name": "Link Preview", "port": 8765, "url": "/api/health", "category": "api"},
    {"name": "Billing", "port": 8766, "url": "/api/health", "category": "core"},
    {"name": "Dashboard", "port": 8780, "url": "/api/health", "category": "core"},
    {"name": "Poke Hub", "port": 8775, "url": "/api/health", "category": "github"},
    {"name": "GitHub Trending", "port": 8788, "url": "/api/health", "category": "data"},
    {"name": "Skill Marketplace", "port": 8790, "url": "/api/health", "category": "marketplace"},
    {"name": "Service Watchdog", "port": 8799, "url": "/api/health", "category": "ops"},
    {"name": "Revenue Dashboard", "port": 8785, "url": "/api/health", "category": "core"},
]

status_cache = {}
cache_lock = threading.Lock()
start_time = time.time()

def check_service(svc):
    try:
        r = urlopen(f"http://127.0.0.1:{svc['port']}{svc['url']}", timeout=5)
        data = json.loads(r.read())
        return {"status": "up", "latency_ms": 0, "details": data}
    except URLError as e:
        return {"status": "down", "error": str(e.reason) if hasattr(e, 'reason') else str(e)}
    except Exception as e:
        return {"status": "down", "error": str(e)}

def check_all():
    global status_cache
    results = {}
    for svc in SERVICES:
        results[svc["name"]] = check_service(svc)
        results[svc["name"]]["port"] = svc["port"]
        results[svc["name"]]["category"] = svc["category"]
    with cache_lock:
        status_cache = results

def monitor_loop():
    while True:
        check_all()
        time.sleep(CHECK_INTERVAL)

class StatusHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        
        if path == "/":
            self.send_html(self.render_dashboard())
        elif path == "/api/status":
            with cache_lock:
                self.send_json(status_cache)
        elif path == "/api/health":
            with cache_lock:
                total = len(status_cache)
                up = sum(1 for s in status_cache.values() if s.get("status") == "up")
            self.send_json({"ok": True, "up": up, "total": total, "uptime_pct": round(up/max(total,1)*100, 1)})
        elif path == "/badge.svg":
            self.send_svg()
        else:
            self.send_response(404); self.end_headers()
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_svg(self):
        with cache_lock:
            total = len(status_cache) or len(SERVICES)
            up = sum(1 for s in status_cache.values() if s.get("status") == "up") if status_cache else 0
        pct = round(up / total * 100) if total else 0
        if pct >= 99:
            color = "#22c55e"
            text = "all systems operational"
        elif pct >= 80:
            color = "#f59e0b"
            text = "partial outage"
        else:
            color = "#ef4444"
            text = "major outage"
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="20">
<rect x="0" y="0" width="80" height="20" fill="#555"/>
<rect x="79" y="0" width="121" height="20" fill="{color}"/>
<text x="40" y="14" text-anchor="middle" fill="white" font-size="11" font-family="monospace">status</text>
<text x="140" y="14" text-anchor="middle" fill="white" font-size="11" font-family="monospace">{text}</text>
</svg>'''
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(svg.encode())
    
    def render_dashboard(self):
        with cache_lock:
            data = dict(status_cache)
        uptime = time.time() - start_time
        uptime_str = f"{int(uptime//3600)}h {int((uptime%3600)//60)}m"
        
        categories = {}
        for svc in SERVICES:
            cat = svc["category"]
            if cat not in categories:
                categories[cat] = []
            sv = data.get(svc["name"], {"status": "unknown"})
            sv["name"] = svc["name"]
            sv["port"] = svc["port"]
            categories[cat].append(sv)
        
        cats_html = ""
        for cat, svcs in categories.items():
            items = ""
            for s in svcs:
                st = s.get("status", "unknown")
                icon = "🟢" if st == "up" else "🔴" if st == "down" else "⚪"
                err = s.get("error", "")
                err_html = f' <span style="color:#ef4444;font-size:0.8em">({err})</span>' if err else ""
                items += f'<div style="padding:4px 0">{icon} <b>{s["name"]}</b> <span style="color:#666">:{s["port"]}</span>{err_html}</div>\n'
            cats_html += f'<div style="margin:12px 0"><h3 style="color:#a78bfa;margin:4px 0">{cat.upper()}</h3>{items}</div>\n'
        
        total = len(data) or len(SERVICES)
        up_count = sum(1 for s in data.values() if s.get("status") == "up") if data else 0
        
        return f'''<!DOCTYPE html>
<html>
<head>
<title>🐾 Poke Labs Status</title>
<meta http-equiv="refresh" content="30">
<style>
body{{font-family:system-ui,sans-serif;max-width:700px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
h1{{color:#a78bfa;margin-bottom:4px}}
.mono{{font-family:monospace}}
.card{{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:12px 0}}
.ok{{color:#22c55e}}.bad{{color:#ef4444}}.unk{{color:#6b7280}}
small{{color:#666}}
</style>
</head>
<body>
<h1>🐾 Poke Labs Status</h1>
<small>Auto-refresh every 30s · Uptime: {uptime_str}</small>

<div class="card">
📊 <b>{up_count}/{total}</b> services healthy
<pre style="margin:8px 0">
{"█" * up_count}{"░" * (total - up_count)}
</pre>
</div>

{cats_html}

<p style="margin-top:20px">
<small>
<a href="/api/status" style="color:#a78bfa">JSON API</a> · 
<a href="/badge.svg" style="color:#a78bfa">Status Badge</a> ·
All services MIT licensed · 
<a href="https://github.com/pokelabshq/services" style="color:#a78bfa">GitHub</a>
</small>
</p>
<p><small>Wallet: 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF (Base chain)</small></p>
</body></html>'''
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    check_all()
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    s = http.server.HTTPServer(("0.0.0.0", PORT), StatusHandler)
    print(f"🐾 Status Page: http://localhost:{PORT}/", flush=True)
    print(f"   Badge: http://localhost:{PORT}/badge.svg", flush=True)
    s.serve_forever()
