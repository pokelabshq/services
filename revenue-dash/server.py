#!/usr/bin/env python3
"""Revenue Dashboard v2.0 — Track x402 earnings and service usage across the fleet."""
import http.server, json, urllib.request, urllib.parse, os, sqlite3, hashlib, time
from datetime import datetime, timedelta

PORT = int(os.environ.get("PORT", 8795))
DB = "/tmp/revenue.db"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
FREE_LIMIT = 3

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS payments
        (id TEXT PRIMARY KEY, service TEXT, payer TEXT, amount INTEGER, currency TEXT, ts INTEGER)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS usage
        (ip TEXT, service TEXT, day TEXT, count INTEGER, PRIMARY KEY(ip, service, day))""")
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB)
    # Total revenue
    row = conn.execute("SELECT COALESCE(SUM(amount),0), COUNT(*) FROM payments").fetchone()
    total_revenue, total_payments = row[0], row[1]
    # Today's usage
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage_rows = conn.execute("SELECT service, SUM(count) FROM usage WHERE day=? GROUP BY service ORDER BY SUM(count) DESC", (today,)).fetchall()
    # Top payers
    payers = conn.execute("SELECT payer, SUM(amount), COUNT(*) FROM payments GROUP BY payer ORDER BY SUM(amount) DESC LIMIT 10").fetchall()
    # Recent payments
    recent = conn.execute("SELECT service, payer, amount, ts FROM payments ORDER BY ts DESC LIMIT 20").fetchall()
    # Unique IPs today
    unique_ips = conn.execute("SELECT COUNT(DISTINCT ip) FROM usage WHERE day=?", (today,)).fetchone()[0]
    conn.close()
    return {
        "total_revenue": total_revenue, "total_payments": total_payments,
        "usage_today": {s: c for s, c in usage_rows},
        "top_payers": [{"payer": p, "total": a, "payments": c} for p, a, c in payers],
        "recent": [{"service": s, "payer": p, "amount": a, "ts": t} for s, p, a, t in recent],
        "unique_ips_today": unique_ips, "wallet": WALLET
    }

def check_usage(ip, service):
    conn = sqlite3.connect(DB)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    row = conn.execute("SELECT count FROM usage WHERE ip=? AND service=? AND day=?", (ip, service, today)).fetchone()
    count = row[0] if row else 0
    if count < FREE_LIMIT:
        conn.execute("INSERT OR REPLACE INTO usage VALUES(?,?,?,?)", (ip, service, today, count+1))
        conn.commit()
        conn.close()
        return True, FREE_LIMIT - count - 1
    conn.close()
    return False, 0

HTML_DASH = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🫧 Revenue Dashboard — Poke Labs</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0a0a14;color:#c8c8d8;min-height:100vh}
.header{background:linear-gradient(135deg,rgba(0,212,255,0.08),rgba(123,47,247,0.08));padding:40px 20px;text-align:center;border-bottom:1px solid #30363d}
.header h1{font-size:2rem;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{color:#8b949e;margin-top:8px}
.wrap{max-width:960px;margin:0 auto;padding:32px 20px}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}
.metric{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;text-align:center}
.metric .val{font-size:2rem;font-weight:700;color:#00d4ff}
.metric .lbl{color:#8b949e;font-size:.85rem;margin-top:4px}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px;margin-bottom:24px}
.card h2{font-size:1.2rem;color:#00d4ff;margin-bottom:16px}
table{width:100%;border-collapse:collapse}th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #21262d}
th{color:#8b949e;font-size:.8rem;text-transform:uppercase}td{font-family:monospace;font-size:.9rem}
.badge{background:#238636;color:#fff;padding:2px 8px;border-radius:12px;font-size:.75rem;font-family:system-ui}
.bill{background:linear-gradient(135deg,rgba(0,212,255,0.05),rgba(123,47,247,0.05));border:1px solid #30363d;border-radius:12px;padding:24px}
.bill code{background:#0a0a14;padding:4px 10px;border-radius:4px;font-size:.85rem;color:#00d4ff;word-break:break-all}
a{color:#00d4ff}footer{text-align:center;padding:32px;color:#6e7681;font-size:.85rem}
</style></head><body>
<div class="header"><h1>💰 Revenue Dashboard</h1><p>Poke Labs · Real-time x402 earnings tracker</p></div>
<div class="wrap">
<div class="metrics">
  <div class="metric"><div class="val">${total_revenue}</div><div class="lbl">Total Revenue (USDC cents)</div></div>
  <div class="metric"><div class="val">{total_payments}</div><div class="lbl">Payments Received</div></div>
  <div class="metric"><div class="val">{unique_ips}</div><div class="lbl">Unique Visitors Today</div></div>
  <div class="metric"><div class="val">{services_up}</div><div class="lbl">Monetized Services</div></div>
</div>
<div class="card"><h2>📊 Usage Today</h2><table><tr><th>Service</th><th>Requests</th></tr>{usage_rows}</table></div>
<div class="card"><h2>🏆 Top Supporters</h2><table><tr><th>Address</th><th>Total</th><th>Payments</th></tr>{payer_rows}</table></div>
<div class="card"><h2>💸 Recent Payments</h2><table><tr><th>Service</th><th>Payer</th><th>Amount</th><th>Time</th></tr>{recent_rows}</table></div>
<div class="bill"><h2 style="margin-bottom:12px">Fund Poke Labs</h2><code>{wallet}</code><p style="margin-top:12px;color:#8b949e;font-size:.9rem">Send USDC on Base to fund the fleet.</p></div>
</div>
<footer>🫧 Poke Labs · revenue-dash v2.0 · {date}</footer>
</body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        init_db()
        p = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(p.query)
        if p.path == "/":
            stats = get_stats()
            usage_rows = "".join(f"<tr><td>{s}</td><td>{c}</td></tr>" for s, c in stats["usage_today"].items()) or '<tr><td colspan="2" style="color:#6e7681">No usage yet</td></tr>'
            payer_rows = "".join(f'<tr><td>{p["payer"][:10]}...</td><td>${p["total"]}</td><td>{p["payments"]}</td></tr>' for p in stats["top_payers"]) or '<tr><td colspan="3" style="color:#6e7681">No payments yet</td></tr>'
            recent_rows = "".join(f'<tr><td>{r["service"]}</td><td>{r["payer"][:8]}...</td><td>${r["amount"]}</td><td>{datetime.fromtimestamp(r["ts"]).strftime("%H:%M")}</td></tr>' for r in stats["recent"]) or '<tr><td colspan="4" style="color:#6e7681">No payments yet</td></tr>'
            html = HTML_DASH.format(
                total_revenue=stats["total_revenue"], total_payments=stats["total_payments"],
                unique_ips=stats["unique_ips_today"], services_up=3,
                usage_rows=usage_rows, payer_rows=payer_rows, recent_rows=recent_rows,
                wallet=stats["wallet"], date=datetime.utcnow().strftime("%Y-%m-%d")
            )
            self.send_html(html)
        elif p.path == "/api/health":
            self.send_json({"ok": True, "v": 2, "port": PORT})
        elif p.path == "/api/stats":
            self.send_json(get_stats())
        elif p.path == "/api/x402":
            # Simulate an x402 payment requirement
            ip = self.client_address[0]
            allowed, remaining = check_usage(ip, "revenue-dash")
            if not allowed:
                self.send_json({"paymentRequired": True, "wallet": WALLET, "amount": 50, "asset": "USDC", "network": "Base"}, 402)
            else:
                self.send_json({"ok": True, "remaining": remaining})
        else:
            self.send_json({"error": "not found"}, 404)

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
    init_db()
    print(f"Revenue Dashboard v2.0 on port {PORT}")
    http.server.HTTPServer(("", PORT), H).serve_forever()
