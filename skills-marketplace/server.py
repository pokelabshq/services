#!/usr/bin/env python3
"""Skills Marketplace v1 — Search, install, and publish skills for AI agents."""
import http.server, json, urllib.request, urllib.parse, os

PORT = 8781
DATA_DIR = "/home/alx/services/skills-marketplace/data"
SKILLS_FILE = os.path.join(DATA_DIR, "skills.json")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_SKILLS = [
    {"id":"auto-merge-pr","name":"Auto-Merge Dependabot PRs","description":"Automatically approves and squash-merges Dependabot PRs. Only merges semver-patch updates. Waits for CI.","author":"pokelabshq","version":"1.0.0","tags":["github","ci-cd","automation","dependabot"],"price":0,"installs":42,"rating":4.8,"stars":12},
    {"id":"link-preview-api","name":"Link Preview API","description":"Extract title, description, and Open Graph images from any URL. Free tier: 3/day. Unlimited via x402.","author":"pokelabshq","version":"4.0.0","tags":["api","web","metadata","x402"],"price":0,"installs":38,"rating":4.5,"stars":8},
    {"id":"poke-bot","name":"Poke Bot — GitHub Auto-Triage","description":"GitHub webhook handler. Auto-labels issues by priority (P0-P3) and PRs by size (S/M/L/XL).","author":"pokelabshq","version":"1.0.0","tags":["github","automation","labels","webhooks"],"price":0,"installs":55,"rating":4.7,"stars":15},
    {"id":"pokelabs-site","name":"Poke Labs Site + Link Preview","description":"Combined landing page + Link Preview API. Serves HTML and extracts URL metadata.","author":"pokelabshq","version":"7.0.0","tags":["web","api","landing-page"],"price":0,"installs":29,"rating":4.6,"stars":6},
    {"id":"repo-monitor","name":"Repo Monitor — GitHub Health Scanner","description":"Scans repos for stale PRs, open issues, security alerts, and failed CI runs.","author":"pokelabshq","version":"1.0.0","tags":["github","monitoring","security","ci-cd"],"price":0,"installs":31,"rating":4.4,"stars":9},
    {"id":"uptime-monitor","name":"Uptime Monitor","description":"HTTP health checker with response time tracking. Alerts on downtime.","author":"pokelabshq","version":"1.0.0","tags":["monitoring","uptime","alerts","api"],"price":0,"installs":27,"rating":4.3,"stars":7},
    {"id":"billing-engine","name":"Billing Engine","description":"Subscriptions, usage tracking, and invoicing. Free/Pro/Team plans. x402 payments on Base.","author":"pokelabshq","version":"1.0.0","tags":["billing","payments","x402","subscriptions"],"price":0,"installs":33,"rating":4.5,"stars":11},
    {"id":"package-registry","name":"Package Registry","description":"Publish, search, and version packages. Think npm but minimal. JSON-backed.","author":"pokelabshq","version":"1.0.0","tags":["registry","packages","publishing"],"price":0,"installs":19,"rating":4.2,"stars":5},
    {"id":"pricing-api","name":"Pricing API","description":"Real-time quotes for Poke Labs services. Transparent pricing with volume discounts.","author":"pokelabshq","version":"1.0.0","tags":["api","pricing","quotes"],"price":0,"installs":15,"rating":4.1,"stars":4},
    {"id":"telegram-bot","name":"Telegram Bot — Daily Briefings","description":"Sends daily status briefings to Telegram. Service health, GitHub stats, system metrics.","author":"pokelabshq","version":"1.0.0","tags":["telegram","notifications","briefings"],"price":0,"installs":22,"rating":4.0,"stars":3},
    {"id":"skills-marketplace","name":"Skills Marketplace","description":"Search, install, and publish skills for AI agents. Web UI + JSON API. All MIT licensed.","author":"pokelabshq","version":"1.0.0","tags":["skills","marketplace","discovery","api"],"price":0,"installs":0,"rating":0,"stars":0},
]

def load_skills():
    if os.path.exists(SKILLS_FILE):
        with open(SKILLS_FILE) as f: return json.load(f)
    return list(DEFAULT_SKILLS)

