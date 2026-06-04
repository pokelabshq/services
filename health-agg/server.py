#!/usr/bin/env python3
"""Poke Labs Health Aggregator — Unified health check for all services."""
import http.server, json, socket, time
from datetime import datetime

PORT = 8774

SERVICES = [
    ("link-preview", 8765),
    ("keywords", 8766),
    ("summarize", 8767),
    ("qr", 8768),
    ("dns", 8769),
    ("portal", 8770),
    ("colors", 8771),
    ("url-shortener", 8772),
    ("template-gen", 8773),
    ("health-agg", 8774),
    ("json2ts", 8775),
    ("github-webhook", 8776),
    ("sentiment", 8777),
    ("dashboard", 8780),
]

def check(port):
    try:
        socket.setdefaulttimeout(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        r = s.connect_ex(('127.0.0.1', port))
        s.close()
        return r == 0
    except:
        return False

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        now = datetime.utcnow().isoformat()
        if self.path in ("/api/health", "/health"):
            self.send_json({"ok": True, "service": "health-agg", "v": 1})
            return
        if self.path in ("/api/status", "/status"):
            results = []
            up = 0
            t0 = time.time()
            for name, port in SERVICES:
                ok = check(port)
                if ok: up += 1
                results.append({"name": name, "port": port, "status": "up" if ok else "down"})
            elapsed = round((time.time() - t0) * 1000)
            total = len(SERVICES)
            self.send_json({
                "timestamp": now,
                "summary": {"total": total, "up": up, "down": total - up, "pct": round(up/total*100)},
                "check_time_ms": elapsed,
                "services": results
            })
            return
        if self.path == "/":
            self.send_html()
            return
        self.send_json({"error": "Not found"}, 404)

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self):
        rows = ""
        up = 0
        for name, port in SERVICES:
            ok = check(port)
            if ok: up += 1
            color = "#00d4aa" if ok else "#ff4757"
            status = "UP" if ok else "DOWN"
            rows += f'<tr><td>{name}</td><td>{port}</td><td style="color:{color};font-weight:bold">{status}</td></tr>\n'
        total = len(SERVICES)
        pct = round(up/total*100)
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        html = f"""<!DOCTYPE html>
<html><head><title>Poke Labs Health</title>
<style>
body{{font-family:system-ui;background:#0a0a1a;color:#e0e0e0;padding:2rem}}
h1{{color:#6c63ff}}
table{{border-collapse:collapse;width:100%;max-width:600px}}
th,td{{padding:.75rem 1rem;text-align:left;border-bottom:1px solid #2a2a4a}}
th{{color:#6c63ff}}
.bar{{background:#1a1a3e;border-radius:8px;height:20px;overflow:hidden;margin:1rem 0}}
.bar-inner{{background:linear-gradient(90deg,#6c63ff,#00d4aa);height:100%;width:{pct}%}}
</style></head><body>
<h1>🦉 Poke Labs Health</h1>
<p>{up}/{total} services online ({pct}%) — {now}</p>
<div class="bar"><div class="bar-inner"></div></div>
<table><tr><th>Service</th><th>Port</th><th>Status</th></tr>
{rows}</table>
</body></html>"""
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

if __name__ == "__main__":
    srv = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Health Agg on :{PORT}")
    srv.serve_forever()
