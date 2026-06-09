#!/usr/bin/env python3
"""
Poke Labs Skill Marketplace v2.0
Discover, install, rate, and publish AI agent skills.
Pure Python stdlib. Zero deps.

Skill format:
{
  "id": "unique-id",
  "name": "Human Name",
  "description": "What it does",
  "author": "0x... or name",
  "version": "1.0.0",
  "tags": ["github", "automation"],
  "rating": 4.5,
  "ratings_count": 42,
  "installs": 1337,
  "price_usdc": 0,
  "content": "# SKILL_NAME\n..."
}

Usage: python3 skill-marketplace-v2/marketplace.py &
API: http://localhost:8790/
"""
import http.server, json, sqlite3, os, hashlib, re, time
from datetime import datetime

PORT = 8790
DB_PATH = "/tmp/skill-marketplace.db"
DATA_DIR = "/tmp/skill-marketplace-data"

os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            author TEXT,
            version TEXT DEFAULT '1.0.0',
            tags TEXT DEFAULT '[]',
            rating REAL DEFAULT 0,
            ratings_count INTEGER DEFAULT 0,
            installs INTEGER DEFAULT 0,
            price_usdc REAL DEFAULT 0,
            content TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ratings (
            skill_id TEXT,
            rater TEXT,
            score INTEGER CHECK(score >= 1 AND score <= 5),
            comment TEXT,
            created_at TEXT,
            FOREIGN KEY(skill_id) REFERENCES skills(id),
            UNIQUE(skill_id, rater)
        );
        CREATE INDEX IF NOT EXISTS idx_skills_rating ON skills(rating DESC);
        CREATE INDEX IF NOT EXISTS idx_skills_installs ON skills(installs DESC);
        CREATE INDEX IF NOT EXISTS idx_skills_tags ON skills(tags);
    """)
    conn.commit()
    return conn

def seed_sample_data():
    """Seed with sample skills if empty."""
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    if count > 0:
        conn.close()
        return
    
    now = datetime.now().isoformat()
    sample_skills = [
        {
            "id": "github-auto-reply",
            "name": "GitHub Auto-Reply",
            "description": "Auto-reply to GitHub issues and PRs with context-aware messages",
            "author": "pokelabshq",
            "version": "1.0.0",
            "tags": json.dumps(["github", "automation", "communication"]),
            "rating": 4.5, "ratings_count": 12, "installs": 234,
            "price_usdc": 0,
            "content": "# GitHub Auto-Reply Skill\n\nAuto-replies to GitHub issues and PRs.\n\n## Usage\nConfigure webhook to point to /webhook endpoint.\n\n## Features\n- Bug reports → asks for repro\n- Feature requests → asks for use case\n- PRs → thanks + checklist"
        },
        {
            "id": "link-preview",
            "name": "Link Preview API",
            "description": "Extract title, description, image from any URL with x402 billing",
            "author": "pokelabshq",
            "version": "4.0.0",
            "tags": json.dumps(["web", "api", "x402", "revenue"]),
            "rating": 4.8, "ratings_count": 28, "installs": 567,
            "price_usdc": 0,
            "content": "# Link Preview API\n\nExtract metadata from URLs.\n\n## API\nPOST /api/preview {\"url\": \"https://...\"}\n\n## Free tier: 3/day. Unlimited via x402."
        },
        {
            "id": "daily-digest",
            "name": "Daily Digest Generator",
            "description": "Scan GitHub repos and generate formatted morning briefings",
            "author": "pokelabshq",
            "version": "1.0.0",
            "tags": json.dumps(["github", "reporting", "automation"]),
            "rating": 4.2, "ratings_count": 8, "installs": 189,
            "price_usdc": 0,
            "content": "# Daily Digest Generator\n\nScans GitHub repos and generates morning briefings.\n\n## Usage\n```bash\npython3 digest.py --output briefing.txt\n```"
        },
        {
            "id": "revenue-tracker",
            "name": "Revenue Tracker",
            "description": "Track x402 payments and earnings across all your services",
            "author": "pokelabshq",
            "version": "1.0.0",
            "tags": json.dumps(["revenue", "x402", "analytics"]),
            "rating": 4.0, "ratings_count": 3, "installs": 91,
            "price_usdc": 0.001,
            "content": "# Revenue Tracker\n\nTracks x402 payments across services.\n\n## API\nGET /api/revenue - Revenue stats\nPOST /api/record - Record payment"
        },
        {
            "id": "service-watchdog",
            "name": "Service Watchdog",
            "description": "Monitor and auto-restart crashed microservices with web dashboard",
            "author": "pokelabshq",
            "version": "1.0.0",
            "tags": json.dumps(["monitoring", "ops", "automation"]),
            "rating": 4.7, "ratings_count": 15, "installs": 312,
            "price_usdc": 0,
            "content": "# Service Watchdog\n\nMonitors services and auto-restarts crashed ones.\n\n## Usage\n```bash\npython3 watchdog.py &\n```"
        },
        {
            "id": "auto-merge",
            "name": "Auto-Merge Dependabot",
            "description": "Automatically approve and squash-merge Dependabot PRs",
            "author": "pokelabshq",
            "version": "1.0.0",
            "tags": json.dumps(["github", "ci-cd", "automation"]),
            "rating": 4.9, "ratings_count": 34, "installs": 891,
            "price_usdc": 0,
            "content": "# Auto-Merge Dependabot\n\nAuto-approves and merges Dependabot PRs.\n\n## Setup\nAdd workflow to .github/workflows/auto-merge.yml"
        },
    ]
    
    for s in sample_skills:
        conn.execute("""
            INSERT OR IGNORE INTO skills (id, name, description, author, version, tags, rating, ratings_count, installs, price_usdc, content, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (s["id"], s["name"], s["description"], s["author"], s["version"], s["tags"], s["rating"], s["ratings_count"], s["installs"], s["price_usdc"], s["content"], now, now))
    conn.commit()
    conn.close()

class MarketplaceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        params = {}
        if "?" in self.path:
            for kv in self.path.split("?")[1].split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[k] = v
        
        if path == "/":
            self.send_html(self.dashboard())
        elif path == "/api/skills":
            self.api_list_skills(params)
        elif path == "/api/health":
            self.send_json({"ok": True, "v": 2, "port": PORT})
        elif path.startswith("/api/skills/"):
            skill_id = path.split("/api/skills/")[1]
            self.api_get_skill(skill_id)
        elif path == "/api/categories":
            self.api_categories()
        elif path == "/api/trending":
            self.api_trending()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        
        if path == "/api/skills":
            self.api_publish(body)
        elif path.startswith("/api/skills/") and path.endswith("/rate"):
            skill_id = path.split("/api/skills/")[1].split("/rate")[0]
            self.api_rate(skill_id, body)
        elif path.startswith("/api/skills/") and path.endswith("/install"):
            skill_id = path.split("/api/skills/")[1].split("/install")[0]
            self.api_install(skill_id)
        else:
            self.send_response(404); self.end_headers()
    
    def api_list_skills(self, params):
        conn = sqlite3.connect(DB_PATH)
        sort = params.get("sort", "rating")
        tag = params.get("tag", "")
        limit = int(params.get("limit", 50))
        q = params.get("q", "")
        
        query = "SELECT id, name, description, author, version, tags, rating, ratings_count, installs, price_usdc, created_at FROM skills WHERE 1=1"
        args = []
        if tag:
            query += " AND tags LIKE ?"
            args.append(f"%{tag}%")
        if q:
            query += " AND (name LIKE ? OR description LIKE ?)"
            args.extend([f"%{q}%", f"%{q}%"])
        
        if sort == "installs":
            query += " ORDER BY installs DESC"
        elif sort == "newest":
            query += " ORDER BY created_at DESC"
        else:
            query += " ORDER BY rating DESC"
        query += f" LIMIT {limit}"
        
        rows = conn.execute(query, args).fetchall()
        conn.close()
        skills = [dict(zip(["id","name","description","author","version","tags","rating","ratings_count","installs","price_usdc","created_at"], r)) for r in rows]
        for s in skills:
            s["tags"] = json.loads(s["tags"])
        self.send_json({"skills": skills, "count": len(skills)})
    
    def api_get_skill(self, skill_id):
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT * FROM skills WHERE id=?", (skill_id,)).fetchone()
        conn.close()
        if not row:
            self.send_json({"error": "Skill not found"}); return
        cols = ["id","name","description","author","version","tags","rating","ratings_count","installs","price_usdc","content","created_at","updated_at"]
        skill = dict(zip(cols, row))
        skill["tags"] = json.loads(skill["tags"])
        self.send_json(skill)
    
    def api_publish(self, body):
        skill_id = body.get("id", "").strip().lower().replace(" ", "-")
        if not skill_id:
            self.send_json({"error": "Missing skill id"}); return
        now = datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT OR REPLACE INTO skills (id, name, description, author, version, tags, rating, ratings_count, installs, price_usdc, content, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            skill_id, body.get("name", skill_id), body.get("description", ""),
            body.get("author", "anonymous"), body.get("version", "1.0.0"),
            json.dumps(body.get("tags", [])), 0, 0, 0,
            body.get("price_usdc", 0), body.get("content", ""),
            now, now
        ))
        conn.commit()
        conn.close()
        self.send_json({"ok": True, "id": skill_id})
    
    def api_rate(self, skill_id, body):
        rater = body.get("rater", "anonymous")
        score = int(body.get("score", 0))
        if score < 1 or score > 5:
            self.send_json({"error": "Score must be 1-5"}); return
        now = datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO ratings (skill_id, rater, score, comment, created_at) VALUES (?,?,?,?,?)",
                     (skill_id, rater, score, body.get("comment", ""), now))
        avg = conn.execute("SELECT AVG(score), COUNT(*) FROM ratings WHERE skill_id=?", (skill_id,)).fetchone()
        conn.execute("UPDATE skills SET rating=?, ratings_count=?, updated_at=? WHERE id=?",
                     (round(avg[0], 2), avg[1], now, skill_id))
        conn.commit()
        conn.close()
        self.send_json({"ok": True, "skill_id": skill_id, "new_rating": round(avg[0], 2)})
    
    def api_install(self, skill_id):
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT content, price_usdc FROM skills WHERE id=?", (skill_id,)).fetchone()
        if not row:
            self.send_json({"error": "Skill not found"}); return
        content, price = row
        if price > 0:
            self.send_json({"error": f"Skill costs {price} USDC. Payment required.", "price_usdc": price}); return
        conn.execute("UPDATE skills SET installs=installs+1, updated_at=? WHERE id=?", (datetime.now().isoformat(), skill_id))
        conn.commit()
        conn.close()
        self.send_json({"ok": True, "content": content})
    
    def api_categories(self):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT tags FROM skills").fetchall()
        conn.close()
        cats = {}
        for r in rows:
            for t in json.loads(r[0]):
                cats[t] = cats.get(t, 0) + 1
        self.send_json({"categories": sorted(cats.items(), key=lambda x: -x[1])})
    
    def api_trending(self):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT id, name, installs, rating FROM skills ORDER BY installs DESC LIMIT 10").fetchall()
        conn.close()
        self.send_json({"trending": [dict(zip(["id","name","installs","rating"], r)) for r in rows]})
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def dashboard(self):
        conn = sqlite3.connect(DB_PATH)
        total_skills = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        total_installs = conn.execute("SELECT SUM(installs) FROM skills").fetchone()[0]
        free_count = conn.execute("SELECT COUNT(*) FROM skills WHERE price_usdc=0").fetchone()[0]
        paid_count = conn.execute("SELECT COUNT(*) FROM skills WHERE price_usdc>0").fetchone()[0]
        top = conn.execute("SELECT id, name, description, rating, installs, price_usdc, tags FROM skills ORDER BY rating DESC LIMIT 6").fetchall()
        conn.close()
        
        cards = ""
        for r in top:
            sid, name, desc, rating, installs, price, tags = r
            tag_list = json.loads(tags)
            tag_html = "".join(f'<span style="background:#2a2a4a;padding:2px 8px;border-radius:4px;margin-right:4px;font-size:0.8em">{t}</span>' for t in tag_list[:3])
            price_str = "FREE" if price == 0 else f"{price} USDC"
            cards += f'''<div style="background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:8px 0">
<div style="display:flex;justify-content:space-between"><b style="color:#a78bfa">{name}</b><span style="color:#{"22c55e" if price==0 else "f59e0b"}">{price_str}</span></div>
<p style="color:#aaa;font-size:0.9em">{desc[:100]}</p>
<div>{tag_html}</div>
<div style="margin-top:8px;color:#888;font-size:0.8em">⭐ {rating} | 📦 {installs} installs</div>
</div>'''
        
        return f'''<!DOCTYPE html>
<html><head><title>🐾 Skill Marketplace</title>
<style>
body{{font-family:system-ui,monospace;max-width:800px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
h1{{color:#a78bfa}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
a{{color:#a78bfa}}
</style></head>
<body>
<h1>🐾 Poke Labs Skill Marketplace v2</h1>
<div class="grid">
<div style="background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:8px 0">
📊 <b>{total_skills}</b> skills | <b>{total_installs or 0}</b> installs<br>
🆓 {free_skills} free | 💰 {paid_count} paid
</div>
<div style="background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:8px 0">
🔌 <b>Install</b><br><code>/api/skills/&lt;id&gt;/install</code><br>
📝 <b>Publish</b><br><code>POST /api/skills</code><br>
⭐ <b>Rate</b><br><code>POST /api/skills/&lt;id&gt;/rate</code>
</div>
</div>
<h2>Top Rated Skills</h2>
{cards}
<p style="margin-top:20px;text-align:center;color:#666"><a href="/api/skills">Browse API</a> | <a href="/api/trending">Trending</a> | <a href="/api/categories">Categories</a></p>
<p style="text-align:center;color:#444;font-size:0.8em">Skills are SKILL.md format. Free to publish via API.</p>
</body></html>'''
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    init_db()
    seed_sample_data()
    s = http.server.HTTPServer(("0.0.0.0", PORT), MarketplaceHandler)
    print(f"🐾 Skill Marketplace v2: http://localhost:{PORT}/", flush=True)
    s.serve_forever()
