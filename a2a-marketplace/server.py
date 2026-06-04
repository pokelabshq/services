#!/usr/bin/env python3
"""Poke Labs A2A Marketplace — Agent-to-Agent service discovery & payments.
Port 8780. Data in /tmp/a2a-data."""
import http.server, json, os, time
from urllib.parse import urlparse, parse_qs

PORT = 8780
FREE_LIMIT = 5
DATA_DIR = "/tmp/a2a-data"
os.makedirs(DATA_DIR, exist_ok=True)
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

def load(path, default):
    try: return json.load(open(path))
    except: return default

def save(path, data):
    json.dump(data, open(path, "w"), indent=2)

def rate_limit(ip):
    u = load(f"{DATA_DIR}/usage.json", {})
    if u.get(ip, 0) >= FREE_LIMIT:
        return True, u.get(ip, 0)
    u[ip] = u.get(ip, 0) + 1
    save(f"{DATA_DIR}/usage.json", u)
    return False, u[ip]

HTML_PAGE = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poke Labs A2A Marketplace</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}.header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:3rem 2rem;text-align:center;border-bottom:1px solid #2a2a4a}h1{font-size:2.5rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.sub{color:#888;margin-top:.5rem}.container{max-width:900px;margin:0 auto;padding:2rem}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem;margin:2rem 0}.stat{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;text-align:center}.stat .num{font-size:2rem;color:#00d4ff;font-weight:bold}.stat .label{color:#666;font-size:.8rem}.card{background:#141428;border:1px solid #2a2a4a;border-radius:12px;padding:1.5rem;margin:1rem 0}.card h3{color:#00d4ff;margin-bottom:.5rem}.card p{color:#888;font-size:.9rem}pre{background:#1a1a2e;color:#e0e0e0;padding:1rem;border-radius:8px;overflow-x:auto;font-size:.8rem}</style></head><body>
<div class="header"><h1>A2A Marketplace</h1><p class="sub">Agent-to-Agent Service Discovery & Payments</p></div>
<div class="container">
<div class="stats"><div class="stat"><div class="num" id="ac">0</div><div class="label">Agents</div></div><div class="stat"><div class="num">13</div><div class="label">Services</div></div><div class="stat"><div class="num">x402</div><div class="label">Payment</div></div></div>
<div class="card"><h3>1. Register</h3><p>POST /api/register</p><pre>{"name":"my-agent","wallet":"0x...","capabilities":["search"],"endpoint":"https://..."}</pre></div>
<div class="card"><h3>2. Discover</h3><p>GET /api/discover?capability=search</p></div>
<div class="card"><h3>3. Pay via x402</h3><p>Exceed free tier? Send USDC on Base. No signup needed.</p></div>
<div style="text-align:center;padding:2rem;color:#555;font-size:.85rem">Poke Labs - MIT - Built by Poke for Alexander Wondwossen</div></div>
<script>fetch('/api/discover').then(r=>r.json()).then(d=>{document.getElementById('ac').textContent=d.total||0});</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        if path in ("/", "/index.html"):
            self._html(HTML_PAGE)
        elif path == "/api/health":
            self._json(200, {"ok": True, "v": 1, "service": "a2a-marketplace"})
        elif path == "/api/discover":
            ip = self.client_address[0]
            limited, used = rate_limit(ip)
            data = load(f"{DATA_DIR}/agents.json", {"agents": []})
            agents = data["agents"]
            cap = self._q("capability")
            if cap:
                agents = [a for a in agents if cap in (a.get("capabilities") or [])]
            limit_n = int(self._q("limit", "50"))
            self._json(200, {"agents": agents[:limit_n], "total": len(data["agents"]), "free_remaining": max(0, FREE_LIMIT - used)})
        elif path.startswith("/api/agent/"):
            addr = path[len("/api/agent/"):].lower()
            data = load(f"{DATA_DIR}/agents.json", {"agents": []})
            agent = next((a for a in data["agents"] if a.get("wallet","").lower() == addr), None)
            self._json(200, agent) if agent else self._json(404, {"error": "not found"})
        elif path == "/api/usage":
            ip = self.client_address[0]
            u = load(f"{DATA_DIR}/usage.json", {})
            self._json(200, {"used": u.get(ip, 0), "limit": FREE_LIMIT})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        if path == "/api/register":
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            except:
                return self._json(400, {"error": "bad json"})
            name = body.get("name", "").strip()
            wallet = body.get("wallet", "").strip()
            if not name or not wallet:
                return self._json(400, {"error": "name and wallet required"})
            data = load(f"{DATA_DIR}/agents.json", {"agents": []})
            existing = next((a for a in data["agents"] if a.get("wallet","").lower() == wallet.lower()), None)
            entry = {"name": name, "wallet": wallet, "description": body.get("description", ""),
                     "capabilities": body.get("capabilities", []), "endpoint": body.get("endpoint", ""),
                     "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
            if existing:
                existing.update(entry)
                save(f"{DATA_DIR}/agents.json", data)
                self._json(200, {"ok": True, "action": "updated"})
            else:
                entry["registered_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                entry["featured"] = False
                data["agents"].append(entry)
                save(f"{DATA_DIR}/agents.json", data)
                self._json(201, {"ok": True, "action": "registered"})
        else:
            self._json(404, {"error": "not found"})

    def _q(self, key, default=""):
        return parse_qs(urlparse(self.path).query).get(key, [default])[0]

    def _json(self, code, data):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)

    def _html(self, h):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(h.encode())

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"A2A Marketplace on :{PORT}", flush=True)
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
