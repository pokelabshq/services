#!/usr/bin/env python3
"""Skills Marketplace v2 — Skill discovery, search, and installation."""
import http.server, json, os, time, urllib.parse

PORT = 8781
VERSION = "2.0"

SKILLS = [
    {"id":"link-preview-api","name":"Link Preview API","cat":"api","desc":"Extract title, description, image from any URL","ver":"4.0","port":8765,"free":3,"price":"x402"},
    {"id":"pokelabs-site","name":"Poke Labs Site","cat":"web","desc":"Landing page + dashboard server","ver":"7.0","port":8766,"free":True,"price":"free"},
    {"id":"github-reply-bot","name":"GitHub Reply Bot","cat":"bot","desc":"Auto-reply to issues/PRs with context","ver":"1.0","port":8775,"free":True,"price":"free"},
    {"id":"poke-hub","name":"Poke Hub","cat":"bot","desc":"All-in-one GitHub bot (reply+stale+label+dash)","ver":"1.2","port":8775,"free":True,"price":"free"},
    {"id":"poke-bot","name":"Poke Bot","cat":"bot","desc":"Auto-triage and priority labeling","ver":"1.0","port":8770,"free":True,"price":"free"},
    {"id":"council","name":"AI Council","cat":"automation","desc":"Stale issue check, dep update, digest","ver":"2.0","port":None,"free":True,"price":"free"},
    {"id":"auto-merge-pr","name":"Auto-Merge PRs","cat":"automation","desc":"Auto-merge Dependabot semver-patch PRs","ver":"1.0","port":None,"free":True,"price":"free"},
    {"id":"github-stats","name":"GitHub Stats","cat":"analytics","desc":"Organization contributor statistics","ver":"1.0","port":8779,"free":True,"price":"free"},
    {"id":"prometheus-metrics","name":"Prometheus Metrics","cat":"monitoring","desc":"Standard /metrics Prometheus endpoint","ver":"1.0","port":8790,"free":True,"price":"free"},
    {"id":"health-aggregator","name":"Health Aggregator","cat":"monitoring","desc":"Aggregate health checks across services","ver":"1.0","port":8799,"free":True,"price":"free"},
    {"id":"x402-gateway","name":"x402 Gateway","cat":"payments","desc":"Accept USDC micropayments via x402","ver":"1.0","port":8795,"free":False,"price":"gateway"},
    {"id":"deploy-manager","name":"Deploy Manager","cat":"devops","desc":"Fleet management for all services","ver":"1.0","port":8798,"free":True,"price":"free"},
]

CATS = sorted(set(s["cat"] for s in SKILLS))

