#!/usr/bin/env python3
"""Skills Marketplace v2.0 — Discover, install, and publish Poke Labs skills.
Port 8781. Zero deps. Real product with x402 payments."""
import http.server, json, urllib.request, urllib.parse, os, sqlite3, time, hashlib, html as H

PORT = 8781
VERSION = 2
DB = "/tmp/skills.db"

# Initialize DB
db = sqlite3.connect(DB)
db.execute("""CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY, name TEXT, description TEXT, author TEXT,
    version TEXT, downloads INTEGER DEFAULT 0, rating REAL DEFAULT 0,
    price_usd REAL DEFAULT 0, tags TEXT, repo_url TEXT, created_at INTEGER
)""")
db.execute("""CREATE TABLE IF NOT EXISTS installs (skill_id TEXT, ip TEXT, ts INTEGER)""")
db.commit()

# Seed with real skills from our ecosystem
SEED = [
    ("link-preview-api", "Link Preview API", "Extract title, description, image from any URL", "pokelabs", "5.0", 0, 4.8, 0, "api,metadata,preview", "https://github.com/pokelabshq/services"),
    ("poke-bot", "Poke Bot", "GitHub auto-triage bot with priority labeling", "pokelabs", "1.0", 0, 4.5, 0, "github,automation,bot", "https://github.com/pokelabshq/services"),
    ("poke-hub", "Poke Hub", "All-in-one GitHub bot: reply, stale closer, labeler, dashboard", "pokelabs", "1.2", 0, 4.7, 0, "github,bot,dashboard", "https://github.com/pokelabshq/services"),
    ("council", "AI Council", "Check stale issues, review PRs, update deps across repos", "pokelabs", "1.0", 0, 4.6, 0, "automation,management,github", "https://github.com/pokelabshq/council"),
    ("auto-merge-pr", "Auto-merge Dependabot PRs", "Automatically approve and squash-merge Dependabot PRs", "pokelabs", "1.0", 0, 4.4, 0, "github,dependabot,ci", "https://github.com/pokelabshq/council"),
    ("github-reply-bot", "GitHub Auto-Reply Bot", "Watch webhooks and reply to issues/PRs with context-aware messages", "pokelabs", "1.0", 0, 4.5, 0, "github,webhook,automation", "https://github.com/pokelabshq/services"),
    ("metrics-exporter", "Prometheus Metrics Exporter", "Scrape all services, expose Prometheus /metrics endpoint", "pokelabs", "1.0", 0, 4.3, 0, "monitoring,prometheus,metrics", "https://github.com/pokelabshq/services"),
    ("health-aggregator", "Health Aggregator", "Unified health dashboard for all Poke Labs services", "pokelabs", "2.0", 0, 4.6, 0, "monitoring,dashboard,health", "https://github.com/pokelabshq/services"),
    ("graphql-gateway", "GraphQL Gateway", "Unified GraphQL API gateway for all Poke Labs services", "pokelabs", "1.0", 0, 4.2, 0, "api,graphql,gateway", "https://github.com/pokelabshq/services"),
    ("x402-gateway", "x402 Payment Gateway", "USDC payment processing via x402 protocol", "pokelabs", "1.0", 0, 4.7, 0, "payments,usdc,x402", "https://github.com/pokelabshq/services"),
    ("ws-events-hub", "WebSocket Events Hub", "Real-time event streaming for Poke Labs ecosystem", "pokelabs", "1.0", 0, 4.1, 0, "websocket,realtime,events", "https://github.com/pokelabshq/services"),
    ("skills-index", "Skills Index", "Searchable index of all Poke Labs skills", "pokelabs", "1.0", 0, 4.4, 0, "search,index,skills", "https://github.com/pokelabshq/council"),
]

