#!/usr/bin/env python3
"""Poke Labs Dashboard v2.0 — Real-time service monitor. Port: 8802"""
import http.server, json, socket, time, subprocess, os, urllib.request, urllib.error, sys

PORT = 8802
VERSION = "2.0.0"
START = time.time()

SERVICES = {
    "dashboard": 8750, "link-preview": 8765, "feedback-tracker": 8766,
    "url-shortener": 8767, "email": 8768, "status-page": 8769,
    "poke-bot": 8770, "poke-connect": 8771, "poke-cast": 8772,
    "poke-forge": 8773, "poke-lab": 8774, "poke-hub": 8775,
    "telegram-bot": 8777, "stats-tracker": 8778, "doc-gen": 8779,
    "skills-hub": 8780, "skills-market": 8781, "agent-cast": 8782,
    "mesh-hub": 8783, "data-forge": 8784, "agent-registry": 8785,
    "health-check": 8786, "task-queue": 8787, "cron-scheduler": 8788,
    "inbox": 8789, "api-gateway": 8790, "poke-status": 8791,
    "billing": 8795, "health-aggregator": 8799, "landing": 8801,
}
REPOS = ["council","services","cli","action","awesome-ai-agents","poke-engine","poke-labs-site"]
_CACHE = {}
_CACHE_T = {}

