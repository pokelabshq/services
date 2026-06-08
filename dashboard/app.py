#!/usr/bin/env python3
"""Poke Labs Service Dashboard v3 — Unified status page for all services."""
import http.server, json, urllib.request, os, re, subprocess, datetime, threading, time

PORT = 8799
SERVICES_DIR = "/home/alx/services"
COUNCIL_DIR = "/home/alx/council"

def scan_all():
    services = []
    if not os.path.isdir(SERVICES_DIR):
        return services
    for name in sorted(os.path.dirname(x) for x in __import__('glob').glob(f"{SERVICES_DIR}/*/")):
        name = os.path.basename(name)
        skill = os.path.join(SERVICES_DIR, name, "SKILL.md")
        server = os.path.join(SERVICES_DIR, name, "server.py")
        if not os.path.exists(skill) and not os.path.exists(server):
            continue
        desc, port, tags = "", 0, []
        if os.path.exists(skill):
            with open(skill) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        desc = line[:120]
                        break
            pm = re.search(r'[Pp]ort[:\s]+(\d{4,5})', open(skill).read())
            if pm: port = int(pm.group(1))
        if os.path.exists(server):
            tags.append("server")
            if not port:
                pm = re.search(r'PORT\s*=\s*(\d{4,5})', open(server).read())
                if pm: port = int(pm.group(1))
        else:
            tags.append("skill")
        services.append({"name":name,"desc":desc or f"{name} service","port":port,"tags":tags})
    return services

def check_port(port):
    if not port: return "unknown"
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
        return "up"
    except urllib.error.HTTPError:
        return "up"
    except:
        return "down"

def get_repos():
    try:
        r = subprocess.run(["gh","api","users/pokelabshq/repos","--jq",".[].full_name"],
                          capture_output=True,text=True,timeout=10)
        return [x for x in r.stdout.strip().split("\n") if x]
    except: return []

def get_workflows():
    wf_dir = os.path.join(COUNCIL_DIR, ".github/workflows")
    if not os.path.isdir(wf_dir): return []
    return [f.replace(".yml","").replace(".yaml","") for f in os.listdir(wf_dir) if f.endswith((".yml",".yaml"))]

PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Labs — Service Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}
.hdr{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:2rem 1rem;text-align:center;border-bottom:1px solid #2a2a4a}
.hdr h1{font-size:2.2rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr p{color:#777;margin-top:.4rem;font-size:.9rem}
.stats{display:flex;justify-content:center;gap:2rem;margin:1.5rem 0;flex-wrap:wrap}
.stat{text-align:center}
.stat .n{font-size:1.8rem;font-weight:700;color:#00d4ff}
.stat .l{color:#555;font-size:.75rem;text-transform:uppercase;letter-spacing:.05rem}
.sb{max-width:500px;margin:0 auto 1.5rem;padding:0 1rem}
.sb input{width:100%;padding:.6rem 1rem;border:1px solid #333;border-radius:8px;background:#111;color:#fff;font-size:.95rem;outline:none;transition:border-color .2s}
.sb input:focus{border-color:#7b2ff7}
.tabs{display:flex;justify-content:center;gap:.5rem;margin-bottom:1.5rem;flex-wrap:wrap;padding:0 1rem}
.tab{padding:.4rem 1rem;border:1px solid #333;border-radius:20px;background:transparent;color:#888;cursor:pointer;font-size:.85rem;transition:all .2s}
.tab:hover,.tab.active{border-color:#7b2ff7;color:#7b2ff7;background:#1a1a2e}
.grid{max-width:1100px;margin:0 auto;padding:0 1rem 2rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.75rem}
.card{background:#111;border:1px solid #1a1a1a;border-radius:10px;padding:1rem;transition:border-color .2s,transform .15s;position:relative;overflow:hidden}
.card:hover{border-color:#444;transform:translateY(-1px)}
.card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:10px 0 0 10px}
.card.up::before{background:#00ff88}.card.down::before{background:#ff4444}.card.unknown::before{background:#444}
.card h3{font-size:.95rem;color:#e0e0e0;margin-bottom:.2rem;display:flex;align-items:center;gap:.4rem}
.card h3 .dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.card h3 .dot.up{background:#00ff88;box-shadow:0 0 6px #00ff8866}
.card h3 .dot.down{background:#ff4444}..card h3 .dot.unknown{background:#555}
.card p{color:#666;font-size:.8rem;line-height:1.4;margin-bottom:.5rem}
.card .meta{display:flex;justify-content:space-between;align-items:center}
.card .port{color:#444;font-size:.75rem;font-family:monospace}
.card .tags{display:flex;gap:.3rem}
.card .tag{background:#1a1a2e;padding:.15rem .4rem;border-radius:3px;font-size:.65rem;color:#666}
.section-title{max-width:1100px;margin:1.5rem auto .75rem;padding:0 1rem;color:#555;font-size:.8rem;text-transform:uppercase;letter-spacing:.08rem}
.ft{text-align:center;padding:2rem;color:#444;border-top:1px solid #1a1a1a;font-size:.8rem}
.ft a{color:#7b2ff7;text-decoration:none}
</style></head><body>
<div class="hdr">
<h1>🐾 Poke Labs Dashboard</h1>
<p>__DATE__ · Auto-refreshes every 30s</p>
<div class="stats">
<div class="stat"><div class="n">__SVC_COUNT__</div><div class="l">Services</div></div>
<div class="stat"><div class="n">__REPO_COUNT__</div><div class="l">Repos</div></div>
<div class="stat"><div class="n">__WF_COUNT__</div><div class="l">Workflows</div></div>
<div class="stat"><div class="n">__UP_COUNT__</div><div class="l">Online</div></div>
</div>
</div>
<div class="sb"><input type="text" id="q" placeholder="Filter services..." oninput="render()"></div>
<div class="tabs">
<button class="tab active" onclick="setTab('all',this)">All</button>
<button class="tab" onclick="setTab('server',this)">Servers</button>
<button class="tab" onclick="setTab('skill',this)">Skills</button>
<button class="tab" onclick="setTab('up',this)">Online</button>
</div>
<div class="section-title">Services</div>
<div class="grid" id="g"></div>
<div class="section-title">Repositories</div>
<div class="grid" id="r"></div>
<div class="section-title">GitHub Actions</div>
<div class="grid" id="w"></div>
<div class="ft">
<p>🐾 <a href="https://github.com/pokelabshq">Poke Labs on GitHub</a> · MIT Licensed</p>
<p style="margin-top:.3rem;font-size:.7rem;color:#333">0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</p>
</div>
<script>
const services=__SVC_JSON__;
const repos=__REPO_JSON__;
const workflows=__WF_JSON__;
let tab='all';
function setTab(t,el){tab=t;document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));el.classList.add('active');render();}
function render(){
  const q=document.getElementById('q').value.toLowerCase();
  const filtered=services.filter(s=>{
    if(tab==='server'&&!s.tags.includes('server'))return false;
    if(tab==='skill'&&!s.tags.includes('skill'))return false;
    if(tab==='up'&&s.status!=='up')return false;
    return s.name.toLowerCase().includes(q)||s.desc.toLowerCase().includes(q);
  });
  document.getElementById('g').innerHTML=filtered.map(s=>{
    const dot=`<span class="dot ${s.status}"></span>`;
    const port=s.port?`:${s.port}`:'';
    const tags=s.tags.map(t=>`<span class="tag">${t}</span>`).join('');
    return `<div class="card ${s.status}"><h3>${dot}${s.name}${port}</h3><p>${s.desc}</p><div class="meta"><div class="tags">${tags}</div><span class="port">${s.status}</span></div></div>`;
  }).join('');
  document.getElementById('r').innerHTML=repos.map(r=>`<div class="card unknown"><h3><span class="dot unknown"></span>${r}</h3><p>GitHub repository</p><div class="meta"><div class="tags"><span class="tag">repo</span></div></div></div>`).join('');
  document.getElementById('w').innerHTML=workflows.map(w=>`<div class="card unknown"><h3><span class="dot unknown"></span>${w}</h3><p>GitHub Actions workflow</p><div class="meta"><div class="tags"><span class="tag">ci</span></div></div></div>`).join('');
}
render();
setInterval(async()=>{
  try{const r=await fetch('/api/live');const d=await r.json();services.forEach(s=>{const l=d.find(x=>x.name===s.name);if(l)s.status=l.status;});render();}catch(e){}
},30000);
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=self.path.split("?")[0]
        if p=="/":
            svcs=scan_all()
            repos=get_repos()
            wfs=get_workflows()
            up=sum(1 for s in svcs if s.get("status")=="up")
            page=(PAGE
                .replace("__DATE__",datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC"))
                .replace("__SVC_COUNT__",str(len(svcs)))
                .replace("__REPO_COUNT__",str(len(repos)))
                .replace("__WF_COUNT__",str(len(wfs)))
                .replace("__UP_COUNT__",str(up))
                .replace("__SVC_JSON__",json.dumps(svcs))
                .replace("__REPO_JSON__",json.dumps(repos))
                .replace("__WF_JSON__",json.dumps(wfs)))
            self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(page.encode())
        elif p=="/api/live":
            svcs=scan_all()
            results=[]
            for s in svcs:
                st=check_port(s["port"]) if s["port"] else "unknown"
                s["status"]=st
                results.append({"name":s.name,"status":st})
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps(results).encode())
        elif p=="/api/health":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps({"ok":True,"v":3}).encode())
        else:self.send_response(404);self.end_headers()
    def log_message(self,*a):pass

if __name__=="__main__":
    server=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Dashboard v3 on port {PORT}")
    server.serve_forever()
