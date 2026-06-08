#!/usr/bin/env python3
"""Poke Labs Gateway — Single entry point that routes to all services."""
import http.server, json, urllib.request, urllib.error, os, re, datetime, threading, time

PORT = 8700
SERVICES_DIR = "/home/alx/services"

def discover():
    svcs = []
    if not os.path.isdir(SERVICES_DIR): return svcs
    for name in sorted(os.listdir(SERVICES_DIR)):
        skill = os.path.join(SERVICES_DIR, name, "SKILL.md")
        if not os.path.exists(skill): continue
        port = 0
        content = open(skill).read()
        pm = re.search(r'[Pp]ort[:\s]+(\d{4,5})', content)
        if pm: port = int(pm.group(1))
        if not port: continue
        svcs.append({"name": name, "port": port, "path": f"/{name}"})
    return svcs

def check(svc):
    try:
        t = time.time()
        r = urllib.request.urlopen(f"http://localhost:{svc['port']}/api/health", timeout=3)
        return r.status, round((time.time()-t)*1000)
    except: return 0, 0

PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Poke Labs Gateway</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0a0a0f;color:#e0e0e0;max-width:900px;margin:0 auto;padding:2rem}
h1{color:#00d4ff;margin-bottom:.5rem}p.sub{color:#666;margin-bottom:2rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}
.card{background:#111;border:1px solid #222;border-radius:10px;padding:1.2rem;text-decoration:none;color:inherit;display:block;transition:border-color .2s}
.card:hover{border-color:#00d4ff}
.card h3{margin-bottom:.3rem;color:#00d4ff}
.card .port{color:#555;font-size:.8rem;margin-bottom:.5rem}
.card .status{display:inline-block;padding:.15rem .5rem;border-radius:3px;font-size:.7rem}
.up{background:#00ff8822;color:#00ff88}.down{background:#ff444422;color:#ff4444}
.card .ms{color:#555;font-size:.7rem;margin-left:.5rem}</style></head><body>
<h1>🐾 Poke Labs Gateway</h1>
<p.sub">Single entry point for all services · __DATE__</p>
<div class="grid" id="g"></div>
<script>
const svcs = __SVCS__;
document.getElementById('g').innerHTML=svcs.map(s=>{
  const url=`/${s.name}`;
  return `<a class="card" href="${url}"><h3>${s.name}</h3><div class="port">:${s.port}</div><span class="status ${s.ok?'up':'down'}">${s.ok?'UP':'DOWN'}</span><span class="ms">${s.ms}ms</span></a>`;
}).join('');
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        svcs = discover()
        
        if p in ("/", "/index.html"):
            for s in svcs:
                status, ms = check(s)
                s["ok"] = 200 <= status < 400
                s["ms"] = ms
            page = PAGE.replace("__DATE__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")).replace("__SVCS__", json.dumps(svcs))
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write(page.encode())
            return
        
        if p == "/api/services":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps(svcs, indent=2).encode())
            return
        
        if p == "/api/health":
            up = sum(1 for s in svcs if check(s)[0])
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"v":1,"services":len(svcs),"up":up}).encode())
            return
        
        # Proxy to matching service
        for s in svcs:
            if p == s["path"] or p.startswith(s["path"] + "/"):
                target = f"http://localhost:{s['port']}{p[len(s['path']):]}"
                try:
                    req = urllib.request.Request(target, headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','transfer-encoding')})
                    if self.command in ("POST","PUT","PATCH"):
                        cl = int(self.headers.get("Content-Length",0))
                        req.data = self.rfile.read(cl)
                    resp = urllib.request.urlopen(req, timeout=15)
                    self.send_response(resp.status)
                    for h in resp.getheaders():
                        if h[0].lower() not in ('transfer-encoding','connection'):
                            self.send_header(h[0], h[1])
                    self.end_headers()
                    self.wfile.write(resp.read())
                except urllib.error.HTTPError as e:
                    self.send_response(e.code); self.end_headers(); self.wfile.write(e.read())
                except Exception as e:
                    self.send_response(502); self.send_header("Content-Type","application/json"); self.end_headers()
                    self.wfile.write(json.dumps({"error":str(e)}).encode())
                return
        
        self.send_response(404); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps({"error":"not found","path":p,"services":[s["name"] for s in svcs]}).encode())
    
    def do_POST(self): self.do_GET()
    def do_PUT(self): self.do_GET()
    def do_DELETE(self): self.do_GET()
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Gateway on port {PORT}")
    s.serve_forever()