def check_port(port, t=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(t)
        s.connect(("127.0.0.1", port)); s.close(); return True
    except: return False

def cached(key, fn, ttl=30):
    n = time.time()
    if key not in _CACHE or n - _CACHE_T.get(key,0) > ttl:
        try: _CACHE[key] = fn()
        except: _CACHE[key] = _CACHE.get(key, None)
        _CACHE_T[key] = n
    return _CACHE[key]

def gh_stars():
    t = 0
    for r in REPOS:
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/pokelabshq/{r}", headers={"User-Agent":"poke-dash/2.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                t += json.loads(resp.read()).get("stargazers_count", 0)
        except: pass
    return t

def disk():
    try:
        o = subprocess.run(["df","-h","/home/alx"], capture_output=True, text=True, timeout=2).stdout
        p = o.strip().split("\n")[1].split()
        return {"size":p[1],"used":p[2],"avail":p[3],"pct":p[4]}
    except: return None

def svc_list():
    return [{"name":n,"port":p,"up":check_port(p)} for n,p in sorted(SERVICES.items(),key=lambda x:x[1])]

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/": self.send_html()
        elif path == "/api/status":
            svcs = svc_list()
            up = sum(1 for s in svcs if s["up"])
            self.send_json({"v":VERSION,"time":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"uptime_s":int(time.time()-START),"total":len(svcs),"up":up,"down":len(svcs)-up,"services":svcs,"disk":cached("d",disk),"stars":cached("s",gh_stars),"repos":len(REPOS)})
        elif path == "/api/health": self.send_json({"ok":True,"v":VERSION,"port":PORT})
        else: self.send_json({"error":"not found"},404)
    def send_json(self,data,code=200):
        b=json.dumps(data).encode(); self.send_response(code)
        self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def send_html(self):
        h=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Poke Labs Dashboard v{VERSION}</title>
<style>
:root{{--bg:#0d1117;--srf:#161b22;--srf2:#21262d;--brd:#30363d;--txt:#c9d1d9;--mut:#8b949e;--acc:#58a6ff;--grn:#3fb950;--red:#f85149;--ylw:#d29922;--pnk:#f778ba}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh}}
a{{color:var(--acc);text-decoration:none}}
.top{{background:var(--srf);border-bottom:1px solid var(--brd);padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center}}
.top h1{{font-size:1.2rem}} .top h1 s{{color:var(--acc)}} .top .v{{color:var(--mut);font-size:.8rem}}
.c{{max-width:1100px;margin:0 auto;padding:1.5rem}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;margin-bottom:1.5rem}}
.sc{{background:var(--srf);border:1px solid var(--brd);border-radius:8px;padding:1.25rem;text-align:center}}
.sc .n{{font-size:2rem;font-weight:700}} .sc .l{{color:var(--mut);font-size:.85rem;margin-top:.25rem}}
.grn{{color:var(--grn)}} .red{{color:var(--red)}} .ylw{{color:var(--ylw)}}
.svcs{{background:var(--srf);border:1px solid var(--brd);border-radius:8px;overflow:hidden}}
.svcs h2{{padding:1rem;border-bottom:1px solid var(--brd);font-size:1rem}}
.svcs h2 s{{color:var(--mut);font-weight:normal}}
.grd{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.5rem;padding:1rem}}
.svc{{background:var(--srf2);border-radius:6px;padding:.75rem 1rem;display:flex;justify-content:space-between;align-items:center;font-size:.85rem}}
.svc.up{{border-left:3px solid var(--grn)}} .svc.dn{{border-left:3px solid var(--red);opacity:.6}}
.svc .nm{{font-weight:600}} .svc .pt{{font-family:monospace;color:var(--mut);font-size:.75rem}}
.svc .st{{font-size:.7rem;padding:.15rem .5rem;border-radius:10px}}
.svc .st.up{{background:rgba(63,185,80,.15);color:var(--grn)}} .svc .st.dn{{background:rgba(248,81,73,.15);color:var(--red)}}
.bar{{height:4px;background:var(--srf2);border-radius:2px;margin-top:1rem;overflow:hidden}}
.bf{{height:100%;background:linear-gradient(90deg,var(--grn),var(--acc));border-radius:2px;transition:width .5s}}
footer{{text-align:center;padding:2rem;color:var(--mut);font-size:.8rem}}
</style></head><body>
<div class="top"><h1>🐾 <s>Poke Labs</s> Dashboard</h1><span class="v">v{VERSION}</span></div>
<div class="c"><div class="stats" id="stats"><div class="sc"><div class="n">—</div><div class="l">Loading...</div></div></div>
<div class="svcs"><h2>📡 Services <span id="ss"></span></h2><div class="grd" id="g">Loading...</div>
<div class="bar"><div class="bf" id="bf" style="width:0%"></div></div></div>
<footer>Built by Poke 🐾 for Alexander Wondwossen · MIT · <a href="https://github.com/pokelabshq">GitHub</a></footer></div>
<script>
async function rf(){{
try{{const r=await fetch('/api/status'),d=await r.json();
const pct=d.total>0?(d.up/d.total*100).toFixed(1):0;
document.getElementById('stats').innerHTML=`
<div class="sc"><div class="n grn">${{d.up}}</div><div class="l">Services Up</div></div>
<div class="sc"><div class="n red">${{d.down}}</div><div class="l">Services Down</div></div>
<div class="sc"><div class="n" style="color:var(--acc)">${{d.total}}</div><div class="l">Total Known</div></div>
<div class="sc"><div class="n ylw">${{d.repos}}</div><div class="l">GitHub Repos</div></div>
<div class="sc"><div class="n" style="color:var(--pnk)">⭐ ${{d.stars||'—'}}</div><div class="l">Total Stars</div></div>
<div class="sc"><div class="n">${{pct}}%</div><div class="l">Uptime</div></div>
${{d.disk?`<div class="sc"><div class="n" style="font-size:1.2rem">${{d.disk.pct}}</div><div class="l">Disk (${{d.disk.used}}/${{d.disk.size}})</div></div>`:''}}`;
document.getElementById('ss').textContent=`(${{d.up}}/${{d.total}} up)`;
document.getElementById('bf').style.width=pct+'%';
const g=document.getElementById('g');g.innerHTML='';
for(const s of d.services){{const c=s.up?'up':'dn';g.innerHTML+=`<div class="svc ${{c}}"><div><div class="nm">${{s.name}}</div><div class="pt">:${{s.port}}</div></div><span class="st ${{c}}">${{s.up?'UP':'DOWN'}}</span></div>`;}}
}}catch(e){{document.getElementById('g').innerHTML='<div style="padding:1rem;color:var(--red)">Error: '+e+'</div>';}}}}
rf();setInterval(rf,15000);
</script></body></html>'''
        b=h.encode(); self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(b)))
        self.end_headers(); self.wfile.write(b)

if __name__=="__main__":
    srv = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Poke Labs Dashboard v{VERSION} running on :{PORT}", flush=True)
    srv.serve_forever()
