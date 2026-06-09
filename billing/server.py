#!/usr/bin/env python3
"""Poke Labs Billing Service — x402 payment gateway
Accepts USDC payments on Base chain. Any service can integrate.
Port: 8795"""

import http.server, json, time, hashlib, hmac, os, urllib.request, urllib.error, secrets, sqlite3, threading

PORT = 8795
VERSION = "1.0.0"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
DB_PATH = "/tmp/billing.db"
# Price table: service -> USDC amount (in cents)
PRICES = {
    "link-preview": 1,      # 1 cent per call after free tier
    "url-shortener": 1,
    "email": 5,
    "doc-gen": 10,
    "readme-gen": 25,
    "dashboard": 0,         # free
    "status-page": 0,
}

# ── Database ──────────────────────────────────────────────
db_lock = threading.Lock()

def db_init():
    with db_lock:
        c = sqlite3.connect(DB_PATH)
        c.execute("""CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            service TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            payer TEXT,
            tx_hash TEXT,
            status TEXT DEFAULT 'pending',
            created_at REAL,
            settled_at REAL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS usage (
            ip TEXT,
            service TEXT,
            used INTEGER DEFAULT 0,
            PRIMARY KEY (ip, service)
        )""")
        c.commit()
        c.close()

def db_insert_payment(pid, service, amount, payer=None):
    with db_lock:
        c = sqlite3.connect(DB_PATH)
        c.execute("INSERT INTO payments(id,service,amount_cents,payer,status,created_at) VALUES(?,?,?,?,?,?)",
                  (pid, service, amount, payer, "pending", time.time()))
        c.commit(); c.close()

def db_settle(pid, tx_hash):
    with db_lock:
        c = sqlite3.connect(DB_PATH)
        c.execute("UPDATE payments SET status='settled',tx_hash=?,settled_at=? WHERE id=?", (tx_hash, time.time(), pid))
        c.commit(); c.close()

def db_get_usage(ip, service):
    with db_lock:
        c = sqlite3.connect(DB_PATH)
        r = c.execute("SELECT used FROM usage WHERE ip=? AND service=?", (ip, service)).fetchone()
        c.close()
        return r[0] if r else 0

def db_inc_usage(ip, service):
    with db_lock:
        c = sqlite3.connect(DB_PATH)
        c.execute("INSERT INTO usage(ip,service,used) VALUES(?,?,1) ON CONFLICT(ip,service) DO UPDATE SET used=used+1", (ip, service))
        c.commit(); c.close()

def db_stats():
    with db_lock:
        c = sqlite3.connect(DB_PATH)
        total = c.execute("SELECT COUNT(*), COALESCE(SUM(amount_cents),0) FROM payments WHERE status='settled'").fetchone()
        pending = c.execute("SELECT COUNT(*) FROM payments WHERE status='pending'").fetchone()[0]
        c.close()
        return {"total_payments": total[0], "total_revenue_cents": total[1], "pending": pending}

# ── Payment request generation ────────────────────────────
def create_payment_request(service, amount_cents):
    pid = secrets.token_hex(16)
    db_insert_payment(pid, service, amount_cents)
    return {
        "pid": pid,
        "version": "x402/v1",
        "chain": "base",
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        "to": WALLET,
        "amount_cents": amount_cents,
        "amount_usdc": f"{amount_cents / 100:.2f}",
        "service": service,
        "settlement_url": f"http://localhost:{PORT}/api/settle",
        "expires_in": 300,
    }

