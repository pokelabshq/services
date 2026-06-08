#!/usr/bin/env python3
"""x402 Gateway v1.0 — Accept USDC payments via x402 protocol.
Provides /api/pay endpoint for paid API access. Port: 8795. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, html as h, hashlib, os

PORT = 8795
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
CHAIN = "base"

# Payment tracking
PAYMENTS_FILE = "/tmp/x402-payments.json"
LOCK = None  ###################

def load_payments():
    try:
        with open(PAYMENTS_FILE) as f:
            return json.load(f)
    except:
        return {"payments": [], "total_usdc": 0, "total_count": 0}

def save_payments(data):
    with open(PAYMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self.json({"ok": True, "v": 1, "port": PORT, "wallet": WALLET, "chain": CHAIN})
        elif p.path == "/api/pay":
            # Return x402 payment request (402 = payment required)
            self.json({
                "error": "Payment required",
                "amount": "1.00",
                "currency": "USDC",
                "wallet": WALLET,
                "chain": CHAIN,
                "protocol": "x402",
                "message": f"Send 1.00 USDC to {WALLET} on Base chain"
            }, 402)
        elif p.path == "/api/payments":
            self.json(load_payments())
        elif p.path in ("/", "/dashboard"):
            self.dashboard()
        elif p.path == "/api/wallet":
            self.json({"wallet": WALLET, "chain": CHAIN, "protocol": "x402"})
        else:
            self.json({"error": "Not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            data = json.loads(body)
        except:
            data = {}

        if p.path == "/api/pay":
            # Simulate payment processing
            amount = data.get("amount", "1.00")
            tx_hash = data.get("tx_hash", "0x" + hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:64])
            payment = {"tx": tx_hash, "amount": amount, "time": time.time(), "status": "confirmed"}
            payments = load_payments()
            payments["payments"].append(payment)
            payments["total_count"] += 1
            try:
                payments["total_usdc"] += float(amount)
            except:
                pass
            save_payments(payment)
            self.json({"ok": True, "payment": payment, "access": "granted"})
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        payments = load_payments()
        total = payments.get("total_usdc", 0)
        count = payments.get("total_count", 0)
        s = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>x402 Gateway — Poke Labs</title><style>body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:40px;max-width:500px;width:90%;text-align:center}}h1{{color:#00ffaa;margin:0 0 8px}}.w{{font-family:monospace;font-size:.75em;color:#666;word-break:break-all;background:rgba(255,255,255,0.03);padding:10px;border-radius:6px;margin:15px 0}}.s{{display:flex;gap:15px;justify-content:center;margin:20px 0}}.st{{text-align:center}}.n{{font-size:2rem;font-weight:700;color:#00ffaa}}.l{{color:#666;font-size:.7rem}}.g{{background:#00ffaa;color:#0a0a1a;border:none;padding:12px 24px;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;margin-top:15px}}</style></head><body><div class="c"><h1>💳 x402 Gateway</h1><p style="color:#888">USDC Payment Processing for Poke Labs APIs</p><div class="w">Wallet: {WALLET}</div><div class="w">Chain: {CHAIN.upper()}</div><div class="s"><div class="st"><div class="n">${total:.2f}</div><div class="l">Total USDC</div></div><div class="st"><div class="n">{count}</div><div class="l">Payments</div></div></div><button class="g" onclick="pay()">Pay 1.00 USDC</button><p id="result" style="font-size:.8rem;margin-top:15px"></p></div><script>async function pay(){{const r=await fetch("/api/pay",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{amount:"1.00",tx_hash:"0x"+Array.from({{length:64}},()=>Math.floor(Math.random()*16).toString(16)).join("")}})}});const d=await r.json();document.getElementById("result").textContent=d.ok?"✅ Access granted!":"❌ "+d.error}}</script></body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"x402 Gateway v1.0 on :{PORT}");s.serve_forever()
