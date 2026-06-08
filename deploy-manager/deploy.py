#!/usr/bin/env python3
"""Deploy Manager v1 — Fleet management for all Poke Labs services."""
import http.server, json, os, subprocess, time, signal, urllib.parse, threading

PORT = 8798
SERVICES_DIR = "/home/alx/services"
PROCS = {}  # name -> subprocess.Popen
lock = threading.Lock()

SERVER_NAMES = ("server.py", "app.py", "bot.py", "gateway.py", "index.py",
                "deploy.py", "digest.py", "metrics.py", "health.py")

def discover():
    svcs = []
    for name in sorted(os.listdir(SERVICES_DIR)):
        path = os.path.join(SERVICES_DIR, name)
        if not os.path.isdir(path): continue
        servers, port = [], None
        for f in os.listdir(path):
            if f.lower() in SERVER_NAMES:
                servers.append(f)
                if port is None:
                    try:
                        with open(os.path.join(path, f)) as fh:
                            import re
                            for line in fh:
                                m = re.search(r'PORT\s*=\s*(\d{4,5})', line)
                                if m: port = int(m.group(1)); break
                    except: pass
        pid, status = None, "stopped"
        if port:
            try:
                r = subprocess.run(["pgrep", "-f", f".*{name}.*\\.py"],
                                   capture_output=True, text=True, timeout=2)
                if r.stdout.strip():
                    pid = int(r.stdout.strip().split("\n")[0])
                    import socket; s = socket.socket(); s.settimeout(1)
                    s.connect(("127.0.0.1", port)); s.close()
                    status = "running"
            except: status = "stopped"
        svcs.append({"name": name, "servers": servers, "port": port,
                      "pid": pid, "status": status, "path": path})
    return svcs

def do_start(name):
    path = os.path.join(SERVICES_DIR, name)
    if not os.path.isdir(path): return {"error": "not found"}
    for sn in SERVER_NAMES:
        fp = os.path.join(path, sn)
        if os.path.exists(fp):
            with lock:
                p = subprocess.Popen(
                    ["python3", fp],
                    stdout=open(f"/tmp/{name}.log", "a"),
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
                PROCS[name] = p
            return {"ok": True, "name": name, "file": sn, "pid": p.pid}
    return {"error": "no server file"}

def do_stop(name):
    with lock:
        if name in PROCS:
            try: PROCS[name].kill(); PROCS.pop(name)
            except: pass
    os.system(f"pkill -f '{SERVICES_DIR}/{name}/' 2>/dev/null")
    return {"ok": True, "name": name, "action": "stop"}

HTML = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><title>Deploy Manager — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6;padding:20px}
h1{color:#00ffaa;margin:10px 0 20px;font-size:1.8rem}
.stats{display:flex;gap:16px;margin:16px 0}
.st{background:rgba(255,255,255,0.03);padding:12px 20px;border-radius:10px;text-align:center}
.st b{color:#00ffaa;display:block;font-size:1.2rem}
table{width:100%;border-collapse:collapse;font-size:.8rem;margin-top:16px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.04)}
th{color:#555;font-size:.7rem;text-transform:uppercase}
.btn{padding:4px 12px;border:none;border-radius:6px;cursor:pointer;font-size:.7rem;font-weight:600;margin:0 2px}
.btn-start{background:#00ffaa;color:#0a0a1a}.btn-stop{background:#ff6b6a;color:#fff}
.badge{padding:3px 10px;border-radius:6px;font-size:.65rem;font-weight:700}
.running{background:rgba(0,255,170,0.15);color:#00ffaa}
.stopped{background:rgba(255,255,255,0.06);color:#666}
.crashed{background:rgba(255,107,106,0.15);color:#ff6b6a}
tr:hover{background:rgba(255,255,255,0.02)}
.actions{display:flex;gap:12px;margin:12px 0}
.ab{padding:8px 16px;border:none;border-radius:8px;cursor:pointer;font-weight:700;font-size:.8rem}
.ab-all-start{background:#00ffaa;color:#0a0a1a}
.ab-all-stop{background:#ff6b6a;color:#fff}
</style></head><body>
<h1>🚀 Deploy Manager</h1>
<div class="actions">
<button class="ab ab-all-start" onclick="mass('start')">▶ Start All</button>
<button class="ab ab-all-stop" onclick="mass('stop')">⏹ Stop All</button>
</div>
<div class="stats"><div class="st"><b id="total">0</b>Total</div>
<div class="st"><b id="run">0</b>Running</div>
<div class="st"><b id="stp">0</b>Stopped</div></div>
<table><thead><tr><th>Service</th><th>Port</th><th>Files</th><th>Status</th><th>Actions</th></tr></thead>
<tbody id="rows"><tr><td colspan="5" style="text-align:center;color:#555;padding:30px">Loading...</td></tr></tbody></table>
<div style="text-align:center;padding:30px;color:#444;font-size:.75rem">
Poke Labs Deploy Manager &middot; Auto-refreshes 10s &middot; <a href="/api/list" style="color:#00ffaa">API</a>
</div>
<script>
async function load(){
  const d=await(await fetch("/api/list")).json();
  const svcs=d.services||[];
  let r=0,st=0;
  document.getElementById("rows").innerHTML=svcs.map(s=>{
    s.status==="running"?r++:st++;
    return `<tr><td><b>${s.name}</b></td><td>${s.port||"—"}</td>
    <td><small style="color:#555">${(s.servers||[]).join(", ")||"—"}</small></td>
    <td><span class="badge ${s.status}">${s.status}</span></td>
    <td><button class="btn btn-start" onclick="ctrl('${s.name}','start')">Start</button>
    <button class="btn btn-stop" onclick="ctrl('${s.name}','stop')">Stop</button></td></tr>`;
  }).join("");
  document.getElementById("total").textContent=svcs.length;
  document.getElementById("run").textContent=r;document.getElementById("stp").textContent=st;
}
async function ctrl(n,a){await fetch("/api/ctrl",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,action:a})});setTimeout(load,2000);}
async function mass(a){
  const d=await(await fetch("/api/list")).json();
  for(const s of d.services||[])
    await fetch("/api/ctrl",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:s.name,action:a})});
  setTimeout(load,3000);
}
load();setInterval(load,10000);
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/": self.html(HTML)
        elif p.path=="/api/list": self.json({"services":discover(),"ts":time.time()})
        elif p.path=="/api/health": self.json({"ok":True,"v":1,"port":PORT,"managed":len(discover())})
        else: self.json({"error":"not found"},404)
    def do_POST(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/api/ctrl":
            try:
                body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
                name,action=body.get("name",""),body.get("action","")
                if action=="start": self.json(do_start(name))
                elif action=="stop": self.json(do_stop(name))
                else: self.json({"error":"bad action"},400)
            except Exception as e: self.json({"error":str(e)},500)
        else: self.json({"error":"not found"},404)
    def html(self,h,code=200):
        b=h.encode("utf-8");self.send_response(code)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def json(self,d,code=200):
        b=json.dumps(d,default=str).encode();self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),H)
    print(f"Deploy Manager v1 on :{PORT}")
    s.serve_forever()
