#!/usr/bin/env python3
"""GitHub Trending Tracker v1.0 — Track trending repos over time."""

import http.server, json, urllib.request, urllib.parse, sqlite3, os, threading, time
from datetime import datetime, timedelta

PORT = int(os.environ.get("PORT", 8790))
DB_PATH = "/tmp/trending.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS trending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo TEXT NOT NULL,
        description TEXT,
        language TEXT,
        stars_today INTEGER,
        total_stars INTEGER,
        captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_repo ON trending(repo)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_date ON trending(captured_at)""")
    conn.commit()
    conn.close()

def fetch_trending(language=""):
    """Scrape GitHub trending page (no auth needed)."""
    try:
        lang_path = f"/{language}" if language else ""
        url = f"https://github.com/trending{lang_path}?since=daily"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; PokeBot/1.0)"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")

        repos = []
        # Parse article.Box-row blocks
        import re
        articles = re.findall(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', html, re.DOTALL)
        for art in articles:
            name_m = re.search(r'href="/([^/]+/[^/"]+)"', art)
            desc_m = re.search(r'<p[^>]*>(.*?)</p>', art, re.DOTALL)
            lang_m = re.search(r'<span[^>]*itemprop="programmingLanguage"[^>]*>(.*?)</span>', art)
            stars_m = re.search(r'<svg[^>]*class="octicon[^"]*star[^"]*".*?</svg>\s*([\d,]+)', art, re.DOTALL)
            total_m = re.search(r'href="/[^/]+/[^/"]+/stargazers".*?([\d,]+)', art, re.DOTALL)

            if name_m:
                name = name_m.group(1).strip()
                desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""
                lang = lang_m.group(1).strip() if lang_m else ""
                today_stars = int(stars_m.group(1).replace(",", "")) if stars_m else 0
                total = int(total_m.group(1).replace(",", "")) if total_m else 0
                repos.append({"repo": name, "description": desc, "language": lang,
                              "stars_today": today_stoday_stars, "total_stars": total})
        return repos
    except Exception as e:
        return []

def save_trending(repos):
    conn = sqlite3.connect(DB_PATH)
    for r in repos:
        conn.execute(
            "INSERT INTO trending (repo, description, language, stars_today, total_stars) VALUES (?,?,?,?,?)",
            (r["repo"], r.get("description",""), r.get("language",""),
             r.get("stars_today",0), r.get("total_stars",0))
        )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM trending").fetchone()[0]
    conn.close()
    return count

def get_trending(days=7, limit=30):
    conn = sqlite3.connect(DB_PATH)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        """SELECT repo, language, SUM(stars_today) as total_today, 
                  MAX(total_stars) as latest_stars, COUNT(*) as appearances
           FROM trending WHERE captured_at >= ?
           GROUP BY repo ORDER BY total_today DESC LIMIT ?""",
        (since, limit)
    ).fetchall()
    conn.close()
    return [{"repo": r[0], "language": r[1], "stars_gained": r[2],
             "total_stars_latest": r[3], "days_trending": r[4]} for r in rows]

def get_history(repo):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT stars_today, total_stars, captured_at FROM trending WHERE repo=? ORDER BY captured_at DESC LIMIT 30",
        (repo,)
    ).fetchall()
    conn.close()
    return [{"stars_today": r[0], "total_stars": r[1], "date": r[2]} for r in rows]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/":
            self.send_html(self.index_page())
        elif parsed.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "db": DB_PATH})
        elif parsed.path == "/api/trending":
            days = int(params.get("days", [7])[0])
            limit = int(params.get("limit", [30])[0])
            data = get_trending(days=days, limit=limit)
            self.send_json({"trending": data, "count": len(data), "days": days})
        elif parsed.path == "/api/history":
            repo = params.get("repo", [""])[0]
            if not repo:
                self.send_json({"error": "repo parameter required"}, 400)
            else:
                self.send_json({"repo": repo, "history": get_history(repo)})
        elif parsed.path == "/api/fetch":
            lang = params.get("language", [""])[0]
            repos = fetch_trending(lang)
            if repos:
                total = save_trending(repos)
                self.send_json({"fetched": len(repos), "total_records": total, "repos": [r["repo"] for r in repos[:10]]})
            else:
                self.send_json({"error": "fetch failed", "fetched": 0}, 500)
        else:
            self.send_json({"error": "not found"}, 404)

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

    def index_page(self):
        return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Trending Tracker</title>
<style>body{font-family:system-ui;background:#0a0a14;color:#c8c8d8;max-width:800px;margin:40px auto;padding:20px}
h1{color:#00d4ff}code{background:#111;padding:2px 8px;border-radius:4px}
a{color:#00d4ff}table{width:100%;border-collapse:collapse;margin:16px 0}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #1a1a2a}
th{color:#778;font-size:12px}
</style></head>
<body><h1>📈 Trending Tracker</h1>
<p>Track GitHub trending repos over time.</p>
<h2>API</h2>
<table>
<tr><th>Endpoint</th><th>Description</th></tr>
<tr><td><code>GET /api/health</code></td><td>Health check</td></tr>
<tr><td><code>GET /api/trending?days=7&limit=30</code></td><td>Top trending repos</td></tr>
<tr><td><code>GET /api/history?repo=owner/name</code></td><td>Repo trend history</td></tr>
<tr><td><code>GET /api/fetch?language=python</code></td><td>Fetch latest trending</td></tr>
</table>
<p>🫧 Built by Poke | <a href="/api/trending">Live Data</a></p>
</body></html>"""

if __name__ == "__main__":
    init_db()
    print(f"Trending Tracker v1.0 on port {PORT}")
    with http.server.HTTPServer(("", PORT), Handler) as s:
        s.serve_forever()
