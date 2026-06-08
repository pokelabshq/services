#!/usr/bin/env python3
"""Poke Dashboard v1.0 — Unified service dashboard for Poke Labs.
Shows all services, their health, quick links, and system stats. Port 8800. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, subprocess, os, html as H

PORT = 8800
VERSION = 1

SERVICES = [
    {"name": "link-preview", "port": 8765, "url": "/api/preview", "desc": "Extract title, description, image from URLs"},
    {"name": "pokelabs-site", "port": 8766, "url": "/", "desc": "Main landing page"},
    {"name": "ws-events", "port": 8767, "url": "/", "desc": "WebSocket real-time events"},
    {"name": "graphql", "port": 8768, "url": "/graphql", "desc": "Unified GraphQL API gateway"},
    {"name": "poke-bot", "port": 8770, "url": "/", "desc": "GitHub auto-triage bot"},
    {"name": "poke-hub", "port": 8775, "url": "/", "desc": "All-in-one GitHub bot"},
    {"name": "github-stats", "port": 8779, "url": "/api/stats", "desc": "GitHub statistics"},
    {"name": "skills-mkt", "port": 8781, "url": "/", "desc": "Skills marketplace"},
    {"name": "metrics", "port": 8792, "url": "/metrics", "desc": "Prometheus metrics exporter"},
    {"name": "x402-pay", "port": 8795, "url": "/api/pay", "desc": "USDC payment gateway"},
]

def check_port(port):
    try:
        urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=2)
        return True
    except:
        return False

def get_load():
    try:
        with open("/proc/loadavg") as f:
            return f.read().split()[:3]
    except:
        return ["?", "?", "?"]

def get_mem():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        total = int(lines[0].split()[1])
        avail = int(lines[2].split()[1])
        used_pct = round((1 - avail/total) * 100, 1)
        return {"total_mb": total//1024, "avail_mb": avail//1024, "used_pct": used_pct}
    except:
        return {"total_mb": 0, "avail_mb": 0, "used_pct": 0}

def get_disk():
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        avail = st.f_bavail * st.f_frsize
        used_pct = round((1 - avail/total) * 100, 1)
        return {"total_gb": round(total/1e9,1), "avail_gb": round(avail/1e9,1), "used_pct": used_pct}
    except:
        return {"total_gb": 0, "avail_gb": 0, "used_pct": 0}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self.json({"ok": True, "v": VERSION, "port": PORT, "role": "dashboard"})
        elif p.path == "/api/services":
            self.json({"services": SERVICES})
        elif p.path == "/api/system":
            self.json({"load": get_load(), "memory": get_mem(), "disk": get_disk(), "ts": time.time()})
        elif p.path == "/":
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        load = get_load()
        mem = get_mem()
        disk = get_disk()
        rows = ""
        up_count = 0
        for s in SERVICES:
            is_up = check_port(s["port"])
            if is_up: up_count += 1
            status = "🟢 UP" if is_up else "🔴 DOWN"
            color = "#00ffaa" if is_up else "#ff4444"
            link = f'http://{self.headers.get("Host", "localhost")}:{s["port"]}{s["url"]}' if is_up else "#"
            name_link = f'<a href="{link}" target="_blank" style="color:#00ffaa;text-decoration:none">{H.escape(s["name"])}</a>' if is_up else H.escape(s["name"])
            rows += f'<tr><td>{name_link}</td><td><span style="color:{color}">{status}</span></td><td>{H.escape(s["desc"])}</td><td>{s["port"]}</td></tr>'

        s = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs — Dashboard</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0a0a1a;color:#e0e0e2;min-height:100vh;padding:20px}}
.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.06)}}
h1{{color:#00ffaa;font-size:1.5rem}}
.version{{color:#666;font-size:.75rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}}
.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px}}
.card h3{{color:#666;font-size:.75rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
.card .value{{font-size:1.8rem;font-weight:700;color:#00ffaa}}
.card .sub{{color:#666;font-size:.75rem;margin-top:4px}}
table{{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.03);border-radius:12px;overflow:hidden}}
th{{text-align:left;color:#666;font-size:.75rem;padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.06);text-transform:uppercase;letter-spacing:.5px}}
td{{padding:10px 16px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:.85rem}}
tr:hover{{background:rgba(255,255,255,0.02)}}
.progress{{height:6px;border-radius:3px;background:rgba(255,255,255,0.06);overflow:hidden;margin-top:6px}}
.progress-bar{{height:100%;border-radius:3px;background:#00ffaa}}
.progress-bar.warn{{background:#ffaa00}}
.progress-bar.danger{{background:#ff4444}}
</style></head><body>
<div class="header"><div><h1>🐙 Poke Labs Dashboard</h1><span class="version">v{VERSION} | {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}</span></div><div style="color:#666;font-size:.75rem">Port {PORT}</div></div>
<div class="grid">
<div class="card"><h3>Services</h3><div class="value">{up_count}/{len(SERVICES)}</div><div class="sub">Online</div></div>
<div class="card"><h3>Load</h3><div class="value">{load[0]}</div><div class="sub">{load[1]} / {load[2]} (1/5/15m)</div></div>
<div class="card"><h3>Memory</h3><div class="value">{mem["used_pct"]}%</div><div class="sub">{mem["avail_mb"]}MB free of {mem["total_mb"]}MB</div><div class="progress"><div class="progress-bar {"warn" if mem["used_pct"]>70 else ""}{"danger" if mem["used_pct"]>85 else ""}" style="width:{mem["used_pct"]}%"></div></div></div>
<div class="card"><h3>Disk</h3><div class="value">{disk["used_pct"]}%</div><div class="sub">{disk["avail_gb"]}GB free of {disk["total_gb"]}GB</div><div class="progress"><div class="progress-bar {"warn" if disk["used_pct"]>70 else ""}{"danger" if disk["used_pct"]>85 else ""}" style="width:{disk["used_pct"]}%"></div></div></div>
</div>
<table><thead><tr><th>Service</th><th>Status</th><th>Description</th><th>Port</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Dashboard v1.0 on :{PORT}");s.serve_forever()
