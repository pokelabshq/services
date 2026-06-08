#!/usr/bin/env python3
"""x402 Payment Gateway v1.0 — Accept USDC payments via x402 protocol.
Processes payments, tracks balances, generates invoices. Port 8795. Zero deps."""
import http.server, json, urllib.request, urllib.parse, sqlite3, time, hashlib, html as H, os

PORT = 8795
VERSION = 1
DB = "/tmp/x402.db"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
CHAIN = "base"

db = sqlite3.connect(DB)
db.execute("""CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY, from_addr TEXT, amount_usd REAL,
    service TEXT, status TEXT DEFAULT 'pending',
    tx_hash TEXT, created_at INTEGER, confirmed_at INTEGER
)""")
db.execute("""CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY, service TEXT, amount_usd REAL,
    description TEXT, status TEXT DEFAULT 'unpaid',
    payment_id TEXT, created_at INTEGER, paid_at INTEGER
)""")
db.commit()

def create_invoice(service, amount, description):
    iid = hashlib.sha256(f"{service}{amount}{time.time()}".encode()).hexdigest()[:16]
    db.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?)",
               (iid, service, amount, description, "unpaid", None, int(time.time()), None))
    db.commit()
    return iid

def get_invoices(status=None):
    q = "SELECT * FROM invoices"
    params = []
    if status:
        q += " WHERE status = ?"
        params.append(status)
    q += " ORDER BY created_at DESC LIMIT 50"
    rows = db.execute(q, params).fetchall()
    cols = ["id","service","amount_usd","description","status","payment_id","created_at","paid_at"]
    return [dict(zip(cols, r)) for r in rows]

def get_payments():
    rows = db.execute("SELECT * FROM payments ORDER BY created_at DESC LIMIT 50").fetchall()
    cols = ["id","from_addr","amount_usd","service","status","tx_hash","created_at","confirmed_at"]
    return [dict(zip(cols, r)) for r in rows]

def get_stats():
    total_paid = db.execute("SELECT COALESCE(SUM(amount_usd),0) FROM payments WHERE status='confirmed'").fetchone()[0]
    total_pending = db.execute("SELECT COALESCE(SUM(amount_usd),0) FROM payments WHERE status='pending'").fetchone()[0]
    count_paid = db.execute("SELECT COUNT(*) FROM payments WHERE status='confirmed'").fetchone()[0]
    count_invoices = db.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    unpaid = db.execute("SELECT COUNT(*) FROM invoices WHERE status='unpaid'").fetchone()[0]
    return {"total_paid_usd": total_paid, "total_pending_usd": total_pending, "payments_confirmed": count_paid, "invoices_total": count_invoices, "invoices_unpaid": unpaid}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        if p.path == "/api/health":
            stats = get_stats()
            self.json({"ok":True,"v":VERSION,"port":PORT,"role":"x402-gateway","wallet":WALLET,"chain":CHAIN,**stats})
        elif p.path == "/api/stats":
            self.json(get_stats())
        elif p.path == "/api/invoices":
            status = qs.get("status", [None])[0]
            self.json({"invoices": get_invoices(status)})
        elif p.path == "/api/payments":
            self.json({"payments": get_payments()})
        elif p.path == "/":
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if p.path == "/api/invoice":
            iid = create_invoice(body.get("service","unknown"), body.get("amount_usd",0), body.get("description",""))
            inv = db.execute("SELECT * FROM invoices WHERE id=?", (iid,)).fetchone()
            cols = ["id","service","amount_usd","description","status","payment_id","created_at","paid_at"]
            self.json({"invoice": dict(zip(cols, inv)), "payment_address": WALLET, "chain": CHAIN}, 201)
        elif p.path == "/api/pay":
            pid = hashlib.sha256(f"{body.get('from','')}{time.time()}".encode()).hexdigest()[:16]
            db.execute("INSERT INTO payments VALUES (?,?,?,?,?,?,?,?)",
                       (pid, body.get("from",""), body.get("amount_usd",0), body.get("service",""),
                        "pending", body.get("tx_hash",""), int(time.time()), None))
            db.commit()
            self.json({"ok":True,"payment_id":pid,"status":"pending","message":"Payment submitted, awaiting confirmation"}, 201)
        elif p.path.startswith("/api/confirm/"):
            pid = p.path.split("/")[-1]
            db.execute("UPDATE payments SET status='confirmed', confirmed_at=? WHERE id=?", (int(time.time()), pid))
            db.execute("UPDATE invoices SET status='paid', paid_at=? WHERE payment_id=?", (int(time.time()), pid))
            db.commit()
            self.json({"ok":True,"message":f"Payment {pid} confirmed"})
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        stats = get_stats()
        invs = get_invoices()[:10]
        pays = get_payments()[:10]
        inv_rows = "".join(f'<tr><td>{H.escape(i["id"][:8])}</td><td>{H.escape(i["service"])}</td><td>${i["amount_usd"]}</td><td><span class="badge {"paid" if i["status"]=="paid" else "unpaid"}">{i["status"]}</span></td></tr>' for i in invs)
        pay_rows = "".join(f'<tr><td>{H.escape(p["id"][:8])}</td><td>{H.escape(p["from_addr"][:10])}...</td><td>${p["amount_usd"]}</td><td><span class="badge {"confirmed" if p["status"]=="confirmed" else "pending"}">{p["status"]}</span></td></tr>' for p in pays)
        h = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>x402 Gateway — Poke Labs</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;min-height:100vh;padding:20px}}