# ── HTTP Handler ──────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        path = self.path.split("?")[0]
        ip = self.client_address[0]

        if path == "/":
            self.send_html()
        elif path == "/api/health":
            self.send_json({"ok": True, "v": VERSION, "port": PORT, "wallet": WALLET})
        elif path == "/api/prices":
            self.send_json({"prices": PRICES, "wallet": WALLET, "chain": "base"})
        elif path == "/api/stats":
            self.send_json(db_stats())
        elif path.startswith("/api/check/"):
            svc = path.split("/api/check/")[1]
            used = db_get_usage(ip, svc)
            free_limit = 3
            price = PRICES.get(svc, 0)
            remaining = max(0, free_limit - used)
            self.send_json({"service": svc, "used": used, "free_limit": free_limit, "remaining": remaining, "price_cents": price, "exhausted": remaining <= 0 and price > 0})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        ip = self.client_address[0]
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")

        if path == "/api/pay":
            svc = body.get("service", "")
            price = PRICES.get(svc, 0)
            if price <= 0:
                self.send_json({"error": "unknown service or free", "service": svc}, 400)
                return
            used = db_get_usage(ip, svc)
            free_limit = 3
            if used < free_limit:
                db_inc_usage(ip, svc)
                self.send_json({"ok": True, "free": True, "remaining": free_limit - used - 1})
                return
            req = create_payment_request(svc, price)
            self.send_json({"ok": False, "free": False, "payment": req, "http_status": 402})

        elif path == "/api/settle":
            pid = body.get("pid", "")
            tx = body.get("tx_hash", "")
            if pid and tx:
                db_settle(pid, tx)
                self.send_json({"ok": True, "pid": pid, "tx_hash": tx})
            else:
                self.send_json({"error": "missing pid or tx_hash"}, 400)

        elif path == "/api/use":
            svc = body.get("service", "")
            used = db_get_usage(ip, svc)
            free_limit = 3
            price = PRICES.get(svc, 0)
            if used < free_limit:
                db_inc_usage(ip, svc)
                self.send_json({"ok": True, "free": True, "remaining": free_limit - used - 1})
            elif price > 0:
                req = create_payment_request(svc, price)
                self.send_json({"ok": False, "free": False, "payment": req}, 402)
            else:
                self.send_json({"ok": True, "free": True, "remaining": "unlimited"})
        else:
            self.send_json({"error": "not found"}, 404)

    def send_json(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def send_html(self):
        html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Poke Labs Billing</title>
<style>
:root{{--bg:#0d1117;--srf:#161b22;--brd:#30363d;--txt:#c9d1d9;--mut:#8b949e;--acc:#58a6ff;--grn:#3fb950;--red:#f85149;--ylw:#d29922}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.card{{background:var(--srf);border:1px solid var(--brd);border-radius:12px;padding:2rem;max-width:500px;width:90%;text-align:center}}
h1{{font-size:1.5rem;margin-bottom:.5rem}} h1 s{{color:var(--acc)}}
.sub{{color:var(--mut);margin-bottom:1.5rem;font-size:.9rem}}
.prices{{text-align:left;margin:1rem 0}}
.prices h3{{margin-bottom:.5rem;font-size:1rem}}
.row{{display:flex;justify-content:space-between;padding:.4rem 0;border-bottom:1px solid var(--brd);font-size:.85rem}}
.row:last-child{{border-bottom:none}}
.svc{{font-weight:600}} .price{{color:var(--ylw);font-family:monospace}}
.free{{color:var(--grn)}}
.wallet{{background:rgba(88,166,255,.1);border:1px solid var(--brd);border-radius:8px;padding:.75rem;font-family:monospace;font-size:.75rem;word-break:break-all;margin-top:1rem}}
.wallet label{{color:var(--mut);font-size:.7rem;display:block;margin-bottom:.25rem}}
.chain{{display:inline-block;background:rgba(63,185,80,.15);color:var(--grn);padding:.2rem .6rem;border-radius:10px;font-size:.75rem;margin-top:.5rem}}
footer{{margin-top:1rem;color:var(--mut);font-size:.75rem}}
</style></head><body>
<div class="card">
<h1>💳 <s>Poke Labs Billing</s></h1>
<p class="sub">x402 payment gateway · USDC on Base</p>
<span class="chain">🔗 Base Chain</span>
<div class="prices">
<h3>Service Pricing</h3>
{"".join(f'<div class="row"><span class="svc">{k}</span><span class="price">{"FREE" if v==0 else f"${v/100:.2f}/call"}</span></div>' for k,v in PRICES.items())}
<p style="color:var(--mut);font-size:.75rem;margin-top:.5rem">3 free calls per service per IP per day</p>
</div>
<div class="wallet"><label>Payment Address (Base)</label>{WALLET}</div>
<footer>Poke Labs v{VERSION} · MIT License</footer>
</div></body></html>'''
        b = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

if __name__ == "__main__":
    db_init()
    srv = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Labs Billing v{VERSION} running on :{PORT}", flush=True)
    print(f"Wallet: {WALLET}")
    srv.serve_forever()
