#!/usr/bin/env python3
"""Poke Dashboard v1.0 — Unified service management UI. Port: 8760. Zero deps."""
import http.server, json, subprocess, os, signal, socketserver, urllib.parse, datetime, re

PORT = 8760
SERVICES_DIR = "/home/alx/services"
ENTRY_FILES = ["server.py", "bot.py", "app.py", "main.py", "index.js"]

def discover():
    services = []
    if not os.path.isdir(SERVICES_DIR): return services
    for name in sorted(os.listdir(SERVICES_DIR)):
        sdir = os.path.join(SERVICES_DIR, name)
        if not os.path.isdir(sdir): continue
        for entry in ENTRY_FILES:
            fpath = os.path.join(sdir, entry)
            if os.path.isfile(fpath):
                port = None
                try:
                    with open(fpath) as f:
                        for line in f:
                            m = re.search(r'PORT\s*=\s*(\d{4,5})', line)
                            if m:
                                port = int(m.group(1))
                                break
                except: pass
                running, pid = False, None
                if port:
                    try:
                        r = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, timeout=2)
                        if r.returncode == 0 and r.stdout.strip():
                            running, pid = True, r.stdout.strip().decode()
                    except: pass
                services.append({"name": name, "entry": entry, "path": sdir, "port": port, "running": running, "pid": pid})
                break
    return services

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/services": self.send_json(discover())
        elif path == "/api/status": self.send_json({"ok": True, "v": 1, "port": PORT, "ts": datetime.datetime.now().isoformat()})
        elif path == "/": self.send_html(DASH_HTML)
        else: self.send_response(404); self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        name = body.get("name", "")
        if path == "/api/start":
            self.send_json(self._start(name))
        elif path == "/api/stop":
            self.send_json(self._stop(name, body.get("pid"), body.get("port")))
        else: self.send_response(404); self.end_headers()

    def _start(self, name):
        sdir = os.path.join(SERVICES_DIR, name)
        if not os.path.isdir(sdir): return {"ok": False, "error": "not found"}
        for entry in ENTRY_FILES:
            fpath = os.path.join(sdir, entry)
            if os.path.isfile(fpath):
                try:
                    subprocess.Popen(["nohup", "python3", fpath],
                        stdout=open(f"/tmp/{name}.log", "a"), stderr=subprocess.STDOUT,
                        cwd=sdir, start_new_session=True)
                    return {"ok": True, "message": f"Started {name}"}
                except Exception as e: return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "no entry point"}

    def _stop(self, name, pid, port):
        killed = []
        if pid:
            try: os.kill(int(pid), signal.SIGTERM); killed.append(f"pid={pid}")
            except: pass
        if port:
            try: subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=3); killed.append(f"port={port}")
            except: pass
        return {"ok": True, "message": f"Stopped {name} ({', '.join(killed)})" if killed else "Nothing to stop"}

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def send_html(self, html):
        body = html.encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a): pass

DASH_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Dashboard</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
h1{font-size:1.8em;margin-bottom:4px}.sub{color:#94a3b8;margin-bottom:24px;font-size:.9em}
.stats{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap}
.stat{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 20px;text-align:center}
.stat .num{font-size:1.6em;font-weight:bold;color:#60a5fa}.stat .label{font-size:.75em;color:#94a3b8;text-transform:uppercase}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.card{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:16px}
.card h3{font-size:.95em;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.7em;font-weight:600}
.badge.up{background:#059669;color:#d1fae5}.badge.down{background:#dc2626;color:#fee2e2}
.port{color:#60a3f5;font-size:.85em;font-family:mono}.path{color:#64748b;font-size:.75em;font-family:mono;margin-top:4px}
.btns{display:flex;gap:8px;margin-top:12px}
.btn{flex:1;padding:6px 12px;border:1px solid #475569;border-radius:6px;background:transparent;color:#e2e8f0;cursor:pointer;font-size:.8em;text-align:center}
.btn.start{border-color:#059669;color:#6ee7b7}.btn.stop{border-color:#dc2626;color:#fca5a5}
</style></head><body>
<h1>🫧 Poke Dashboard</h1><p class="sub">v1.0 · Port 8760</p>
<div class="stats">
<div class="stat"><div class="num" id="total">—</div><div class="label">Services</div></div>
<div class="stat"><div class="num" id="running" style="color:#6ee7b7">—</div><div class="label">Running</div></div>
<div class="stat"><div class="num" id="down" style="color:#fca5a5">—</div><div class="label">Down</div></div>
</div>
<div class="grid" id="grid">Loading...</div>
<script>
async function load(){
  const svcs=await(await fetch('/api/services')).json();
  document.getElementById('total').textContent=svcs.length;
  document.getElementById('running').textContent=svcs.filter(s=>s.running).length;
  document.getElementById('down').textContent=svcs.filter(s=>!s.running).length;
  document.getElementById('grid').innerHTML=svcs.map(s=>`<div class="card">
    <h3><span class="badge ${s.running?'up':'down'}">${s.running?'UP':'DOWN'}</span> ${s.name}</h3>
    <div class="port">${s.port?'Port '+s.port:'No port'}</div>
    <div class="path">${s.path}/${s.entry}</div>
    <div class="btns">
    <button class="btn start" onclick="fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'${s.name}'})}).then(()=>setTimeout(load,2000))">Start</button>
    <button class="btn stop" onclick="fetch('/api/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'${s.name}',pid:${s.pid||'null'},port:${s.port||'null'}})}).then(()=>setTimeout(load,2000))">Stop</button>
    </div></div>`).join('');
}
load();setInterval(load,10000);
</script></body></html>"""

class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"🫧 Poke Dashboard v1.0 on port {PORT}")
    ReusableServer(("", PORT), Handler).serve_forever()