h1{{color:#00ffaa;text-align:center;margin:20px 0}}.wallet{{text-align:center;color:#666;font-size:.8rem;word-break:break-all;margin-bottom:30px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;max-width:1000px;margin:0 auto 30px}}
.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;text-align:center}}
.card .n{{font-size:1.8rem;font-weight:700;color:#00ffaa}}.card .l{{color:#666;font-size:.75rem;margin-top:4px}}
.tables{{display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:1000px;margin:0 auto}}
table{{width:100%;border-collapse:collapse}}th{{text-align:left;color:#666;font-size:.75rem;padding:8px;border-bottom:1px solid rgba(255,255,255,0.06)}}
td{{padding:8px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:.8rem}}
.badge{{padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:600}}
.badge.paid,.badge.confirmed{{background:rgba(0,255,170,0.1);color:#00ffaa}}
.badge.unpaid,.badge.pending{{background:rgba(255,170,0,0.1);color:#ffaa00}}
h3{{color:#e0e0e2;margin-bottom:12px;font-size:.9rem}}
</style></head><body>
<h1>💳 x402 Payment Gateway</h1>
<div class="wallet">Wallet: {WALLET} | Chain: {CHAIN} | Port {PORT}</div>
<div class="grid">
<div class="card"><div class="n">${stats["total_paid_usd"]:.2f}</div><div class="l">Total Paid</div></div>
<div class="card"><div class="n">${stats["total_pending_usd"]:.2f}</div><div class="l">Pending</div></div>
<div class="card"><div class="n">{stats["payments_confirmed"]}</div><div class="l">Payments</div></div>
<div class="card"><div class="n">{stats["invoices_unpaid"]}</div><div class="l">Unpaid Invoices</div></div>
</div>
<div class="tables">
<div><h3>Recent Invoices</h3><table><thead><tr><th>ID</th><th>Service</th><th>Amount</th><th>Status</th></tr></thead><tbody>{inv_rows}</tbody></table></div>
<div><h3>Recent Payments</h3><table><thead><tr><th>ID</th><th>From</th><th>Amount</th><th>Status</th></tr></thead><tbody>{pay_rows}</tbody></table></div>
</div></body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(h.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"x402 Gateway v1.0 on :{PORT}");s.serve_forever()
