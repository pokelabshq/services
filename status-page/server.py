#!/usr/bin/env python3
"""Poke Labs Status Page — Public service status dashboard. Port 8740."""
import http.server, json, subprocess, os, socketserver, urllib.parse, datetime, re

PORT = 8740
SERVICES_DIR = "/home/alx/services"
ENTRY_FILES = ["server.py", "bot.py", "app.py", "main.py", "index.js"]

def discover():
    svcs = []
    if not os.path.isdir(SERVICES_DIR): return svcs
    for name in sorted(os.listdir(SERVICES_DIR)):
        sdir = os.path.join(SERVICES_DIR, name)
        if not os.path.isdir(sdir): continue
        for entry in ENTRY_FILES:
            if os.path.isfile(os.path.join(sdir, entry)):
                port = None
                try:
                    with open(os.path.join(sdir, entry)) as f:
                        for line in f:
                            m = re.search(r'PORT\s*=\s*(\d{4,5})', line)
                            if m: port = int(m.group(1)); break
                except: pass
                running = False
                if port:
                    try:
                        r = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, timeout=2)
                        if r.returncode == 0 and r.stdout.strip(): running = True
                    except: pass
                svcs.append({"name": name, "port": port, "running": running})
                break
    return svcs

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/api/status": self.send_json({"ts": datetime.datetime.utcnow().isoformat(), "services": self.check_all()})
        elif p == "/": self.send_html(PAGE)
        else: self.send_json({"error": "not found"}, 404)

    def check_all(self):
        svcs = discover()
        total = len(svcs)
        up = sum(1 for s in svcs if s["running"])
        return {"total": total, "up": up, "down": total - up, "uptime_pct": round(100*up/total) if total else 0, "services": svcs}

    def send_json(self, d, c=200):
        b = json.dumps(d, default=str).encode()
        self.send_response(c); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)

    def send_html(self, h):
        b = h.encode()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Labs Status</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e0;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:40px 20px}
.header{text-align:center;margin-bottom:32px}
h1{font-size:2.2em;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#666;margin-top:8px}
.stats{display:flex;gap:16px;margin-bottom:32px;flex-wrap:wrap;justify-content:center}
.stat{background:#16162a;border:1px solid #2a2a4a;border-radius:12px;padding:20px 28px;text-align:center;min-width:120px}
.stat .v{font-size:2em;font-weight:700}
.stat .l{font-size:.75em;color:#666;text-transform:uppercase;margin-top:4px}
.ok{color:#34d399}.warn{color:#fbbf24}.err{color:#f87171}
.bar{height:8px;background:#1a1a3a;border-radius:4px;overflow:hidden;margin-bottom:32px;width:100%;max-width:600px}
.bar-fill{height:100%;background:linear-gradient(90deg,#34d399,#60a5fa);border-radius:4px;transition:width 1s}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;width:100%;max-width:800px}
.s{background:#12122a;border:1px solid #2a2a4a;border-radius:8px;padding:12px 16px;display:flex;align-items:center;gap:10px;font-size:.9em}
.d{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.d.up{background:#34d399;box-shadow:0 0 6px #34d399}.d.down{background:#f87171;box-shadow:0 0 6px #f87171}
.sn{flex:1}.pt{color:#555;font-size:.8em;font-family:mono}
footer{margin-top:40px;color:#444;font-size:.8em}
</style></head><body>
<div class="header"><h1>🫧 Poke Labs</h1><p class="sub">Service Status Dashboard</p></div>
<div class="stats" id="stats"></div>
<div class="bar"><div class="bar-fill" id="bar" style="width:0%"></div></div>
<div class="grid" id="grid"></div>
<footer>Powered by Poke Labs · Open Source · <a href="https://github.com/pokelabshq/services" style="color:#60a5fa">GitHub</a></footer>
<script>
(async function(){
  try{
    const d=await(await fetch('/api/status')).json();
    const s=d.services;
    const up=s.filter(x=>x.running).length;
    const down=s.length-up;
    const pct=d.uptime_pct;
    document.getElementById('stats').innerHTML=`
      <div class="stat"><div class="v">${s.length}</div><div class="l">Total</div></div>
      <div class="stat"><div class="v ok">${up}</div><div class="l">Operational</div></div>
      <div class="stat"><div class="v ${down?'err':'ok'}">${down}</div><div class="l">Down</div></div>
      <div class="stat"><div class="v ${pct>90?'ok':pct>50?'warn':'err'}">${pct}%</div><div class="l">Uptime</div></div>
    `;
    document.getElementById('bar').style.width=pct+'%';
    document.getElementById('grid').innerHTML=s.map(x=>`
      <div class="s"><div class="d ${x.running?'up':'down'}"></div>
      <div class="sn">${x.name}</div>
      ${x.port?'<div class="pt">:'+x.port+'</div>':''}</div>
    `).join('');
  }catch(e){document.getElementById('stats').innerHTML='<p class="err">Failed to load status</p>'}
})();
setInterval(()=>location.reload(),30000);
</script></body></html>"""

class R(socketserver.TCPServer): allow_reuse_address=True

if __name__=="__main__":
    print(f"📊 Poke Status Page on port {PORT}")
    R(("",PORT),H).serve_forever()
