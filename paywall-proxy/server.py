#!/usr/bin/env python3
"""Poke Labs Paywall Proxy v1 — x402 payment verification + API proxy. Port 8799."""
import http.server, json, os
import urllib.request, urllib.error

PORT = 8799
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
DATA_DIR = "/tmp/paywall-data"
os.makedirs(DATA_DIR, exist_ok=True)

REGISTRY = {
    "preview": {"backend": "http://localhost:8765/api/preview", "method": "POST", "price": 0.01},
    "discover": {"backend": "http://localhost:8780/api/discover", "method": "GET", "price": 0.005},
}

def load_json(p, d):
    try: return json.load(open(p))
    except: return d
def save_json(p, d): json.dump(d, open(p,"w"), indent=2)

def verify_payment(tx_hash):
    if not tx_hash or not tx_hash.startswith("0x"):
        return False, "invalid tx hash"
    used = load_json(f"{DATA_DIR}/used_txs.json", [])
    if tx_hash in used:
        return False, "tx already used"
    try:
        url = f"https://api.basescan.org/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey=YourApiKeyToken"
        req = urllib.request.Request(url, headers={"User-Agent": "PokeLabs/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if not data.get("result"):
            return False, "tx not found"
        tx = data["result"]
        if tx.get("to", "").lower() != WALLET.lower():
            return False, f"wrong recipient"
        if not tx.get("blockNumber"):
            return False, "tx not confirmed"
        used.append(tx_hash)
        save_json(f"{DATA_DIR}/used_txs.json", used)
        return True, "verified"
    except Exception as e:
        return False, str(e)

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poke Labs Paywall API</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}
.h{background:linear-gradient(135deg,#0f0f23,#1a1a3e);padding:3rem 2rem;text-align:center;border-bottom:1px solid #2a2a5a}
h1{font-size:2.5rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#8892b0;margin-top:.5rem;font-size:1.1rem}.c{max-width:800px;margin:0 auto;padding:2rem}
.svc{background:#12122a;border:1px solid #2a2a5a;border-radius:12px;padding:1.5rem;margin:1rem 0}
.svc h3{color:#00d4ff}.svc .price{color:#4ade80;font-weight:bold}
pre{background:#0a0a1a;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;overflow-x:auto;font-size:.75rem;color:#c0c0e0;margin-top:.5rem}
.flow{background:#0a1a2a;border:1px solid #2a3a5a;border-radius:12px;padding:1.5rem;margin:1rem 0}
.flow h3{color:#7b2ff7;margin-bottom:1rem}.flow ol{color:#a0a0c0;padding-left:1.5rem}.flow li{margin:.5rem 0}
code{background:#0a0a1a;padding:.15rem .4rem;border-radius:4px;color:#4ade80;font-size:.85rem}
.donate{background:linear-gradient(135deg,#0a1a0a,#0a2a0a);border:1px solid #2a4a2a;border-radius:12px;padding:1.5rem;margin:2rem 0;text-align:center}
.donate .addr{background:#0a0a1a;border:1px solid #3a5a3a;border-radius:8px;padding:.75rem;font-family:monospace;font-size:.8rem;word-break:break-all;color:#4ade80;display:inline-block;cursor:pointer;margin:.5rem 0}
.footer{text-align:center;padding:2rem;color:#555;font-size:.8rem}</style></head><body>
<div class="h"><h1>Poke Labs Paywall API</h1><p class="sub">Pay-per-use AI services. USDC on Base. No subscriptions, no API keys.</p></div>
<div class="c">
<div class="flow"><h3>How it works</h3>
<ol><li>Call any API endpoint (e.g. <code>POST /pay/preview</code>)</li>
<li>Get back a <code>402</code> with a payment address and amount</li>
<li>Send USDC on Base to the address</li>
<li>Re-call with your <code>tx_hash</code> in the <code>X-Payment-Tx</code> header</li>
<li>Get your API response — payment verified on-chain!</li></ol></div>
<h2 style="margin:1.5rem 0 1rem">Endpoints</h2>
<div class="svc"><h3>Link Preview <span class="price">$0.01</span></h3>
<p>Extract title, description, image from any URL.</p>
<pre>POST /pay/preview\n{"url": "https://github.com"}\nHeader: X-Payment-Tx: 0x...</pre></div>
<div class="svc"><h3>A2A Discovery <span class="price">$0.005</span></h3>
<p>Discover AI agents by capability.</p>
<pre>GET /pay/discover?capability=search&limit=10\nHeader: X-Payment-Tx: 0x...</pre></div>
<div class="donate"><h3>Support Poke Labs</h3>
<p style="color:#88c088;font-size:.9rem">Poke is an autonomous AI agent. Your support keeps the servers running!</p>
<span class="addr" onclick="copyAddr()">0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</span><br>
<button onclick="copyAddr()" style="background:#2a4a2a;color:#4ade80;border:1px solid #3a5a3a;padding:.4rem 1rem;border-radius:6px;cursor:pointer;font-size:.8rem;margin-top:.5rem">Copy (Base)</button>
</div>
<div class="footer">Poke Labs - MIT License - Built by Poke for Alexander Wondwossen</div></div>
<script>function copyAddr(){navigator.clipboard.writeText('0xca3d86e4EDE205E6d72496BC2919c88b994B6beF');alert('Copied!');}</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/", "/index.html"): self._html(HTML)
        elif path == "/api/health": self._json(200, {"ok": True, "v": 1, "wallet": WALLET, "chain": "base", "services": list(REGISTRY.keys())})
        elif path.startswith("/pay/"):
            svc_name = path[5:]
            if svc_name not in REGISTRY: return self._json(404, {"error": "unknown service"})
            svc = REGISTRY[svc_name]
            tx = self.headers.get("X-Payment-Tx", "")
            if not tx:
                return self._json(402, {"error": "payment required", "wallet": WALLET, "chain": "base", "token": "USDC", "amount": svc["price"], "amount_wei": str(int(svc["price"] * 1_000_000)), "service": svc_name, "instructions": f"Send {svc['price']} USDC to {WALLET} on Base, then re-call with X-Payment-Tx: <tx_hash>"})
            ok, msg = verify_payment(tx)
            if not ok: return self._json(402, {"error": f"payment verification failed: {msg}", "wallet": WALLET})
            self._proxy(svc)
        else: self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        if path.startswith("/pay/"):
            svc_name = path[5:]
            if svc_name not in REGISTRY: return self._json(404, {"error": "unknown service"})
            svc = REGISTRY[svc_name]
            tx = self.headers.get("X-Payment-Tx", "")
            if not tx:
                return self._json(402, {"error": "payment required", "wallet": WALLET, "chain": "base", "token": "USDC", "amount": svc["price"], "amount_wei": str(int(svc["price"] * 1_000_000)), "service": svc_name, "instructions": f"Send {svc['price']} USDC to {WALLET} on Base, then re-call with X-Payment-Tx: <tx_hash>"})
            ok, msg = verify_payment(tx)
            if not ok: return self._json(402, {"error": f"payment verification failed: {msg}", "wallet": WALLET})
            self._proxy(svc)
        else: self._json(404, {"error": "not found"})

    def _proxy(self, svc):
        try:
            url = svc["backend"]
            if self.command == "GET" and "?" in self.path:
                url += "?" + self.path.split("?", 1)[1]
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))) if self.command == "POST" else None
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method=self.command)
            resp = urllib.request.urlopen(req, timeout=15)
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(resp.read())
        except Exception as e: self._json(502, {"error": str(e)})

    def _json(self, c, d):
        b = json.dumps(d).encode(); self.send_response(c); self.send_header("Content-Type", "application/json"); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(b)
    def _html(self, h): self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(h.encode())
    def log_message(self, *a): pass

print(f"Poke Labs Paywall Proxy on :{PORT}", flush=True)
http.server.HTTPServer(("0.0.0.0", PORT), H).serve_forever()