PAGE = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Skills Marketplace — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6;min-height:100vh}
.h{background:linear-gradient(135deg,#0a0a1a,#1a1a3e);padding:50px 20px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.04)}
h1{font-size:2.4rem;color:#00ffaa;margin-bottom:6px}
.sub{color:#666;font-size:.85rem}
.filters{display:flex;justify-content:center;gap:8px;padding:16px;flex-wrap:wrap}
.fp{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);padding:6px 16px;border-radius:20px;font-size:.75rem;color:#888;cursor:pointer}
.fp.active,.fp:hover{border-color:#00ffaa;color:#00ffaa}
.sb{max-width:400px;margin:0 auto 20px;position:relative}
.sb input{width:100%;padding:12px 16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:#e0e0e2;font-size:.9rem;outline:none}
.sb input:focus{border-color:#00ffaa}
.container{max-width:1100px;margin:0 auto;padding:20px}
.stats{display:flex;justify-content:center;gap:20px;margin-bottom:20px}
.st{text-align:center;font-size:.7rem;color:#666}.st b{color:#00ffaa;font-size:1.3rem;display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:20px;transition:all .2s}
.card:hover{border-color:rgba(0,255,170,0.3);transform:translateY(-2px)}
.card h3{font-size:1rem;color:#e0e0e2;margin-bottom:4px}
.card .desc{color:#888;font-size:.8rem;margin-bottom:12px;min-height:36px}
.card .meta{display:flex;justify-content:space-between;align-items:center}
.badge{display:inline-block;padding:3px 10px;border-radius:8px;font-size:.65rem;font-weight:700}
.badge-free{background:rgba(0,255,170,0.15);color:#00ffaa}
.badge-x402{background:rgba(100,150,255,0.15);color:#6496ff}
.cat{display:inline-block;padding:2px 8px;border-radius:6px;font-size:.6rem;background:rgba(255,255,255,0.06);color:#666;margin-bottom:8px}
.btn{padding:6px 14px;border:none;border-radius:8px;cursor:pointer;font-size:.7rem;font-weight:700;background:#00ffaa;color:#0a0a1a}
.btn:hover{filter:brightness(1.1)}
.footer{text-align:center;padding:40px;color:#444;font-size:.75rem}
</style></head><body>
<div class="h"><h1>⚡ Skills Marketplace</h1><p class="sub">Open-source AI agent skills by Poke Labs — MIT Licensed</p></div>
<div class="stats"><div class="st"><b>""" + str(len(SKILLS)) + """</b>Skills</div><div class="st"><b>""" + str(len(CATS)) + """</b>Categories</div><div class="st"><b>100%</b>Open Source</div></div>
<div class="filters"><div class="fp active" onclick="filter('all')">All</div>""" + ''.join(f'<div class="fp" onclick="filter(\'{c}\')">{c.title()}</div>' for c in CATS) + """</div>
<div class="sb"><input type="text" id="search" placeholder="Search skills..." oninput="doSearch()"></div>
<div class="container"><div class="grid" id="grid"></div></div>
<div class="footer">2026 Poke Labs &middot; MIT License &middot; <a href="/api/skills" style="color:#00ffaa">JSON API</a></div>
<script>
const skills=""" + json.dumps(SKILLS) + """;
function render(skts){
  document.getElementById("grid").innerHTML=skts.map(s=>`
    <div class="card" data-cat="${s.cat}">
      <span class="cat">${s.cat}</span>
      <h3>${s.name}</h3>
      <div class="desc">${s.desc}</div>
      <div class="meta">
        <div>
          <span class="badge ${s.price==='free'?'badge-free':'badge-x402'}">${s.price}</span>
          <span style="color:#555;font-size:.65rem;margin-left:8px">v${s.ver}</span>
        </div>
        <button class="btn" onclick="install('${s.id}')">Install</button>
      </div>
    </div>
  `).join("")||'<div style="text-align:center;color:#555;padding:40px;grid-column:1/-1">No skills match your search</div>';
}
function filter(c){
  document.querySelectorAll('.fp').forEach(e=>e.classList.toggle('active',e.textContent.trim().toLowerCase()===(c==='all'?'all':c)));
  render(c==='all'?skills:skills.filter(s=>s.cat===c));
}
function doSearch(){
  const q=document.getElementById("search").value.toLowerCase();
  render(skills.filter(s=>s.name.toLowerCase().includes(q)||s.desc.toLowerCase().includes(q)||s.cat.includes(q)));
}
function install(id){
  fetch("/api/install",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id})}).then(r=>r.json()).then(d=>{
    alert(d.ok?`✅ ${d.skill} installed to /home/alx/skills/${d.skill}/`:(d.error||"Install failed"));
  });
}
render(skills);
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/": self._html(PAGE)
        elif p.path=="/api/skills": self._json({"skills":SKILLS,"total":len(SKILLS),"v":VERSION,"ts":time.time()})
        elif p.path=="/api/categories": self._json({"categories":CATS})
        elif p.path=="/api/health": self._json({"ok":True,"v":VERSION,"port":PORT,"skills":len(SKILLS)})
        else: self._json({"error":"not found"},404)

    def do_POST(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/api/install":
            try:
                body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
                sid=body.get("id","")
                skill=next((s for s in SKILLS if s["id"]),None)
                if not skill: self._json({"error":"skill not found"},404);return
                dest=os.path.join("/home/alx/skills",skill["id"])
                os.makedirs(dest,exist_ok=True)
                with open(os.path.join(dest,"SKILL.md"),"w") as f:
                    f.write(f"# {skill['name']}\n\n{skill['desc']}\n\nVersion: {skill['ver']}\nCategory: {skill['cat']}\n")
                self._json({"ok":True,"skill":skill["id"],"path":dest})
            except Exception as e: self._json({"error":str(e)},500)
        else: self._json({"error":"not found"},404)

    def _html(self,h,code=200):
        b=h.encode("utf-8");self.send_response(code)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def _json(self,d,code=200):
        b=json.dumps(d,default=str).encode();self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Skills Marketplace v{VERSION} on :{PORT}")
    s.serve_forever()
