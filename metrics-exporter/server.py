#!/usr/bin/env python3
"""Prometheus Metrics Exporter v1.0 — Exposes Poke Labs service metrics in Prometheus format.
Scrapes /api/health from all registered services, outputs /metrics endpoint. Port 8792. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, threading, html as htmlmod

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

# Cached metrics
_metrics_cache = {"data": "", "ts": 0, "lock": threading.Lock()}
CACHE_TTL = 10  # seconds

def scrape_services():
    lines = []
    lines.append("# HELP poke_service_up Service availability (1=up, 0=down)")
    lines.append("# TYPE poke_service_up gauge")
    lines.append("# HELP poke_service_response_time_ms Response time in milliseconds")
    lines.append("# TYPE poke_service_response_time_ms gauge")
    lines.append("# HELP poke_service_info Service information")
    lines.append("# TYPE poke_service_info gauge")
    
    up_count = 0
    for s in SERVICES:
        name = s["name"]
        port = s["port"]
        start = time.time()
        try:
            req = urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=2)
            elapsed = (time.time() - start) * 1000
            data = json.loads(req.read())
            status = 1
            up_count += 1
            version = data.get("v", 0)
        except:
            elapsed = (time.time() - start) * 1000
            status = 0
            version = 0
        
        lines.append(f'poke_service_up{{name="{name}",port="{port}"}} {status}')
        lines.append(f'poke_service_response_time_ms{{name="{name}"}} {elapsed:.1f}')
        lines.append(f'poke_service_info{{name="{name}",port="{port}",version="{version}"}} {status}')
    
    lines.append("# HELP poke_services_total Total number of registered services")
    lines.append("# TYPE poke_services_total gauge")
    lines.append(f"poke_services_total {len(SERVICES)}")
    lines.append("# HELP poke_services_up Total services currently up")
    lines.append("# TYPE poke_services_up gauge")
    lines.append(f"poke_services_up {up_count}")
    lines.append("# HELP poke_scrape_duration_seconds Time to scrape all services")
    lines.append("# TYPE poke_scrape_duration_seconds gauge")
    lines.append(f"poke_scrape_duration_seconds 0")
    lines.append(f"# HELP poke_exporter_info Exporter version info")
    lines.append(f"# TYPE poke_exporter_info gauge")
    lines.append(f'poke_exporter_info{{version="{VERSION}"}} 1')
    
    return "\n".join(lines) + "\n"

def get_metrics():
    with _metrics_cache["lock"]:
        now = time.time()
        if now - _metrics_cache["ts"] > CACHE_TTL:
            start = time.time()
            _metrics_cache["data"] = scrape_services()
            _metrics_cache["ts"] = now
        return _metrics_cache["data"]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/metrics":
            data = get_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data.encode())
        elif p.path == "/api/health":
            self.json({"ok": True, "v": VERSION, "port": PORT, "role": "metrics-exporter", "services": len(SERVICES)})
        elif p.path == "/":
            self.dashboard()
        else:
            self.json({"error": "Not found. Try /metrics"}, 404)

    def dashboard(self):
        lines = get_metrics().split("\n")
        metrics_html = "".join(f"<div class='m'>{htmlmod.escape(l)}</div>" for l in lines if l)
        s = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Metrics Exporter — Poke Labs</title><style>body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;display:flex;justify-content:center;padding:30px}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:30px;max-width:800px;width:100%}}h1{{color:#00ffaa}}.m{{font-family:monospace;font-size:.75em;padding:2px 8px;border-radius:3px;margin:1px 0}}.m:hover{{background:rgba(0,255,170,0.05)}}.hdr{{color:#666}}.val{{color:#00ffaa}}</style></head><body><div class="c"><h1>📊 Prometheus Metrics Exporter</h1><p style="color:#888">Port {PORT} | <a href="/metrics" style="color:#00ffaa">/metrics</a> | {len(SERVICES)} services</p><div style="max-height:500px;overflow-y:auto;background:rgba(0,0,0,0.3);border-radius:8px;padding:15px">{metrics_html}</div></div></body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

_metrics_cache["lock"] = threading.Lock()

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Prometheus Metrics Exporter v1.0 on :{PORT}");s.serve_forever()
