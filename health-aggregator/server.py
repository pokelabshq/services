#!/usr/bin/env python3
"""Health Aggregator v1.0 — Monitors all Poke Labs services.
Checks each service endpoint and reports overall status. Port: 8799. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, html as h, threading

PORT = 8799
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

# All known Poke Labs services
SERVICES = [
    {"name": "link-preview", "port": 8765, "url": "http://localhost:8765/api/health"},
    {"name": "pokelabs-site", "port": 8766, "url": "http://localhost:8766/api/health"},
    {"name": "poke-bot", "port": 8770, "url": "http://localhost:8770/"},
    {"name": "poke-hub", "port": 8775, "url": "http://localhost:8775/api/health"},
    {"name": "github-stats-api", "port": 8779, "url": "http://localhost:8779/api/health"},
    {"name": "skills-marketplace", "port": 8781, "url": "http://localhost:8781/api/health"},
    {"name": "registry", "port": 8785, "url": "http://localhost:8785/api/health"},
    {"name": "x402-gateway", "port": 8795, "url": "http://localhost:8795/api/health"},
]

_cache = {"ts": 0, "results": []}
CACHE_TTL = 30

def check_service(svc):
    try:
        req = urllib.request.Request(svc["url"], headers={"User-Agent": "PokeHealth/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            data = json.loads(body) if body.startswith("{") else {}
            return {"name": svc["name"], "port": svc["port"], "status": "up",
                    "response_ms": 0, "details": data}
    except urllib.error.URLError:
        return {"name": svc["name"], "port": svc["port"], "status": "down",
                "response_ms": -1, "details": {}}
    except Exception as e:
        return {"name": svc["name"], "port": svc["port"], "status": "error",
                "response_ms": -1, "details": {"error": str(e)}}

def run_checks():
    results = []
    threads = []
    lock = threading.Lock()
    def check_and_store(svc):
        r = check_service(svc)
        with lock:
            results.append(r)
    for svc in SERVICES:
        t = threading.Thread(target=check_and_store, args=(svc,))
        threads.append(t); t.start()
    for t in threads:
        t.join(timeout=10)
    return sorted(results, key=lambda x: x["port"])

def get_health():
    now = time.time()
    if not _cache["results"] or now - _cache["ts"] > CACHE_TTL:
        _cache["results"] = run_checks()
        _cache["ts"] = now
    return _cache["results"]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self.json({"ok": True, "v": 1, "port": PORT, "time": time.time()})
        elif p.path == "/api/status":
            results = get_health()
            up = sum(1 for r in results if r["status"] == "up")
            self.json({"ok": True, "services": results, "up": up,
                       "total": len(results), "pct": round(up/len(results)*100) if results else 0})
        elif p.path in ("/", "/dashboard"):
            self.dashboard()
        elif p.path == "/api/wallet":
            self.json({"wallet": WALLET, "chain": "Base (EVM)"})
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        results = get_health()
        up = sum(1 for r in results if r["status"] == "up")
        total = len(results)
        pct = round(up/total*100) if total else 0
        overall = "healthy" if pct >= 80 else ("degraded" if pct >= 50 else "down")
        color = "#00ffaa" if overall == "healthy" else ("#ffaa00" if overall == "degraded" : "#ff4444")
        rows = ""
        for r in results:
            st = r["status"]
            sc = "#00ffaa" if st == "up" else "#ff4444"
            sd = "✓ UP" if st == "up" else "✗ DOWN"
            rows += f'<tr><td>{h.escape(r["name"])}</td><td>{r["port"]}</td><td style="color:{sc}">{sd}</td><td>{h.escape(str(r["details"]))}</td></tr>'
        s = f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Health Dashboard — Poke Labs</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}.hd{{padding:40px 20px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(0,255,170,0.08) 0%,transparent 60%)}}h1{{font-size:1.8rem;color:#00ffaa}}.status{{font-size:2rem;font-weight:700;color:{color};margin:10px 0}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;max-width:700px;margin:0 auto;padding:20px}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;text-align:center}}.n{{font-size:1.8rem;font-weight:700;color:#00ffaa}}.l{{color:#666;font-size:.75rem}}table{{width:100%;max-width:900px;margin:0 auto;border-collapse:collapse;padding:0 20px 40px}}th{{text-align:left;padding:8px;color:#555;font-size:.7rem;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.05)}}td{{padding:8px;border-bottom:1px solid rgba(255,255,255,0.02);font-size:.8rem}}tr:hover td{{background:rgba(255,255,255,0.01)}}.ft{{text-align:center;padding:20px;color:#444;font-size:.7rem}}</style></head><body><div class="hd"><h1>🏥 Health Dashboard — Poke Labs</h1><div class="status">{overall.upper()}</div><p style="color:#666;font-size:.8rem">{up}/{total} services up · {pct}% healthy · Updated {time.strftime("%H:%M:%S UTC", time.gmtime())}</p></div><div class="g"><div class="c"><div class="n">{total}</div><div class="l">Services</div></div><div class="c"><div class="n" style="color:#00ffaa">{up}</div><div class="l">Up</div></div><div class="c"><div class="n" style="color:#ff4444">{total-up}</div><div class="l">Down</div></div><div class="c"><div class="n">{pct}%</div><div class="l">Healthy</div></div></div><table><thead><tr><th>Service</th><th>Port</th><th>Status</th><th>Details</th></tr></thead><tbody>{rows}</tbody></table><div class="ft">🐾 Poke Labs Health Aggregator v1.0 · MIT · Port {PORT} · Wallet: {WALLET[:10]}...</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Health Aggregator v1.0 on :{PORT}");s.serve_forever()
