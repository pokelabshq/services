#!/usr/bin/env python3
"""Residual Income Tracker v1.0 — Track revenue across all Poke Labs services.
Shows projected monthly income, revenue per service, growth trends.
Pure stdlib. Zero deps."""
import http.server, json, sqlite3, time, os

PORT = 8795
DB = "/tmp/residual-income.db"

def init_db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS revenue (id INTEGER PRIMARY KEY, service TEXT, amount REAL, currency TEXT, ts TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS projections (service TEXT PRIMARY KEY, monthly REAL, annual REAL, updated TEXT)")
    # Seed with current service data
    services = [
        ("link-preview", 0.0, "USD"),
        ("color-api", 0.0, "USD"),
        ("hash-gen", 0.0, "USD"),
        ("keyword-api", 0.0, "USD"),
        ("word-analyzer", 0.0, "USD"),
        ("og-generator", 0.0, "USD"),
        ("email-validator", 0.0, "USD"),
        ("url-shortener", 0.0, "USD"),
        ("json2ts", 0.0, "USD"),
        ("timestamp-conv", 0.0, "USD"),
        ("uuid-gen", 0.0, "USD"),
        ("github-stats", 0.0, "USD"),
        ("webhook-tester", 0.0, "USD"),
        ("dashboard", 0.0, "USD"),
        ("billing", 0.0, "USD"),
    ]
    for s, a, cur in services:
        c.execute("INSERT OR IGNORE INTO revenue (service, amount, currency, ts) VALUES (?,?,?,?)", (s, a, cur, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
    c.commit(); c.close()

def get_summary():
    c = sqlite3.connect(DB)
    total = c.execute("SELECT COALESCE(SUM(amount),0) FROM revenue").fetchone()[0]
    by_service = c.execute("SELECT service, SUM(amount) as total FROM revenue GROUP BY service ORDER BY total DESC").fetchall()
    count = c.execute("SELECT COUNT(DISTINCT service) FROM revenue").fetchone()[0]
    c.close()
    return {
        "total_revenue": total,
        "services_tracked": count,
        "by_service": {s: t for s, t in by_service},
        "projected_monthly": total * 30 if total > 0 else 0,
        "projected_annual": total * 365 if total > 0 else 0,
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/":
            s = get_summary()
            self.send_html(self.page(s))
        elif p == "/api/summary":
            self.send_json(get_summary())
        elif p == "/api/services":
            c = sqlite3.connect(DB)
            rows = c.execute("SELECT service, SUM(amount), COUNT(*) FROM revenue GROUP BY service ORDER BY SUM(amount) DESC").fetchall()
            c.close()
            self.send_json([{"service": s, "revenue": r, "transactions": t} for s, r, t in rows])
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
            service = data.get("service", "unknown")
            amount = float(data.get("amount", 0))
            c = sqlite3.connect(DB)
            c.execute("INSERT INTO revenue (service, amount, currency, ts) VALUES (?,?,?,?)", (service, amount, "USD", time.strftime("%Y-%m-%dT%H:%M:%SZ")))
            c.commit(); c.close()
            self.send_json({"ok": True, "service": service, "amount": amount})
        except Exception as e:
            self.send_json({"ok": False, "error": str(e)})

    def send_html(self, h):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(h.encode())

    def send_json(self, d):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(d, indent=2).encode())

    def page(self, s):
        lines = []
        lines.append("<!DOCTYPE html><html><head><title>Residual Income Tracker</title>")
        lines.append("<style>")
        lines.append("body{font-family:system-ui,monospace;max-width:800px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}")
        lines.append("h1{color:#a78bfa}.card{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:10px 0}")
        lines.append(".num{font-size:2em;font-weight:700;color:#22c55e}.label{color:#666;font-size:0.85em}")
        lines.append("table{width:100%;border-collapse:collapse}th,td{padding:8px;text-align:left;border-bottom:1px solid #333}")
        lines.append("th{color:#a78bfa}")
        lines.append("</style></head><body>")
        lines.append("<h1>Residual Income Tracker</h1>")
        lines.append('<div class="card"><div class="num">$' + "{:.2f}".format(s['total_revenue']) + '</div><div class="label">Total Revenue</div></div>')
        lines.append('<div class="card"><div class="num">$' + "{:.2f}".format(s['projected_monthly']) + '/mo</div><div class="label">Projected Monthly (at current rate)</div></div>')
        lines.append('<div class="card"><div class="num">$' + "{:.2f}".format(s['projected_annual']) + '/yr</div><div class="label">Projected Annual</div></div>')
        lines.append('<div class="card"><h2>By Service</h2><table><tr><th>Service</th><th>Revenue</th></tr>')
        for svc, rev in s['by_service'].items():
            lines.append('<tr><td>' + svc + '</td><td>$' + "{:.2f}".format(rev) + '</td></tr>')
        lines.append('</table></div>')
        lines.append('<div class="card"><h2>API</h2>')
        lines.append('<p>POST /api/summary — Get full summary</p>')
        lines.append('<p>POST /api/services — List all services</p>')
        lines.append('<p>POST / {"service": "link-preview", "amount": 0.05} — Record revenue</p>')
        lines.append('</div>')
        lines.append('</body></html>')
        return "".join(lines)

    def log_message(self, *a): pass

if __name__ == "__main__":
    init_db()
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print("Residual Income Tracker: http://localhost:" + str(PORT) + "/", flush=True)
    s.serve_forever()
