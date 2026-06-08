#!/usr/bin/env python3
"""Health Aggregator v2.0 — Unified health dashboard for all Poke Labs services.
Checks health of all registered services, provides single dashboard view. Port 8799. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, threading, html as H

PORT = 8799
VERSION = 2

SERVICES = [
    {"name": "link-preview", "port": 8765, "desc": "URL metadata extraction"},
    {"name": "pokelabs-site", "port": 8766, "desc": "Landing page + link preview"},
    {"name": "ws-events-hub", "port": 8767, "desc": "Real-time event streaming"},
    {"name": "graphql-gateway", "port": 8768, "desc": "Unified GraphQL API"},
    {"name": "poke-bot", "port": 8770, "desc": "GitHub auto-triage bot"},
    {"name": "poke-hub", "port": 8775, "desc": "All-in-one GitHub bot"},
    {"name": "github-stats", "port": 8779, "desc": "GitHub statistics tracker"},
    {"name": "skills-hub", "port": 8780, "desc": "Skills aggregator"},
    {"name": "skills-marketplace", "port": 8781, "desc": "Skills marketplace"},
    {"name": "skills-index", "port": 8782, "desc": "Skills search index"},
    {"name": "metrics-exporter", "port": 8792, "desc": "Prometheus metrics"},
    {"name": "x402-gateway", "port": 8795, "desc": "USDC payment processing"},
]

_cache = {"data": None, "ts": 0, "lock": threading.Lock()}
CACHE_TTL = 15

def check_all():
    results = []
    for s in SERVICES:
        start = time.time()
        try:
            req = urllib.request.urlopen(f"http://localhost:{s['port']}/api/health", timeout=3)
            latency = round((time.time() - start) * 1000, 1)
            health = json.loads(req.read())
            results.append({**s, "status": "up", "latency_ms": latency, "version": health.get("v", "?")})
        except:
            latency = round((time.time() - start) * 1000, 1)
            results.append({**s, "status": "down", "latency_ms": latency, "version": "?"})
    return results

def get_results():
    with _cache["lock"]:
        now = time.time()
        if _cache["data"] is None or now - _cache["ts"] > CACHE_TTL:
            start = time.time()
            _cache["data"] = check_all()
            _cache["ts"] = now
        return _cache["data"]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        if p.path == "/api/health":
            self.json({"ok": True, "v": VERSION, "port": PORT, "services": len(SERVICES)})
        elif p.path == "/api/status":
            fmt = qs.get("format", ["json"])[0]
            results = get_results()
            up = sum(1 for r in results if r["status"] == "up")
            resp = {"ts": time.time(), "total": len(results), "up": up, "down": len(results) - up, "services": results}
            if fmt == "prometheus":
                lines = ["# HELP poke_service_up Service status", "# TYPE poke_service_up gauge"]
                for r in results:
                    lines.append(f'poke_service_up{{name="{r["name"]}"}} {1 if r["status"]=="up" else 0}')
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write("\n".join(lines).encode())
            else:
                self.json(resp)
        elif p.path == "/":
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        results = get_results()
        up = sum(1 for r in results if r["status"] == "up")
        rows = ""
        for r in results:
            color = "#00ffaa" if r["status"] == "up" else "#ff4444"
            status_icon = "🟢" if r["status"] == "up" else "🔴"
            rows += f'<tr><td>{status_icon} {H.escape(r["name"])}</td><td>{H.escape(r["desc"])}</td><td style="color:{color}">{r["status"].upper()}</td><td>{r["latency_ms"]}ms</td><td>v{r["version"]}</td></tr>'
        s = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs — Health Dashboard</title><style>body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;margin:0;padding:20px}}h1{{color:#00ffaa;text-align:center}}.summary{{display:flex;gap:20px;justify-content:center;margin:20px 0}}.stat{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:15px 25px;text-align:center}}.stat .n{{font-size:1.8rem;font-weight:700;color:#00ffaa}}.stat .l{{color:#666;font-size:.75rem}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th{{text-align:left;color:#666;font-size:.75rem;padding:8px;border-bottom:1px solid rgba(255,255,255,0.06)}}td{{padding:10px 8px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:.85rem}}tr:hover{{background:rgba(255,255,255,0.02)}}a{{color:#00ffaa;text-decoration:none}}</style></head><body><h1>🐙 Poke Labs — Health Dashboard</h2><p style="text-align:center;color:#666;font-size:.8rem">Port {PORT} | {len(SERVICES)} services | Last updated: {time.strftime("%H:%M:%S UTC", time.gmtime())} | <a href="/api/status">JSON</a> | <a href="/api/status?format=prometheus">Prometheus</a></p><div class="summary"><div class="stat"><div class="n">{len(SERVICES)}</div><div class="l">Total</div></div><div class="stat"><div class="n" style="color:#00ffaa">{up}</div><div class="l">Online</div></div><div class="stat"><div class="n" style="color:#ff4444">{len(SERVICES)-up}</div><div class="l">Offline</div></div></div><table><thead><tr><th>Service</th><th>Description</th><th>Status</th><th>Latency</th><th>Version</th></tr></thead><tbody>{rows}</tbody></table></body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    _cache["lock"] = threading.Lock()
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Health Aggregator v2.0 on :{PORT}");s.serve_forever()
