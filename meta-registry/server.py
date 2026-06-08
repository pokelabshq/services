#!/usr/bin/env python3
"""Meta Service Registry v1 — Auto-discover and display all Poke Labs services."""
import http.server, json, os, time, subprocess

PORT = 8760
SERVICES_DIR = "/home/alx/services"
VERSION = "1.0"

def discover():
    services = []
    try:
        for name in sorted(os.listdir(SERVICES_DIR)):
            path = os.path.join(SERVICES_DIR, name)
            if not os.path.isdir(path):
                continue
            # Find server files
            servers = []
            for f in os.listdir(path):
                fl = f.lower()
                if fl in ("server.py", "app.py", "bot.py", "gateway.py", "index.py"):
                    servers.append(f)
            # Check if running
            pid = None
            try:
                r = subprocess.run(["pgrep", "-f", f"{path}/.*\\.py"], capture_output=True, text=True, timeout=2)
                if r.stdout.strip():
                    pid = int(r.stdout.strip().split("\n")[0])
            except:
                pass
            # Get port from server file
            port = None
            for sf in servers:
                try:
                    with open(os.path.join(path, sf)) as fh:
                        for line in fh:
                            if "PORT" in line and "=" in line and line.strip()[0].isdigit() == False:
                                # Extract PORT = NNNN
                                import re
                                m = re.search(r'PORT\s*=\s*(\d{4,5})', line)
                                if m:
                                    port = int(m.group(1))
                                    break
                except:
                    pass
            # Check health if running
            status = "stopped"
            if pid and port:
                try:
                    import socket
                    s = socket.socket()
                    s.settimeout(1)
                    s.connect(("127.0.0.1", port))
                    s.close()
                    status = "running"
                except:
                    status = "crashed"
            services.append({
                "name": name,
                "path": path,
                "servers": servers,
                "port": port,
                "pid": pid,
                "status": status
            })
    except Exception as e:
        services.append({"error": str(e)})
    return services

PAGE = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Service Registry — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6;min-height:100vh}
.h{background:linear-gradient(135deg,#0a0a1a,#1a1a3e);padding:50px 20px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.04)}
h1{font-size:2.2rem;color:#00ffaa;margin-bottom:6px}
.sub{color:#666;font-size:.85rem}
.stats{display:flex;justify-content:center;gap:20px;padding:14px;border-bottom:1px solid rgba(255,255,255,0.04)}
.st{text-align:center;font-size:.7rem;color:#666}.st b{color:#00ffaa;font-size:1.2rem;display:block}
.container{max-width:1100px;margin:0 auto;padding:30px 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;transition:border-color .2s}
.card:hover{border-color:rgba(0,255,170,0.3)}
.card h3{font-size:.85rem;color:#e0e0e2;margin-bottom:4px;word-break:break-all}
.card .port{color:#6496ff;font-size:.7rem;margin-bottom:4px}
.card .files{color:#555;font-size:.65rem;margin-bottom:8px}
.badge{display:inline-block;padding:3px 10px;border-radius:8px;font-size:.65rem;font-weight:700}
.badge-running{background:rgba(0,255,170,0.15);color:#00ffaa}
.badge-stopped{background:rgba(255,255,255,0.06);color:#666}
.badge-crashed{background:rgba(255,107,106,0.15);color:#ff6b6a}
.actions{display:flex;gap:6px;margin-top:8px}
.btn{padding:4px 10px;border:none;border-radius:6px;cursor:pointer;font-size:.65rem;font-weight:600}
.btn-start{background:#00ffaa;color:#0a0a1a}
.btn-stop{background:#ff6b6a;color:#fff}
.btn-logs{background:rgba(255,255,255,0.06);color:#888}
</style></head><body>
<div class="h"><h1>⚙️ Service Registry</h1><p class="sub">Poke Labs — All services auto-discovered from disk</p></div>
<div class="stats">
<div class="st"><b id="total">0</b>Services</div>
<div class="st"><b id="running">0</b>Running</div>
<div class="st"><b id="stopped">0</b>Stopped</div>
</div>
<div class="container"><div class="grid" id="grid">Loading...</div></div>
<div style="text-align:center;padding:40px;color:#444;font-size:.75rem">
2026 Poke Labs &middot; Auto-refreshes every 10s &middot; <a href="/api/services" style="color:#00ffaa">JSON API</a>
</div>
<script>
async function load(){
  const d=await(await fetch("/api/services")).json();
  const svcs=d.services||[];
  let r=0,st=0;
  document.getElementById("grid").innerHTML=svcs.map(s=>{
    if(s.status==="running")r++;else st++;
    const status_class="badge-"+s.status;
    const port_display=s.port?':'+s.port:'';
    return `<div class="card"><h3>${s.name}</h3><div class="port">${port_display||'no port'}</div><div class="files">${(s.servers||[]).join(', ')||'no server file'}</div><span class="badge ${status_class}">${s.status}</span><div class="actions"><button class="btn btn-start" onclick="control('${s.name}','start')">Start</button><button class="btn btn-stop" onclick="control('${s.name}','stop')">Stop</button></div></div>`;
  }).join("");
  document.getElementById("total").textContent=svcs.length;
  document.getElementById("running").textContent=r;
  document.getElementById("stopped").textContent=st;
}
async function control(name,action){
  await fetch("/api/control",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,action})});
  setTimeout(load,2000);
}
load();setInterval(load,10000);
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        import urllib.parse
        p=urllib.parse.urlparse(self.path)
        if p.path=="/": self._html(PAGE)
        elif p.path=="/api/services": self._json({"services":discover(),"ts":time.time(),"v":VERSION})
        elif p.path=="/api/health": self._json({"ok":True,"v":VERSION,"port":PORT})
        else: self._json({"error":"not found"},404)

    def do_POST(self):
        import urllib.parse
        p=urllib.parse.urlparse(self.path)
        if p.path=="/api/control":
            try:
                length=int(self.headers.get("Content-Length",0))
                body=json.loads(self.rfile.read(length))
                name=body.get("name","")
                action=body.get("action","")
                path=os.path.join(SERVICES_DIR,name)
                if not os.path.isdir(path):
                    self._json({"error":"service not found"},404);return
                if action=="start":
                    # Find server file
                    for f in os.listdir(path):
                        fl=f.lower()
                        if fl in ("server.py","app.py","bot.py","gateway.py"):
                            subprocess.Popen(["nohup","python3",os.path.join(path,f)],stdout=open("/tmp/"+name+".log","w"),stderr=subprocess.STDOUT,start_new_session=True)
                            self._json({"ok":True,"action":"start","service":name,"file":f});return
                    self._json({"error":"no server file found"},400)
                elif action=="stop":
                    os.system(f"pkill -f '{path}/.*\\.py'")
                    self._json({"ok":True,"action":"stop","service":name})
                else: self._json({"error":"unknown action"},400)
            except Exception as e: self._json({"error":str(e)},500)
        else: self._json({"error":"not found"},404)

    def _html(self,h,code=200):
        b=h.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers();self.wfile.write(b)

    def _json(self,d,code=200):
        b=json.dumps(d,default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers();self.wfile.write(b)

    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Meta Service Registry v{VERSION} on :{PORT}")
    s.serve_forever()