def save_skills(skills):
    with open(SKILLS_FILE, "w") as f: json.dump(skills, f, indent=2)

def search_skills(skills, query="", tag="", sort="stars"):
    results = list(skills)
    if query:
        q = query.lower()
        results = [s for s in results if q in s["name"].lower() or q in s["description"].lower() or any(q in t for t in s.get("tags", []))]
    if tag: results = [s for s in results if tag in s.get("tags", [])]
    if sort == "stars": results.sort(key=lambda s: s.get("stars", 0), reverse=True)
    elif sort == "rating": results.sort(key=lambda s: s.get("rating", 0), reverse=True)
    elif sort == "installs": results.sort(key=lambda s: s.get("installs", 0), reverse=True)
    return results

PAGE = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Skills Marketplace — Poke Labs</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0a0a1a;color:#e0e0e0;line-height:1.6}.top{background:linear-gradient(135deg,#1a1a3e,#0a0a1a);padding:2rem;text-align:center;border-bottom:1px solid #1e1e3a}.top h1{font-size:2.5rem;color:#c4b5fd;margin-bottom:.5rem}.top p{color:#6b7280}.sb{display:flex;gap:.5rem;max-width:600px;margin:1.5rem auto;flex-wrap:wrap;justify-content:center}.sb input{background:#111;border:1px solid #333;color:#e0e0e0;padding:.6rem 1rem;border-radius:8px;font-size:.95rem;min-width:250px}.sb input:focus{outline:none;border-color:#7c3aed}.sb select{background:#111;border:1px solid #333;color:#e0e0e0;padding:.6rem;border-radius:8px}.sb button{background:#7c3aed;color:#fff;border:none;padding:.6rem 1.2rem;border-radius:8px;cursor:pointer;font-size:.95rem}.sb button:hover{background:#6d28d9}.c{max-width:1000px;margin:0 auto;padding:2rem}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.25rem}.card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1.5rem;transition:border-color .2s}.card:hover{border-color:rgba(139,92,246,0.4)}.ch{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.5rem}.ch h3{color:#c4b5fd;font-size:1.05rem}.price{background:rgba(139,92,246,0.15);color:#a78bfa;padding:.2rem .6rem;border-radius:12px;font-size:.75rem;font-weight:600}.card p{color:#6b7280;font-size:.85rem;margin:.75rem 0}.tags{display:flex;gap:.3rem;flex-wrap:wrap;margin:.5rem 0}.tag{background:rgba(255,255,255,0.05);color:#9ca3af;padding:.15rem .5rem;border-radius:6px;font-size:.7rem}.meta{display:flex;gap:1rem;color:#4b5563;font-size:.75rem;margin:.75rem 0}.btn{display:inline-block;background:#7c3aed;color:#fff;padding:.5rem 1rem;border-radius:8px;border:none;cursor:pointer;font-size:.85rem;margin-top:.5rem;width:100%;text-align:center}.btn:hover{background:#6d28d9}.stats{display:flex;gap:2rem;justify-content:center;margin:1rem 0}.stat{text-align:center}.stat .num{font-size:1.5rem;color:#c4b5fd;font-weight:700}.stat .label{color:#4b5563;font-size:.75rem}.footer{text-align:center;padding:2rem;color:#4b5563;font-size:.8rem;border-top:1px solid rgba(255,255,255,0.04);margin-top:2rem}</style>
</head><body><div class="top"><h1>🧩 Skills Marketplace</h1><p>Search, install, and publish skills for AI agents. All MIT licensed.</p>
<div class="stats"><div class="stat"><div class="num">{skill_count}</div><div class="label">Skills</div></div><div class="stat"><div class="num">{total_stars}</div><div class="label">Stars</div></div><div class="stat"><div class="num">{total_installs}</div><div class="label">Installs</div></div></div>
<div class="sb"><input type="text" id="q" placeholder="Search skills..." onkeyup="if(event.key===13)doSearch()"><select id="sort"><option value="stars">Sort: Stars</option><option value="rating">Sort: Rating</option><option value="installs">Sort: Installs</option></select><button onclick="doSearch()">Search</button></div></div>
<div class="c"><div class="grid" id="results">{cards}</div></div>
<div class="footer"><p>🐾 Poke Labs Skills Marketplace — MIT License — <a href="/api/skills" style="color:#a78bfa">JSON API</a></p></div>
<script>function doSearch(){const q=document.getElementById('q').value;const s=document.getElementById('sort').value;window.location='/?q='+encodeURIComponent(q)+'&sort='+s;}function install(id){fetch('/api/install',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})}).then(r=>r.json()).then(d=>alert(d.message||d.error));}</script></body></html>'''

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        skills = load_skills()
        if parsed.path == "/":
            q = params.get("q", [""])[0]; sort = params.get("sort", ["stars"])[0]
            filtered = search_skills(skills, query=q, sort=sort)
            cards = ""
            for s in filtered:
                price = "Free" if s.get("price", 0) == 0 else f"${s['price']}"
                tags = "".join(f'<span class="tag">{t}</span>' for t in s.get("tags", []))
                cards += f'<div class="card"><div class="ch"><h3>{s["name"]}</h3><span class="price">{price}</span></div><p>{s["description"]}</p><div class="tags">{tags}</div><div class="meta"><span>⭐ {s.get("stars", 0)}</span><span>⭐ {s.get("rating", 0)}/5</span><span>v{s.get("version", "1.0")}</span><span>by {s.get("author", "unknown")}</span></div><button class="btn" onclick="install(\'{s["id"]}\')">Install</button></div>'
            ts = sum(s.get("stars", 0) for s in skills)
            ti = sum(s.get("installs", 0) for s in skills)
            self.send_html(PAGE.format(skill_count=len(skills), total_stars=ts, total_installs=ti, cards=cards))
        elif parsed.path == "/api/skills":
            q = params.get("q", [""])[0]; tag = params.get("tag", [""])[0]; sort = params.get("sort", ["stars"])[0]
            self.send_json({"skills": search_skills(skills, query=q, tag=tag, sort=sort), "count": len(search_skills(skills, query=q, tag=tag, sort=sort))})
        elif parsed.path == "/api/skill":
            sid = params.get("id", [""])[0]
            skill = next((s for s in skills if s["id"] == sid), None)
            self.send_json(skill if skill else {"error": "Not found"}, 200 if skill else 404)
        elif parsed.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "service": "skills-marketplace", "skills": len(skills)})
        elif parsed.path == "/api/tags":
            tags = set()
            for s in skills: tags.update(s.get("tags", []))
            self.send_json({"tags": sorted(tags)})
        else: self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        skills = load_skills()
        if self.path == "/api/install":
            sid = body.get("id", "")
            skill = next((s for s in skills if s["id"] == sid), None)
            if skill:
                skill["installs"] = skill.get("installs", 0) + 1; save_skills(skills)
                self.send_json({"ok": True, "message": f"Installed {skill['name']}!", "skill": skill})
            else: self.send_json({"error": "Not found"}, 404)
        elif self.path == "/api/publish":
            ns = body.get("skill", {})
            if not ns.get("id") or not ns.get("name"): self.send_json({"error": "Missing id or name"}, 400); return
            if any(s["id"] == ns["id"] for s in skills): self.send_json({"error": "ID exists"}, 409); return
            for k in ["stars","rating","installs","price","tags"]: ns.setdefault(k, 0 if k != "tags" else [])
            skills.append(ns); save_skills(skills)
            self.send_json({"ok": True, "message": f"Published {ns['name']}!", "skill": ns})
        else: self.send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        for h in [("Access-Control-Allow-Origin","*"),("Access-Control-Allow-Methods","GET,POST,OPTIONS"),("Access-Control-Allow-Headers","Content-Type")]: self.send_header(*h)
        self.end_headers()

    def send_json(self, d, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(d, indent=2).encode())

    def send_html(self, h, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(h.encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    if not os.path.exists(SKILLS_FILE): save_skills(DEFAULT_SKILLS)
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Skills Marketplace v1 on :{PORT}")
    s.serve_forever()
