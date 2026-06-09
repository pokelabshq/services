#!/usr/bin/env python3
"""
GitHub Trending Tracker v1.0
Scrapes GitHub trending repos, stores in SQLite, exposes API.
Pure Python stdlib. Zero deps.

Usage: python3 github-trending/tracker.py &
API: http://localhost:8788/
"""
import http.server, json, sqlite3, os, re, threading, time
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 8788
DB_PATH = "/tmp/github-trending.db"
SCRAPE_INTERVAL = 3600  # 1 hour

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo TEXT NOT NULL,
            description TEXT,
            language TEXT,
            stars INTEGER,
            forks INTEGER,
            stars_today INTEGER,
            date TEXT NOT NULL,
            scraped_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON trending(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_repo ON trending(repo)")
    conn.commit()
    return conn

def scrape_trending():
    """Scrape GitHub trending page."""
    url = "https://github.com/trending"
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    })
    try:
        r = urlopen(req, timeout=15)
        html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ Scrape failed: {e}")
        return []
    
    repos = []
    # Parse trending repos from HTML
    pattern = r'href="/([^"]+)"[^>]*>\s*<[^>]*>\s*([^<]+)</[^>]*>.*?<p[^>]*>(.*?)</p>.*?<span[^>]*>([^<]+)</span>.*?(\d[\d,]*)\s*stars.*?(\d[\d,]*)\s*forks'
    
    # Simpler approach: extract repo names and descriptions
    repo_blocks = re.findall(
        r'href="/([^/"]+/[^/"]+)"[^>]*class="[^"]*Link[^"]*"[^>]*>(.*?)</a>.*?<p[^>]*>(.*?)</p>',
        html, re.DOTALL
    )
    
    for match in re.finditer(
        r'href="/([^/"]+/[^/"]+)"[^>]*>\s*<[^>]*>\s*([^<]+)</[^>]*>.*?<p[^>]*>(.*?)</p>',
        html, re.DOTALL
    ):
        repo_path = match.group(1).strip()
        name = match.group(2).strip()
        desc = match.group(3).strip()
        
        # Skip if it's not a repo link
        if "/" not in repo_path or len(repo_path.split("/")) != 2:
            continue
        
        repos.append({
            "repo": repo_path,
            "description": desc[:200] if desc else "",
            "language": "",
            "stars": 0,
            "forks": 0,
            "stars_today": 0
        })
    
    # Also try to get language and star info
    star_pattern = r'href="/([^/"]+/[^/"]+)".*?<span[^>]*d-inline[^>]*>([^<]+)</span>.*?(\d[\d,]*)\s*stars today'
    for match in re.finditer(star_pattern, html, re.DOTALL):
        repo_path = match.group(1)
        stars_today_str = match.group(3).replace(",", "")
        try:
            stars_today = int(stars_today_str)
        except:
            stars_today = 0
        for r in repos:
            if r["repo"] == repo_path:
                r["stars_today"] = stars_today
    
    return repos[:25]  # Top 25

def save_repos(repos):
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().isoformat()[:10]
    now = datetime.now().isoformat()
    for r in repos:
        conn.execute(
            "INSERT INTO trending (repo, description, language, stars, forks, stars_today, date, scraped_at) VALUES (?,?,?,?,?,?,?,?)",
            (r["repo"], r["description"], r["language"], r["stars"], r["forks"], r["stars_today"], today, now)
        )
    conn.commit()
    conn.close()

def get_trending(days=1, limit=25):
    conn = sqlite3.connect(DB_PATH)
    since = (datetime.now() - timedelta(days=days)).isoformat()[:10]
    rows = conn.execute(
        "SELECT repo, description, language, stars, forks, stars_today, date FROM trending WHERE date >= ? GROUP BY repo ORDER BY stars_today DESC, stars DESC LIMIT ?",
        (since, limit)
    ).fetchall()
    conn.close()
    return [dict(zip(["repo","description","language","stars","forks","stars_today","date"], r)) for r in rows]

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM trending").fetchone()[0]
    repos = conn.execute("SELECT COUNT(DISTINCT repo) FROM trending").fetchone()[0]
    days = conn.execute("SELECT COUNT(DISTINCT date) FROM trending").fetchone()[0]
    latest = conn.execute("SELECT MAX(date) FROM trending").fetchone()[0]
    top = conn.execute("SELECT repo, SUM(stars_today) as total FROM trending GROUP BY repo ORDER BY total DESC LIMIT 5").fetchall()
    conn.close()
    return {"total_records": total, "unique_repos": repos, "days_tracked": days, "latest_scrape": latest, "top_repos": top}

def scrape_loop():
    while True:
        print(f"🔄 Scraping GitHub trending at {datetime.now().isoformat()[:19]}...")
        repos = scrape_trending()
        if repos:
            save_repos(repos)
            print(f"✅ Saved {len(repos)} trending repos")
        else:
            print("⚠️ No repos scraped")
        time.sleep(SCRAPE_INTERVAL)

class TrendingHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.send_html(self.dashboard())
        elif self.path == '/api/trending':
            days = int(self.path.split("days=")[1].split("&")[0]) if "days=" in self.path else 1
            self.send_json(get_trending(days=days))
        elif self.path == '/api/stats':
            self.send_json(get_stats())
        elif self.path == '/api/scrape':
            repos = scrape_trending()
            if repos:
                save_repos(repos)
            self.send_json({"ok": True, "count": len(repos)})
        elif self.path == '/api/health':
            self.send_json({"ok": True, "v": 1, "port": PORT})
        else:
            self.send_response(404); self.end_headers()
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def dashboard(self):
        trending = get_trending(7, 25)
        stats = get_stats()
        rows = ""
        for r in trending:
            sd = r['stars_today'] or '?'
            rows += f'<tr><td><a href="https://github.com/{r["repo"]}" style="color:#a78bfa">{r["repo"]}</a></td><td>{r["description"][:80]}</td><td>{r["language"] or "?"}</td><td>{sd}</td></tr>'
        return f'''<!DOCTYPE html>
<html><head><title>🐾 GitHub Trending</title>
<style>
body{{font-family:system-ui,monospace;max-width:900px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
h1{{color:#a78bfa}}table{{width:100%;border-collapse:collapse;margin:10px 0}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #333}}
th{{color:#a78bfa}}.card{{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px;margin:10px 0}}
a{{color:#a78bfa;text-decoration:none}}
</style></head>
<body>
<h1>🐾 GitHub Trending Tracker</h1>
<div class="card">
📊 Stats: {stats['total_records']} records | {stats['unique_repos']} unique repos | {stats['days_tracked']} days tracked
| Latest: {stats['latest_scrape'] or 'Never'}
</div>
<h2>Trending (Last 7 Days)</h2>
<table><tr><th>Repo</th><th>Description</th><th>Language</th><th>Stars Today</th></tr>
{rows}
</table>
<p><a href="/api/trending">API</a> | <a href="/api/stats">Stats</a> | <a href="/api/scrape">Trigger Scrape</a></p>
</body></html>'''
    
    def log_message(self, *a): pass

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=scrape_loop, daemon=True)
    t.start()
    s = http.server.HTTPServer(('0.0.0.0', PORT), TrendingHandler)
    print(f"🐾 GitHub Trending Tracker: http://localhost:{PORT}/", flush=True)
    s.serve_forever()
