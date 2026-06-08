#!/usr/bin/env python3
"""Poke Labs Uptime Monitor — Checks all service endpoints and reports status."""
import http.server, json, urllib.request, urllib.error, threading, time, datetime, os, re

PORT = 8776
SERVICES_DIR = "/home/alx/services"
CHECK_INTERVAL = 60  # seconds

statuses = {}  # name -> {status, ms, last_check, uptime_pct, total_checks, fails}
lock = threading.Lock()

def discover_endpoints():
    endpoints = []
    if not os.path.isdir(SERVICES_DIR):
        return endpoints
    for name in sorted(os.listdir(SERVICES_DIR)):
        skill = os.path.join(SERVICES_DIR, name, "SKILL.md")
        if not os.path.exists(skill):
            continue
        port = 0
        content = open(skill).read()
        pm = re.search(r'[Pp]ort[:\s]+(\d{4,5})', content)
        if pm:
            port = int(pm.group(1))
        if port:
            endpoints.append({"name": name, "port": port, "url": f"http://localhost:{port}/api/health"})
    return endpoints

def check_endpoint(ep):
    t = time.time()
    try:
        r = urllib.request.urlopen(ep["url"], timeout=5)
        ms = round((time.time() - t) * 1000)
        return r.status, ms, None
    except urllib.error.HTTPError as e:
        ms = round((time.time() - t) * 1000)
        return e.code, ms, str(e)
    except Exception as e:
        ms = round((time.time() - t) * 1000)
        return 0, ms, str(e)[:100]

def monitor_loop():
    while True:
        for ep in discover_endpoints():
            status, ms, err = check_endpoint(ep)
            with lock:
                s = statuses.get(ep["name"], {"total": 0, "fails": 0, "history": []})
                s["total"] = s.get("total", 0) + 1
                if status >= 400 or status == 0:
                    s["fails"] = s.get("fails", 0) + 1
                s["status"] = status
                s["ms"] = ms
                s["error"] = err
                s["last_check"] = datetime.datetime.now().isoformat()
                s["uptime_pct"] = round((s["total"] - s["fails"]) / s["total"] * 100, 1) if s["total"] > 0 else 100
                s.setdefault("history", [])
                s["history"].append({"ts": s["last_check"], "status": status, "ms": ms})
                if len(s["history"]) > 100:
                    s["history"] = s["history"][-100:]
                statuses[ep["name"]] = s
        time.sleep(CHECK_INTERVAL)

PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Poke Labs Uptime</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0a0a0f;color:#e0e0e0;max-width:900px;margin:0 auto;padding:2rem}
h1{color:#00d4ff;margin-bottom:1rem}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem}
.card{background:#111;border:1px solid #222;border-radius:10px;padding:1rem}
.card h3{margin-bottom:.5rem}.card .status{font-size:.8rem;padding:.2rem .5rem;border-radius:4px;display:inline-block}
.up{background:#00ff8822;color:#00ff88}.down{background:#ff444422;color:#ff4444}.warn{background:#ffaa0022;color:#ffaa00}
.card .meta{color:#666;font-size:.75rem;margin-top:.5rem}</style></head><body>
<h1>🐾 Uptime Monitor</h1><div class="grid" id="g"></div>
<script>
async function load(){
  const d=await(await fetch('/api/status')).json();
  document.getElementById('g').innerHTML=Object.entries(d).map(([name,s])=>{
    const cls=s.status>=200&&s.status<300?'up':(s.status===0?'down':'warn');
    const label=s.status>=200&&s.status<300?'UP':(s.status===0?'DOWN':'WARN');
    return `<div class="card"><h3>${name}</h3><span class="status ${cls}">${label} ${s.status||'timeout'}</span><span style="color:#555;font-size:.75rem;margin-left:.5rem">${s.ms}ms</span><div class="meta">Uptime: ${s.uptime_pct}% · Checks: ${s.total} · Last: ${s.last_check?.substring(11,19)||'never'}</div></div>`;
  }).join('');
}
load();setInterval(load,15000);</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=self.path.split("?")[0]
        if p in ("/",""):
            self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(PAGE.encode())
        elif p=="/api/status":
            with lock: s = json.loads(json.dumps(statuses))
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps(s,indent=2).encode())
        elif p=="/api/health":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps({"ok":True,"v":1}).encode())
        else:self.send_response(404);self.end_headers()
    def log_message(self,*a):pass

if __name__=="__main__":
    threading.Thread(target=monitor_loop,daemon=True).start()
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Uptime Monitor on port {PORT}");s.serve_forever()
