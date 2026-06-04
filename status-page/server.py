#!/usr/bin/env python3
import http.client, json, os, ssl, sys, time
from datetime import datetime, timezone
from urllib.parse import urlparse

SERVICES = [
    {"name": "pokelabs.org", "url": "https://pokelabs.org", "desc": "Main website"},
    {"name": "ai-council", "url": "https://ai-council.pokelabs.com", "desc": "AI Council"},
    {"name": "link-preview", "url": "http://localhost:8765/api/health", "desc": "Link Preview API", "internal": True},
    {"name": "uptime-monitor", "url": "http://localhost:8766/api/health", "desc": "Uptime Monitor", "internal": True},
]
PORT = int(os.environ.get("STATUS_PORT", 8767))
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "status_history.json")
os.makedirs(DATA_DIR, exist_ok=True)

def check_one(svc):
    url = svc["url"]
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"
    host = parsed.hostname
    port = parsed.port or (443 if is_https else 80)
    path = parsed.path or "/"
    start = time.time()
    try:
        if is_https:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection(host, port, timeout=10, context=ctx)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=10)
        conn.request("GET", path, headers={"User-Agent": "PokeLabs-Status/1.0"})
        resp = conn.getresponse()
        status = resp.status
        body = resp.read(512).decode("utf-8", errors="ignore")
        conn.close()
        ms = round((time.time() - start) * 1000)
        is_up = 200 <= status < 500
        if svc.get("internal") and "health" in path:
            try:
                j = json.loads(body)
                is_up = j.get("status") == "ok"
            except: pass
        return {"name": svc["name"], "status": status, "ms": ms, "up": is_up, "desc": svc["desc"]}
    except Exception as e:
        return {"name": svc["name"], "status": None, "ms": round((time.time()-start)*1000), "up": False, "desc": svc["desc"], "error": str(e)}

def run_checks():
    results = [check_one(s) for s in SERVICES]
    public = [r for r in results if not any(s.get("internal") for s in SERVICES if s["name"] == r["name"])]
    if all(r["up"] for r in public): overall = "operational"
    elif any(r["up"] for r in public): overall = "degraded"
    else: overall = "down"
    report = {"overall": overall, "time": datetime.now(timezone.utc).isoformat(), "services": results}
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f: history = json.load(f)
        except: pass
    history.append(report)
    with open(HISTORY_FILE, "w") as f: json.dump(history[-100:], f, indent=2)
    return report

def run_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/api/status", "/api/check"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(run_checks(), indent=2).encode())
            elif self.path == "/api/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            elif self.path == "/":
                r = run_checks()
                colors = {"operational": "#22c55e", "degraded": "#f59e0b", "down": "#ef4444"}
                c = colors.get(r["overall"], "#6b7280")
                rows = ""
                for s in r["services"]:
                    sc = "#22c55e" if s["up"] else "#ef4444"
                    st = s["status"] if s["status"] else "ERR"
                    rows += f'<tr><td>{s["name"]}</td><td>{s["desc"]}</td><td style="color:{sc}">{st}</td><td>{s["ms"]}ms</td></tr>'
                html = f'<!DOCTYPE html><html><head><title>Poke Labs Status</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:system-ui,sans-serif;max-width:800px;margin:40px auto;padding:0 20px}h1{{color:#111}}.status{{display:inline-block;padding:4px 12px;border-radius:20px;color:#fff;background:{c};font-weight:600}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{text-align:left;padding:8px 12px;border-bottom:1px solid #eee}}th{{color:#666;font-size:12px;text-transform:uppercase}}</style></head><body><h1>Poke Labs Status</h1><span class="status">{r["overall"]}</span><p style="color:#999;font-size:12px">Updated: {r["time"]}</p><table><tr><th>Service</th><th>Description</th><th>Status</th><th>Latency</th></tr>{rows}</table></body></html>'
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
            else:
                self.send_response(404); self.end_headers()
        def log_message(self, *a): pass
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "check":
        for s in SERVICES:
            r = check_one(s)
            print(f"{'OK' if r['up'] else 'FAIL'} | {r['name']} | {r.get('status','ERR')} | {r['ms']}ms")
    elif mode == "json":
        print(json.dumps(run_checks(), indent=2))
    elif mode == "server":
        run_server()
