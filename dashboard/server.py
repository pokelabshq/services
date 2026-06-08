#!/usr/bin/env python3
"""Poke Labs Dashboard v1.0 — Live service status + control panel. Port: 8760. Zero deps."""
import http.server, json, os, socket, subprocess, time
from http import HTTPStatus

PORT = 8760
SERVICES_DIR = "/home/alx/services"

# Service registry: (name, port, description)
SERVICES = [
    ("Poke Hub", 8775, "All-in-one GitHub bot"),
    ("Link Preview", 8765, "Extract metadata from URLs"),
    ("Poke Labs Site", 8766, "Landing page + API"),
    ("Poke Bot", 8770, "GitHub auto-triage"),
    ("Telegram Bot", 8777, "Telegram notifications"),
    ("Skills Hub", 8780, "Skills marketplace"),
    ("Registry", 8785, "Agent registry"),
    ("Pricing", 8790, "Pricing API"),
    ("Dashboard", 8760, "This dashboard"),
]

def check_port(port):
    """Check if a port is open."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except:
        return False

def count_services():
    """Count service directories."""
    try:
        return len([d for d in os.listdir(SERVICES_DIR) if os.path.isdir(os.path.join(SERVICES_DIR, d))])
    except:
        return 0

def get_uptime():
    """Get system uptime."""
    try:
        with open('/proc/uptime') as f:
            return float(f.read().split()[0])
    except:
        return 0

def uptime_str(seconds):
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}h {m}m {s}s"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Labs Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.header{{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px 28px;border-bottom:1px solid #2a2a4a;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:22px;color:#00d4ff}}
.header h1 span{{color:#ff6b6b}}
.badge{{padding:5px 14px;border-radius:16px;font-size:12px;font-weight:600}}
.offline{{background:#2a1a1a;color:#ff6b6b;border:1px solid #ff6b6b33}}
.online{{background:#1a2a1a;color:#51cf66;border:1px solid #51cf6633}}
.container{{max-width:1100px;margin:0 auto;padding:20px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:20px 0}}
.stat{{background:#141420;border:1px solid #2a2a3a;border-radius:10px;padding:16px;text-align:center}}
.stat .num{{font-size:28px;font-weight:700;color:#00d4ff}}
.stat .lbl{{font-size:11px;color:#777;margin-top:4px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-top:16px}}
.card{{background:#141420;border:1px solid #2a2a3a;border-radius:10px;padding:16px}}
.card h3{{font-size:14px;color:#fff;margin-bottom:6px}}
.card p{{font-size:12px;color:#777;line-height:1.4}}
.card .port{{font-family:monospace;color:#00d4ff;font-size:11px;margin-top:6px}}
.dot{{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px}}
.off{{background:#ff6b6b}}
.on{{background:#51cf66}}
h2{{font-size:16px;color:#fff;margin:24px 0 12px;padding-bottom:6px;border-bottom:1px solid #2a2a3a}}
.wallet{{font-family:monospace;font-size:11px;color:#666;background:#141420;padding:10px 14px;border-radius:6px;border:1px solid #2a2a3a;margin-top:20px;word-break:break-all}}
.wallet b{{color:#00d4ff}}
</style>
</head>
<body>
<div class="header">
  <h1>🐾 <span>Poke</span> Labs</h1>
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:11px;color:#555">{ts}</span>
    <span class="badge {cls}">{status}</span>
  </div>
</div>
<div class="container">
  <div class="stats">
    <div class="stat"><div class="num">{svcs}</div><div class="lbl">Services Built</div></div>
    <div class="stat"><div class="num">{running}</div><div class="lbl">Running</div></div>
    <div class="stat"><div class="num">{repos}</div><div class="lbl">GitHub Repos</div></div>
    <div class="stat"><div class="num">{uptime}</div><div class="lbl">Uptime</div></div>
    <div class="stat"><div class="num">{creds}</div><div class="lbl">Credits</div></div>
  </div>
  <h2>Services</h2>
  <div class="grid">{cards}</div>
  <div class="wallet"><b>Wallet (Base):</b> 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</div>
</div>
</body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        svcs = count_services()
        running = sum(1 for _,p,_ in SERVICES if check_port(p))
        uptime_s = get_uptime()
        uptime = uptime_str(uptime_s)
        
        cards = ""
        for name, port, desc in SERVICES:
            on = check_port(port)
            dot_class = "on" if on else "off"
            status_text = "online" if on else "offline"
            cards += f'''<div class="card"><h3><span class="dot {dot_class}"></span>{name}</h3><p>{desc}</p><div class="port">:{port} — {status_text}</div></div>'''
        
        if running > 0:
            badge_cls = "online"
            badge_text = f"● {running} Online"
        else:
            badge_cls = "offline"
            badge_text = "● Offline — Funding Needed"
        
        html = TEMPLATE.format(
            ts=time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()),
            cls=badge_cls, status=badge_text,
            svcs=svcs, running=running, repos=4, uptime=uptime, creds="-$0.01",
            cards=cards
        )
        
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, fmt, *args):
        pass  # suppress stderr noise

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Labs Dashboard v1.0 on http://0.0.0.0:{PORT}")
    server.serve_forever()
