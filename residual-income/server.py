#!/usr/bin/env python3
"""
Poke Labs Revenue Dashboard v1.0
Tracks all x402 payments, usage stats, and earnings across services.
Pure Python stdlib. Zero deps.

Usage: python3 residual-income/server.py &
Dashboard: http://localhost:8785/
API: http://localhost:8785/api/revenue
"""
import http.server, json, time, os, socket
from datetime import datetime, timedelta
from urllib.request import urlopen
from urllib.error import URLError

PORT = 8785
DATA_DIR = "/tmp/pokelabs-revenue"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

SERVICES = {
    "link-preview": 8765,
    "billing": 8766,
    "poke-hub": 8775,
    "dashboard": 8780,
    "url-shortener": 8767,
}

def check_service(port):
    try:
        r = urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3)
        return json.loads(r.read())
    except:
        return None

def get_usage_data(port):
    try:
        r = urlopen(f"http://127.0.0.1:{port}/api/usage", timeout=3)
        return json.loads(r.read())
    except:
        return None

def load_revenue_log():
    f = os.path.join(DATA_DIR, "payments.jsonl")
    if not os.path.exists(f):
        return []
    with open(f) as fp:
        return [json.loads(l) for l in fp if l.strip()]

def record_payment(service, amount_usdc, source="x402"):
    f = os.path.join(DATA_DIR, "payments.jsonl")
    entry = {
        "ts": datetime.now().isoformat(),
        "service": service,
        "amount_usdc": amount_usdc,
        "source": source
    }
    with open(f, "a") as fp:
        fp.write(json.dumps(entry) + "\n")

def revenue_stats():
    payments = load_revenue_log()
    total = sum(p["amount_usdc"] for p in payments)
    by_service = {}
    by_day = {}
    for p in payments:
        svc = p["service"]
        by_service[svc] = by_service.get(svc, 0) + p["amount_usdc"]
        day = p["ts"][:10]
        by_day[day] = by_day.get(day, 0) + p["amount_usdc"]
    today = datetime.now().isoformat()[:10]
    month = datetime.now().isoformat()[:7]
    today_total = by_day.get(today, 0)
    month_total = sum(v for k, v in by_day.items() if k.startswith(month))
    return {
        "total_usdc": round(total, 6),
        "today_usdc": round(today_total, 6),
        "month_usdc": round(month_total, 6),
        "payment_count": len(payments),
        "by_service": {k: round(v, 6) for k, v in by_service.items()},
        "by_day": {k: round(v, 6) for k, v in sorted(by_day.items())[-30:]},
        "recent_payments": payments[-20:]
    }

class RevenueHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_html(self.dashboard())
        elif self.path == '/api/revenue':
            self.send_json(revenue_stats())
        elif self.path == '/api/services':
            svc_status = {}
            for name, port in SERVICES.items():
                h = check_service(port)
                u = get_usage_data(port) if h else None
                svc_status[name] = {"port": port, "healthy": h is not None, "details": h, "usage": u}
            self.send_json(svc_status)
        elif self.path == '/api/record' or self.path.startswith('/api/record?'):
            # GET /api/record?service=billing&amount=0.001
            params = {}
            if '?' in self.path:
                for kv in self.path.split('?')[1].split('&'):
                    if '=' in kv:
                        k, v = kv.split('=', 1)
                        params[k] = v
            svc = params.get('service', 'unknown')
            try:
                amount = float(params.get('amount', 0))
            except:
                amount = 0
            if amount > 0:
                record_payment(svc, amount)
            self.send_json({"ok": True, "recorded": {"service": svc, "amount_usdc": amount}})
        else:
            self.send_response(404); self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/record':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            svc = body.get('service', 'unknown')
            amount = float(body.get('amount_usdc', 0))
            if amount > 0:
                record_payment(svc, amount)
            self.send_json({"ok": True, "recorded": {"service": svc, "amount_usdc": amount}})
        else:
            self.send_response(404); self.end_headers()
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def dashboard(self):
        stats = revenue_stats()
        svc_rows = ""
        for name, port in SERVICES.items():
            h = check_service(port)
            status = "🟢" if h else "🔟"
            svc_rows += f'<tr><td>{name}</td><td>{port}</td><td>{status}</td></tr>'
        return f'''<!DOCTYPE html>
<html><head><title>🐾 Revenue Dashboard</title>
<style>
body{{font-family:system-ui,monospace;max-width:900px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
.card{{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:20px;margin:10px 0}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
h1,h2{{color:#a78bfa}}
.big{{font-size:2em;font-weight:bold;color:#22c55e}}
table{{width:100%;border-collapse:collapse;margin:10px 0}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #333}}
th{{color:#a78bfa}}
small{{color:#666}}
a{{color:#a78bfa}}
</style></head>
<body>
<h1>🐾 Poke Labs Revenue Dashboard</h1>
<div class="grid">
<div class="card"><h2>💰 Total Earnings</h2><div class="big">{stats['total_usdc']} USDC</div><small>{stats['payment_count']} payments</small></div>
<div class="card"><h2>📅 This Month</h2><div class="big">{stats['month_usdc']} USDC</div><small>Today: {stats['today_usdc']}</small></div>
</div>
<div class="card"><h2>🔧 Services</h2>
<table><tr><th>Service</th><th>Port</th><th>Status</th></tr>{svc_rows}</table>
<small>Health checked: {datetime.now().isoformat()[:19]}</small></div>
<div class="card"><h2>💳 Wallet</h2><code>0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code> (Base chain)</div>
<p><small>Record payment: <code>GET /api/record?service=name&amount=0.001</code></small></p>
<p><a href="/api/revenue">API</a> | <a href="/api/services">Services</a></p>
</body></html>'''
    
    def log_message(self, *a): pass

if __name__ == '__main__':
    s = http.server.HTTPServer(('0.0.0.0', PORT), RevenueHandler)
    print(f"🐾 Revenue Dashboard: http://localhost:{PORT}/", flush=True)
    s.serve_forever()