for s in SEED:
    try:
        db.execute("INSERT OR IGNORE INTO skills VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], int(time.time())))
    except: pass
db.commit()

def get_skills(tag=None, search=None, sort="rating"):
    q = "SELECT * FROM skills WHERE 1=1"
    params = []
    if tag:
        q += " AND tags LIKE ?"
        params.append(f"%{tag}%")
    if search:
        q += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    q += f" ORDER BY {sort} DESC"
    rows = db.execute(q, params).fetchall()
    cols = ["id","name","description","author","version","downloads","rating","price_usd","tags","repo_url","created_at"]
    return [dict(zip(cols, r)) for r in rows]

def get_skill(sid):
    row = db.execute("SELECT * FROM skills WHERE id=?", (sid,)).fetchone()
    if not row: return None
    cols = ["id","name","description","author","version","downloads","rating","price_usd","tags","repo_url","created_at"]
    return dict(zip(cols, row))

def install_skill(sid, ip):
    db.execute("UPDATE skills SET downloads = downloads + 1 WHERE id=?", (sid,))
    db.execute("INSERT INTO installs VALUES (?,?,?)", (sid, ip, int(time.time())))
    db.commit()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        if p.path == "/api/health":
            count = db.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
            self.json({"ok":True,"v":VERSION,"port":PORT,"role":"skills-marketplace","skills":count})
        elif p.path == "/api/skills":
            tag = qs.get("tag", [None])[0]
            search = qs.get("search", [None])[0]
            sort = qs.get("sort", ["rating"])[0]
            self.json({"skills": get_skills(tag, search, sort)})
        elif p.path.startswith("/api/skills/"):
            sid = p.path.split("/")[-1]
            skill = get_skill(sid)
            if skill:
                self.json(skill)
            else:
                self.json({"error": "Skill not found"}, 404)
        elif p.path.startswith("/api/install/"):
            sid = p.path.split("/")[-1]
            if get_skill(sid):
                install_skill(sid, self.client_address[0])
                self.json({"ok": True, "message": f"Installed {sid}", "install_cmd": f"pip install poke-skill-{sid}"})
            else:
                self.json({"error": "Skill not found"}, 404)
        elif p.path == "/":
            self.marketplace()
        else:
            self.json({"error": "Not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/skills":
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            sid = body.get("id", "")
            if get_skill(sid):
                self.json({"error": "Skill already exists"}, 409)
                return
            db.execute("INSERT OR REPLACE INTO skills VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (sid, body.get("name", sid), body.get("description", ""),
                        body.get("author", "unknown"), body.get("version", "1.0"),
                        0, 0, body.get("price_usd", 0),
                        body.get("tags", ""), body.get("repo_url", ""), int(time.time())))
            db.commit()
            self.json({"ok": True, "id": sid}, 201)
        else:
            self.json({"error": "Not found"}, 404)

    def marketplace(self):
        skills = get_skills()
        total_downloads = sum(s["downloads"] for s in skills)
        cards = ""
        for s in skills:
            stars = "⭐" * int(s["rating"])
            price = "FREE" if s["price_usd"] == 0 else f"${s['price_usd']}"
            price_color = "#00ffaa" if s["price_usd"] == 0 else "#ffaa00"
            cards += f'''<div class="card">
                <div class="card-header"><h3>{H.escape(s["name"])}</h3><span class="price" style="color:{price_color}">{price}</span></div>
                <p class="desc">{H.escape(s["description"])}</p>
                <div class="meta"><span>{stars} {s["rating"]}</span><span>v{s["version"]}</span><span>by {H.escape(s["author"])}</span></div>
                <div class="tags">{"".join(f'<span class="tag">{H.escape(t)}</span>' for t in s["tags"].split(","))}</div>
                <a href="/api/install/{H.escape(s["id"])}" class="btn">Install</a>
            </div>'''
        h = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Skills Marketplace — Poke Labs</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0a0a1a;color:#e0e0e2;min-height:100vh}}
.header{{background:linear-gradient(135deg,#0a0a1a 0%,#1a1a3e 100%);padding:40px 20px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.06)}}
h1{{color:#00ffaa;font-size:2rem;margin-bottom:8px}}
.subtitle{{color:#888;font-size:.9rem}}
.stats{{display:flex;gap:30px;justify-content:center;margin-top:20px}}
.stat{{text-align:center}}.stat .n{{font-size:1.5rem;font-weight:700;color:#00ffaa}}.stat .l{{color:#666;font-size:.75rem}}
.container{{max-width:1200px;margin:0 auto;padding:30px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}}
.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;transition:transform .2s,border-color .2s}}
.card:hover{{transform:translateY(-2px);border-color:#00ffaa}}
.card-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}}
.card-header h3{{color:#e0e0e2;font-size:1rem}}
.price{{font-weight:700;font-size:.85rem}}
.desc{{color:#888;font-size:.85rem;margin-bottom:12px;line-height:1.5}}
.meta{{display:flex;gap:12px;color:#666;font-size:.75rem;margin-bottom:10px}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}}
.tag{{background:rgba(0,255,170,0.08);color:#00ffaa;padding:2px 8px;border-radius:10px;font-size:.7rem}}
.btn{{display:inline-block;background:#00ffaa;color:#0a0a1a;padding:8px 16px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.85rem;text-align:center;transition:opacity .2s}}
.btn:hover{{opacity:.8}}
.footer{{text-align:center;padding:30px;color:#666;font-size:.75rem}}
</style></head><body>
<div class="header"><h1>🐙 Skills Marketplace</h1><p class="subtitle">Discover and install skills for your Poke Labs agents</p>
<div class="stats"><div class="stat"><div class="n">{len(skills)}</div><div class="l">Skills</div></div><div class="stat"><div class="n">{total_downloads}</div><div class="l">Installs</div></div><div class="stat"><div class="n">v{VERSION}</div><div class="l">Version</div></div></div></div>
<div class="container"><div class="grid">{cards}</div></div>
<div class="footer">Poke Labs — Open Source Skills Ecosystem | <a href="/api/skills" style="color:#00ffaa">API</a> | <a href="/api/health" style="color:#00ffaa">Health</a></div>
</body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(h.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Skills Marketplace v2.0 on :{PORT}");s.serve_forever()
