#!/usr/bin/env python3
"""Skills Marketplace v1.0 — Browse and install Poke Labs skills.
Port: 8781. Zero external deps. Serves HTML + JSON API."""
import http.server, json, os, re, urllib.request, urllib.error, html as html_mod

PORT = 8781
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
SERVICES_DIR = "/home/alx/services"

def scan_skills():
    skills = []
    try:
        for name in sorted(os.listdir(SERVICES_DIR)):
            skill_path = os.path.join(SERVICES_DIR, name)
            if not os.path.isdir(skill_path): continue
            md_path = os.path.join(skill_path, "SKILL.md")
            readme_path = os.path.join(skill_path, "README.md")
            desc = ""
            if os.path.exists(md_path):
                with open(md_path) as f:
                    content = f.read(500)
                    # Extract first meaningful line after title
                    for line in content.split("\n"):
                        line = line.strip()
                        if line and not line.startswith("#"):
                            desc = line[:120]
                            break
            elif os.path.exists(readme_path):
                with open(readme_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            desc = line[:120]
                            break
            # Detect category from content
            cat = "utility"
            content_lower = (desc + " " + name).lower()
            if any(k in content_lower for k in ["github", "pr", "issue", "webhook", "repo"]): cat = "github"
            elif any(k in content_lower for k in ["api", "http", "server", "endpoint", "rest"]): cat = "api"
            elif any(k in content_lower for k in ["web", "site", "landing", "page", "dashboard"]): cat = "web"
            elif any(k in content_lower for k in ["bot", "telegram", "discord", "social"]): cat = "social"
            elif any(k in content_lower for k in ["monitor", "health", "uptime", "status"]): cat = "monitoring"
            elif any(k in content_lower for k in ["data", "analytics", "stats", "metric"]): cat = "data"
            elif any(k in content_lower for k in ["ai", "ml", "model", "inference", "llm"]): cat = "ai"
            elif any(k in content_lower for k in ["pay", "wallet", "usdc", "x402", "crypto"]): cat = "finance"
            skills.append({"id": name, "name": name.replace("-", " ").title(), "description": desc or f"Poke Labs skill: {name}", "category": cat, "path": skill_path})
    except Exception as e:
        skills.append({"id": "error", "name": "Scan Error", "description": str(e), "category": "error", "path": ""})
    return skills

SKILLS = scan_skills()

def skill_detail(skill_id):
    for s in SKILLS:
        if s["id"] == skill_id:
            md_path = os.path.join(s["path"], "SKILL.md")
            if os.path.exists(md_path):
                with open(md_path) as f: s["full_readme"] = f.read()
            return s
    return None

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "skills": len(SKILLS), "wallet": WALLET})
        elif path == "/api/skills":
            cat = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("cat", [None])[0]
            result = [s for s in SKILLS if not cat or s["category"] == cat]
            self.send_json({"ok": True, "skills": result, "total": len(result), "categories": sorted(set(s["category"] for s in SKILLS))})
        elif path.startswith("/api/skill/"):
            sid = path[10:]
            detail = skill_detail(sid)
            if detail: self.send_json({"ok": True, "skill": detail})
            else: self.send_json({"error": "Not found"}, 404)
        elif path == "/":
            self.serve_homepage()
        else:
            self.send_json({"error": "Not found", "endpoints": ["/", "/api/health", "/api/skills", "/api/skills?cat=github", "/api/skill/<id>"]}, 404)

    def serve_homepage(self):
        cats = {}
        for s in SKILLS:
            cats.setdefault(s["category"], []).append(s)
        cat_order = sorted(cats.keys())
        sections = ""
        for cat in cat_order:
            items = cats[cat]
            cards = ""
            for s in items:
                desc_esc = html_mod.escape(s["description"][:100])
                name_esc = html_mod.escape(s["name"])
                cards += f'''<div class="card" onclick="location.href='/api/skill/{s["id"]}'">
                    <div class="card-cat">{s["category"]}</div>
                    <div class="card-title">{name_esc}</div>
                    <div class="card-desc">{desc_esc}</div>
                </div>'''
            sections += f'''<div class="cat-section">
                <h2 class="cat-title">{cat.title()} <span class="cat-count">({len(items)})</span></h2>
                <div class="grid">{cards}</div>
            </div>'''
        body = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Labs — Skills Marketplace</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}
.header{{padding:60px 20px 40px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(123,47,255,0.15) 0%,transparent 60%)}}
h1{{font-size:2.5rem;background:linear-gradient(135deg,#00d4ff,#7b2fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}}
.subtitle{{color:#888;font-size:1.1rem}}
.stats{{display:flex;justify-content:center;gap:32px;margin-top:24px;flex-wrap:wrap}}
.stat{{text-align:center}}.stat-n{{font-size:1.8rem;font-weight:700;color:#00d4ff}}.stat-l{{font-size:.75rem;color:#666;text-transform:letter-spacing:1px}}
.container{{max-width:1100px;margin:0 auto;padding:32px 20px}}
.cat-section{{margin-bottom:40px}}
.cat-title{{font-size:1.3rem;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.08)}}
.cat-count{{color:#666;font-size:.9rem;font-weight:400}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;cursor:pointer;transition:all .2s}}
.card:hover{{background:rgba(255,255,255,0.08);border-color:rgba(123,47,255,0.3);transform:translateY(-2px)}}
.card-cat{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.65rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;background:rgba(0,212,255,0.12);color:#00d4ff;margin-bottom:8px}}
.card-title{{font-size:1rem;font-weight:600;margin-bottom:6px}}
.card-desc{{color:#888;font-size:.85rem;line-height:1.4}}
.footer{{text-align:center;padding:40px 20px;color:#555;font-size:.85rem;border-top:1px solid rgba(255,255,255,0.05);margin-top:40px}}
</style></head><body>
<div class="header">
    <h1>🛍 Skills Marketplace</h1>
    <p class="subtitle">Browse and install open-source skills from Poke Labs</p>
    <div class="stats">
        <div class="stat"><div class="stat-n">{len(SKILLS)}</div><div class="stat-l">Skills</div></div>
        <div class="stat"><div class="stat-n">{len(cat_order)}</div><div class="stat-l">Categories</div></div>
        <div class="stat"><div class="stat-n">MIT</div><div class="stat-l">License</div></div>
    </div>
</div>
<div class="container">{sections}</div>
<div class="footer">Poke Labs © 2026 · MIT Licensed · Wallet: 0xca3d...6beF</div>
</body></html>'''
        self.send_response(200); self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body.encode())

    def send_json(self, d, code=200):
        body = json.dumps(d).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    import urllib.parse
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Skills Marketplace v1.0 on :{PORT} | {len(SKILLS)} skills")
    s.serve_forever()
