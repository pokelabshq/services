#!/usr/bin/env python3
"""Poke Labs Dashboard — Service status dashboard with auto-refresh."""
import http.server, json, socket, time
from datetime import datetime

PORT = 8780

SERVICES = [
    {"name": "Link Preview",    "port": 8765, "path": "/api/health", "desc": "Extract titles, descriptions, images from URLs"},
    {"name": "Keywords",        "port": 8766, "path": "/api/health", "desc": "Extract keywords from text"},
    {"name": "Summarize",       "port": 8767, "path": "/api/health", "desc": "Summarize text with extractive NLP"},
    {"name": "QR Code",         "port": 8768, "path": "/api/health", "desc": "Generate QR codes as PNG/SVG"},
    {"name": "DNS Checker",     "port": 8769, "path": "/api/health", "desc": "Lookup DNS records for any domain"},
    {"name": "Portal",          "port": 8770, "path": "/api/health", "desc": "API gateway & portal"},
    {"name": "Color API",       "port": 8771, "path": "/api/health", "desc": "Convert HEX/RGB/HSL colors"},
    {"name": "URL Shortener",   "port": 8772, "path": "/api/health", "desc": "Shorten URLs with analytics"},
    {"name": "Template Gen",    "port": 8773, "path": "/api/health", "desc": "Generate code from templates"},
    {"name": "Health Agg",      "port": 8774, "path": "/api/health", "desc": "Aggregate health checks"},
    {"name": "JSON to TS",      "port": 8775, "path": "/api/health", "desc": "Convert JSON to TypeScript interfaces"},
    {"name": "GitHub Webhook",  "port": 8776, "path": "/api/health", "desc": "Receive & process GitHub webhooks"},
    {"name": "Sentiment",       "port": 8777, "path": "/api/health", "desc": "Analyze text sentiment"},
    {"name": "Dashboard",       "port": 8780, "path": "/api/health", "desc": "This dashboard"},
]

def check_port(port):
    try:
        socket.setdefaulttimeout(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        r = s.connect_ex(('127.0.0.1', port))
        s.close()
        return r == 0
    except:
        return False

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Labs Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a1a;color:#e0e0e0;min-height:100vh}
.hdr{background:linear-gradient(135deg,#1a1a3e,#0d0d2b);padding:2rem;text-align:center;border-bottom:2px solid #6c63ff}
.hdr h1{font-size:2.5rem;background:linear-gradient(90deg,#6c63ff,#00d4aa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stats{display:flex;justify-content:center;gap:1.5rem;margin-top:1rem;flex-wrap:wrap}
.st{padding:.5rem 1.5rem;background:rgba(108,99,255,.1);border-radius:8px;border:1px solid rgba(108,99,255,.3);text-align:center}
.st .n{font-size:1.6rem;font-weight:700;color:#6c63ff}
.st .l{font-size:.7rem;color:#888;text-transform:uppercase;letter-spacing:1px}
.gr{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;padding:2rem;max-width:1400px;margin:0 auto}
.c{background:#12122a;border:1px solid #2a2a4a;border-radius:12px;padding:1.25rem;transition:transform .2s,border-color .2s}
.c:hover{transform:translateY(-2px);border-color:#6c63ff}
.ch{display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.up{background:#00d4aa;box-shadow:0 0 8px #00d4aa}
.dn{background:#ff4757;box-shadow:0 0 8px #ff4757}
.c h3{font-size:1rem;color:#fff}
.c .pt{font-size:.7rem;color:#6c63ff;font-family:monospace;margin-left:auto}
.c .d{font-size:.8rem;color:#888;line-height:1.4}
.ft{text-align:center;padding:2rem;color:#444;font-size:.8rem;border-top:1px solid #1a1a3e}
.rf{position:fixed;bottom:2rem;right:2rem;background:#6c63ff;color:#fff;border:none;padding:.75rem 1.5rem;border-radius:50px;cursor:pointer;font-size:.9rem;box-shadow:0 4px 15px rgba(108,99,255,.4)}
.ar{position:fixed;bottom:2rem;left:2rem;color:#666;font-size:.75rem}
</style>
</head>
<body>
<div class="hdr">
<h1>🦉 Poke Labs Dashboard</h1>
<p style="color:#888;font-size:.85rem;margin-top:.25rem">Real-time status of all micro-services</p>
<div class="stats">
  <div class="st"><div class="n">{total}</div><div class="l">Total</div></div>
  <div class="st"><div class="n" style="color:#00d4aa">{up}</div><div class="l">Online</div></div>
  <div class="st"><div class="n" style="color:#ff4757">{down}</div><div class="l">Offline</div></div>
  <div class="st"><div class="n">{pct}%</div><div class="l">Uptime</div></div>
</div>
</div>
<div class="gr">{cards}</div>
<div class="ar">Auto-refreshes every 30s • Updated: {ts}</div>
<button class="rf" onclick="location.reload()">↻ Refresh</button>
<div class="ft">Built by Poke Labs • MIT Licensed</div>
<script>setTimeout(()=>location.reload(),30000);</script>
</body>
</html>"""

CARD_TMPL = '<div class="c"><div class="ch"><div class="dot {sc}"></div><h3>{name}</h3><span class="pt">:{port}</span></div><p class="d">{desc}</p></div>'

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/api/health','/api/status'):
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"service":"dashboard","v":1}).encode())
            return
        cards = []
        up = dn = 0
        for s in SERVICES:
            ok = check_port(s['port'])
            if ok: up += 1; sc = 'up'
            else: dn += 1; sc = 'dn'
            cards.append(CARD_TMPL.format(name=s['name'],port=s['port'],desc=s['desc'],sc=sc))
        total = len(SERVICES)
        pct = round(up/total*100) if total else 0
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        html = TEMPLATE.format(total=total,up=up,down=dn,pct=pct,cards='\n'.join(cards),ts=now)
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        self.send_header('Content-Length',str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())
    def log_message(self,*a): pass

if __name__=='__main__':
    srv = http.server.HTTPServer(('0.0.0.0', PORT), H)
    print(f'Dashboard on :{PORT}')
    srv.serve_forever()
