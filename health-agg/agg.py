#!/usr/bin/env python3
"""Health Aggregator for Poke Labs — polls all services, generates status API + RSS feed.
Port: 8790. Zero deps. Static dashboard."""
import http.server, json, os, time, urllib.request, threading
from datetime import datetime, timezone

PORT = 8790
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

SERVICES = [
    {"name": "link-preview", "url": "http://localhost:8765/api/health", "port": 8765},
    {"name": "pokelabs-site", "url": "http://localhost:8766/api/health", "port": 8766},
    {"name": "poke-hub", "url": "http://localhost:8775/api/health", "port": 8775},
    {"name": "skills-marketplace", "url": "http://localhost:8781/api/health", "port": 8781},
]

_status_cache = {"ts": 0, "results": []}

def check_service(svc):
    try:
        req = urllib.request.Request(svc["url"], method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            return {"name": svc["name"], "port": svc["port"], "ok": True,
                    "version": data.get("v", "?"), "latency_ms": 0}
    except Exception as e:
        return {"name": svc["name"], "port": svc["port"], "ok": False, "error": str(e)[:80]}

def poll():
    while True:
        results = [check_service(s) for s in SERVICES]
        _status_cache["results"] = results
        _status_cache["ts"] = time.time()
        time.sleep(15)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        elapsed = time.time() - _status_cache["ts"]
        results = _status_cache["results"]
        ok = sum(1 for r in results if r.get("ok"))

        if path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "wallet": WALLET})
        elif path in ("/api/status", "/api/healthz"):
            self.send_json({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "services_total": len(SERVICES),
                "services_up": ok,
                "services_down": len(SERVICES) - ok,
                "all_ok": ok == len(SERVICES),
                "stale_seconds": round(elapsed, 1),
                "results": results
            })
        elif path == "/api/health/rss":
            self.send_rss(results, ok)
        elif path == "/":
            self.serve_dashboard(results, ok, elapsed)
        else:
            self.send_json({"error": "Not found"}, 404)

    def serve_dashboard(self, results, ok, elapsed):
        rows = ""
        for r in results:
            color = "#4ade80" if r.get("ok") else "#ef4444"
            status = "UP" if r.get("ok") else "DOWN"
            ver = r.get("version", "?")
            err = r.get("error", "")
            rows += f'<tr><td>{r["name"]}</td><td>{r["port"]}</td>'
            rows += f'<td><span style="color:{color};font-weight:700">{status}</span></td>'
            rows += f'<td>{ver}</td><td style="color:#888;font-size:.8rem">{err}</td></tr>'

        html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta http-equiv="refresh" content="15">
<title>Poke Labs — Health Dashboard</title>
<style>body{{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;margin:0;padding:40px}}
h1{{background:linear-gradient(135deg,#00d4ff,#7b2fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
table{{width:100%;border-collapse:collapse;margin-top:24px}}
th,td{{padding:12px 16px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.08)}}
th{{color:#888;font-size:.8rem;text-transform:uppercase;letter-spacing:1px}}
.bar{{height:4px;background:#1a1a2e;border-radius:2px;margin-top:16px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,#4ade80,#00d4ff);border-radius:2px}}
</style></head><body>
<h1>🐾 Poke Labs — Health Dashboard</h1>
<p style="color:#888">{ok}/{len(results)} services up — updated {round(elapsed,0)}s ago — auto-refresh 15s</p>
<div class="bar"><div class="bar-fill" style="width:{ok/len(results)*100}%"></div></div>
<table><tr><th>Service</th><th>Port</th><th>Status</th><th>Version</th><th>Detail</th></tr>
{rows}</table>
<p style="color:#555;margin-top:32px;font-size:.8rem">API: /api/status · RSS: /api/health/rss</p></body></html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())

    def send_rss(self, results, ok):
        now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        items = ""
        for r in results:
            status = "UP" if r.get("ok") else "DOWN"
            desc = f"Service {r['name']} on port {r['port']} is {status}"
            items += f"<item><title>{r['name']} — {status}</title><description>{desc}</description></item>"
        rss = f'''<?xml version="1.0"?><rss version="2.0"><channel><title>Poke Labs Health</title>
<link>http://localhost:{PORT}</link><lastBuildDate>{now}</lastBuildDate>
<description>Poke Labs service health monitoring</description>{items}</channel></rss>'''
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml")
        self.send_header("Content-Length", str(len(rss)))
        self.end_headers()
        self.wfile.write(rss.encode())

    def send_json(self, d, code=200):
        body = json.dumps(d).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

if __name__ == "__main__":
    t = threading.Thread(target=poll, daemon=True)
    t.start()
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Health Aggregator v1.0 on :{PORT}")
    s.serve_forever()
