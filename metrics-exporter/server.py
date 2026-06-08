#!/usr/bin/env python3
"""Prometheus Metrics Exporter v1.0 — Scrapes all Poke Labs services, exposes /metrics. Port 8792. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, threading

PORT = 8792
VERSION = 1

SERVICES = [
    {"name": "link-preview", "port": 8765},
    {"name": "pokelabs-site", "port": 8766},
    {"name": "ws-events-hub", "port": 8767},
    {"name": "graphql-gateway", "port": 8768},
    {"name": "poke-bot", "port": 8770},
    {"name": "poke-hub", "port": 8775},
    {"name": "github-stats", "port": 8779},
    {"name": "skills-hub", "port": 8780},
    {"name": "skills-marketplace", "port": 8781},
    {"name": "skills-index", "port": 8782},
    {"name": "x402-gateway", "port": 8795},
]

_cache = {"data": "", "ts": 0}
_lock = threading.Lock()
CACHE_TTL = 10

def scrape():
    lines = ["# HELP poke_service_up Service availability (1=up, 0=down)", "# TYPE poke_service_up gauge",
             "# HELP poke_service_response_time_ms Response time in ms", "# TYPE poke_service_response_time_ms gauge",
             "# HELP poke_service_info Service info", "# TYPE poke_service_info gauge"]
    up_count = 0
    for s in SERVICES:
        start = time.time()
        try:
            req = urllib.request.urlopen(f"http://localhost:{s['port']}/api/health", timeout=2)
            ms = (time.time() - start) * 1000
            data = json.loads(req.read())
            st = 1; up_count += 1; ver = data.get("v", 0)
        except:
            ms = (time.time() - start) * 1000; st = 0; ver = 0
        lines.append(f'poke_service_up{{name="{s["name"]}",port="{s["port"]}"}} {st}')
        lines.append(f'poke_service_response_time_ms{{name="{s["name"]}"}} {ms:.1f}')
        lines.append(f'poke_service_info{{name="{s["name"]}",version="{ver}"}} {st}')
    lines += ["# HELP poke_services_total Total registered", "# TYPE poke_services_total gauge",
              f"poke_services_total {len(SERVICES)}",
              "# HELP poke_services_up_count Total up", "# TYPE poke_services_up_count gauge",
              f"poke_services_up_count {up_count}",
              f'poke_exporter_info{{version="{VERSION}"}} 1']
    return "\n".join(lines) + "\n"

def get_metrics():
    with _lock:
        now = time.time()
        if now - _cache["ts"] > CACHE_TTL:
            _cache["data"] = scrape(); _cache["ts"] = now
        return _cache["data"]

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/metrics":
            d = get_metrics()
            self.send_response(200); self.send_header("Content-Type","text/plain; version=0.0.4")
            self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d.encode())
        elif p.path == "/api/health":
            self.json({"ok":True,"v":VERSION,"port":PORT,"role":"metrics-exporter","services":len(SERVICES)})
        elif p.path == "/":
            lines = get_metrics().split("\n")
            rows = "".join(f'<div style="font-family:monospace;font-size:.75em;padding:2px 8px">{l}</div>' for l in lines if l)
            h = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Metrics — Poke Labs</title><style>body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;padding:30px}}h1{{color:#00ffaa}}</style></head><body><h1>📊 Prometheus Metrics Exporter</h1><p style="color:#888">Port {PORT} | <a href="/metrics" style="color:#00ffaa">/metrics</a> | {len(SERVICES)} services</p><div style="background:rgba(0,0,0,0.3);border-radius:8px;padding:15px;max-height:500px;overflow-y:auto">{rows}</div></body></html>'''
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(h.encode())
        else:
            self.json({"error":"Not found. Try /metrics"},404)
    def json(self,d,code=200):
        body=json.dumps(d,default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),H)
    print(f"Prometheus Metrics Exporter v1.0 on :{PORT}");s.serve_forever()
