#!/usr/bin/env python3
"""Skills Marketplace v2 — Dynamic skill browser for Poke Labs"""
import http.server, json, os, re, subprocess

PORT = int(os.environ.get("PORT", 8781))
REPO = "/home/alx/council"
SERVICES = "/home/alx/services"

def scan_skills():
    skills = []
    # Scan services dir for SKILL.md files
    if os.path.isdir(SERVICES):
        for name in sorted(os.listdir(SERVICES)):
            skill_md = os.path.join(SERVICES, name, "SKILL.md")
            server_py = os.path.join(SERVICES, name, "server.py")
            if not os.path.exists(skill_md) and not os.path.exists(server_py):
                continue
            desc, port, tags = "", 0, []
            if os.path.exists(skill_md):
                with open(skill_md) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            desc = line[:150]
                            break
                pm = re.search(r'[Pp]ort[:\s]+(\d{4,5})', open(skill_md).read())
                if pm: port = int(pm.group(1))
            if os.path.exists(server_py):
                tags.append("service")
                if not port:
                    pm = re.search(r'PORT\s*=\s*(\d{4,5})', open(server_py).read())
                    if pm: port = int(pm.group(1))
            skills.append({"name": name, "description": desc or f"{name} service", "port": port, "tags": tags or ["skill"]})
    return skills

def get_repos():
    try:
        r = subprocess.run(["gh", "api", "users/pokelabshq/repos", "--jq", ".[].full_name"],
                          capture_output=True, text=True, timeout=10)
        return [x.strip() for x in r.stdout.strip().split("\n") if x.strip()]
    except: return []

PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Labs — Skills Marketplace v2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}
.hdr{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:2rem;text-align:center;border-bottom:1px solid #2a2a4a}
.hdr h1{font-size:2.5rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr p{color:#888;margin-top:.5rem}
.sb{max-width:600px;margin:2rem auto;padding:0 1rem}
.sb input{width:100%;padding:.75rem 1rem;border:1px solid #333;border-radius:8px;background:#111;color:#fff;font-size:1rem;outline:none}
.sb input:focus{border-color:#7b2ff7}
.gr{max-width:1200px;margin:0 auto;padding:0 1rem 2rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem}
.card{background:#111;border:1px solid #222;border-radius:12px;padding:1.5rem;transition:transform .2s,border-color .2s}
.card:hover{transform:translateY(-2px);border-color:#7b2ff7}
.card h3{color:#00d4ff;margin-bottom:.5rem}
.card p{color:#999;font-size:.9rem;line-height:1.5}
.tags{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1rem}
.tag{background:#1a1a2e;padding:.25rem .5rem;border-radius:4px;font-size:.75rem;color:#7b2ff7}
.btn{margin-top:1rem;padding:.5rem 1rem;background:linear-gradient(90deg,#7b2ff7,#00d4ff);border:none;border-radius:6px;color:#fff;cursor:pointer;font-weight:600}
.btn:hover{opacity:.9}
.ft{text-align:center;padding:2rem;color:#555;border-top:1px solid #222}
.ft a{color:#7b2ff7;text-decoration:none}
</style></head><body>
<div class="hdr"><h1>🐾 Skills Marketplace v2</h1><p>__SKILL_COUNT__ skills across __REPO_COUNT__ repos</p></div>
<div class="sb"><input type="text" id="q" placeholder="Search skills..." oninput="flt()"></div>
<div class="gr" id="g"></div>
<div class="ft"><p>🐾 <a href="https://github.com/pokelabshq">Poke Labs on GitHub</a> · MIT Licensed</p></div>
<script>
const skills=__SKILLS__;
const g=document.getElementById('g');
function render(sk){
g.innerHTML=sk.map(s=>`<div class="card"><h3>${s.name}</h3><p>${s.description}</p><div class="tags">${s.tags.map(t=>`<span class="tag">${t}</span>`).join('')}</div><button class="btn" onclick="alert('Install: cat /home/alx/services/${s.name}/SKILL.md')">Install</button></div>`).join('');
}
function flt(){const q=document.getElementById('q').value.toLowerCase();render(skills.filter(s=>s.name.toLowerCase().includes(q)||s.description.toLowerCase().includes(q)));}
render(skills);
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=self.path.split("?")[0]
        if p=="/":
            s=scan_skills();rs=get_repos()
            page=PAGE.replace("__SKILLS__",json.dumps(s)).replace("__SKILL_COUNT__",str(len(s))).replace("__REPO_COUNT__",str(len(rs)))
            self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(page.encode())
        elif p=="/api/skills":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps(scan_skills()).encode())
        elif p=="/api/health":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps({"ok":True,"v":2,"skills":len(scan_skills())}).encode())
        else:self.send_response(404);self.end_headers()
    def log_message(self,*a):pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),H)
    print(f"Skills Marketplace v2 on port {PORT}")
    s.serve_forever()
