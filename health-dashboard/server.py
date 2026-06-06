#!/usr/bin/env python3
"""Poke Labs Health Dashboard v1 — monitors all services, JSON API + HTML dashboard.
Zero deps, stdlib only."""

import http.server, json, os, socket, subprocess, time, threading
from urllib.parse import urlparse

PORT = 8799
SERVICES = [
    {"name": "Poke Labs Site",      "url": "http://localhost:8766/api/health", "port": 8766},
    {"name": "Link Preview API",    "url": "http://localhost:8765/api/health", "port": 8765},
    {"name": "Poke Bot",            "url": "http://localhost:8770/",           "port": 8770},
    {"name": "Telegram Bot",        "url": "http://localhost:8777/",           "port": 8777},
    {"name": "Skills Hub",          "url": "http://localhost:8780/",           "port": 8780},
    {"name": "Package Registry",    "url": "http://localhost:8785/",           "port": 8785},
    {"name": "Pricing API",         "url": "http://localhost:8790/",           "port": 8790},
    {"name": "Billing Engine",      "url": "http://localhost:8795/",           "port": 8795},
]

_cache = {"results": [], "ts": 0}
_lock = threading.Lock()

def port_open(port, timeout=2):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def http_ok(url, timeout=3):
    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "poke-health/1"})
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return True, resp.status
    except Exception as e:
        return False, str(e)

def scan():
    results = []
    for svc in SERVICES:
        if port_open(svc["port"]):
            ok, code = http_ok(svc["url"])
            status = "up" if ok else "degraded"
        else:
            status, code = "down", None
        results.append({"name": svc["name"], "port": svc["port"], "status": status, "http_code": code})
    return results

def sysinfo():
    info = {}
    try: info["uptime"] = subprocess.check_output(["uptime","-p"], text=True).strip()
    except: pass
    try: info["load"] = list(os.getloadavg())
    except: pass
    try:
        m = subprocess.check_output(["free","-m"], text=True).split("\n")[1].split()
        info["memory"] = {"total": int(m[1]), "used": int(m[2]), "free": int(m[6])}
    except: pass
    try:
        d = subprocess.check_output(["df","-h","/"], text=True).split("\n")[1].split()
        info["disk"] = {"total": d[1], "used": d[2], "free": d[3], "pct": d[4]}
    except: pass
    return info

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path.rstrip("/") or "/"
        if p == "/api/health":
            self._json({"ok": True, "service": "health-dashboard", "v": 1})
        elif p == "/api/status":
            with _lock:
                now = time.time()
                if now - _cache["ts"] > 30:
                    _cache["results"] = scan()
                    _cache["ts"] = now
                r = _cache["results"]
            up = sum(1 for x in r if x["status"] == "up")
            deg = sum(1 for x in r if x["status"] == "degraded")
            self._json({
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "summary": {"total": len(r), "up": up, "degraded": deg, "down": len(r)-up-deg},
                "services": r,
                "system": sysinfo(),
            })
        elif p == "/":
            self._html()
        else:
            self._json({"error": "not found"}, 404)

    def _json(self, data, code=200):
        b = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)

    def _html(self):
        h = '''<!DOCTYPE html><html><head><title>Poke Labs Health</title>
<meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0f172a;color:#e2e8f0;padding:2rem}
h1{font-size:1.5rem;margin:0 0 .25rem}
.sub{color:#94a3b8;margin-bottom:2rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;margin-bottom:2rem}
.card{background:#1e293b;border-radius:12px;padding:1.25rem;border:1px solid #334155}
.card h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.05em;color:#94a3b8;margin-bottom:.5rem}
.badge{display:inline-block;padding:.2rem .6rem;border-radius:9999px;font-size:.7rem;font-weight:600}
.up{background:#064e3b;color:#6ee7b7}.down{background:#7f1d1d;color:#fca5a5}.deg{background:#713f12;color:#fcd34d}
.port{color:#64748b;font-size:.75rem}
</style></head><body>
<h1>&#x1F43E; Poke Labs Health</h1><p class=sub>Service Dashboard</p>
<div id=svc class=grid></div>
<p style=text-align:center;color:#475569;font-size:.8rem>Refreshes every 30s &mdash; Last: <span id=ts>&mdash;</span></p>
<script>
fetch('/api/status').then(r=>r.json()).then(d=>{
document.getElementById('ts').textContent=new Date().toLocaleTimeString();
document.getElementById('svc').innerHTML=d.services.map(s=>'<div class=card><h3>'+s.name+'</h3>'+
'<span class=badge '+s.status+'>'+s.status.toUpperCase()+'</span>'+
'<p class=port>:'+s.port+(s.http_code?' &mdash; HTTP '+s.http_code:'')+'</p></div>').join('');
});
setInterval(()=>location.reload(),30000);
</script></body></html>'''
        b = h.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Health Dashboard :{PORT}")
    s.serve_forever()
