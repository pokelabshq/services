#!/usr/bin/env python3
"""Release Tracker v1 — Monitor GitHub repos for new releases. Stdlib only."""

import http.server, json, sqlite3, os, datetime, urllib.request, urllib.error

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "releases.db")
PORT = 8782
TRACKED_REPOS = [
    "pokelabshq/council",
    "pokelabshq/pokelabs-site",
    "conway-research/automaton",
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS releases (
        id TEXT PRIMARY KEY, repo TEXT NOT NULL, tag TEXT NOT NULL,
        name TEXT, body TEXT, author TEXT, prerelease INTEGER DEFAULT 0,
        published_at TEXT, fetched_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, repo TEXT, status INTEGER,
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    return conn

def fetch_releases(repo):
    url = f"https://api.github.com/repos/{repo}/releases"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "PokeLabs-ReleaseTracker/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception:
        return None

def store_release(conn, repo, rel):
    rid = f"{repo}@{rel['tag_name']}"
    try:
        conn.execute(
            "INSERT OR IGNORE INTO releases(id,repo,tag,name,body,author,prerelease,published_at) VALUES (?,?,?,?,?,?,?,?)",
            (rid, repo, rel["tag_name"], rel.get("name",""), rel.get("body","")[:500],
             rel.get("author",{}).get("login",""), int(rel.get("prerelease",False)), rel.get("published_at","")))
    except sqlite3.IntegrityError:
        pass

def do_poll(conn):
    results = {}
    for repo in TRACKED_REPOS:
        data = fetch_releases(repo)
        if data:
            for rel in data:
                store_release(conn, repo, rel)
            conn.execute("INSERT INTO polls(repo,status) VALUES (?,?)", (repo, 200))
            results[repo] = len(data)
        else:
            conn.execute("INSERT INTO polls(repo,status) VALUES (?,?)", (repo, 0))
            results[repo] = 0
    conn.commit()
    return results

def get_all_releases(conn, limit=50):
    return conn.execute("SELECT repo,tag,name,author,prerelease,published_at,fetched_at FROM releases ORDER BY published_at DESC LIMIT ?",(limit,)).fetchall()

def get_latest_per_repo(conn):
    return conn.execute("""
        SELECT r.repo, r.tag, r.name, r.published_at, r.fetched_at
        FROM releases r INNER JOIN (
            SELECT repo, MAX(published_at) as max_date FROM releases GROUP BY repo
        ) latest ON r.repo=latest.repo AND r.published_at=latest.max_date""").fetchall()

def get_stats(conn):
    return {
        "tracked": conn.execute("SELECT COUNT(DISTINCT repo) FROM releases").fetchone()[0],
        "releases": conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0],
        "last_poll": conn.execute("SELECT MAX(fetched_at) FROM polls").fetchone()[0],
        "port": PORT
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        conn = init_db()
        try:
            if self.path in ("/", "/dashboard"):
                rels = get_all_releases(conn, 30)
                latest = get_latest_per_repo(conn)
                stats = get_stats(conn)
                lr = "".join(f"<tr><td><code>{r[0]}</code></td><td>{r[1]}</td><td>{r[2] or '-'}</td><td>{r[3]}</td></tr>" for r in latest)
                rr = "".join(f"<tr><td><code>{r[0]}</code></td><td>{'🟡' if r[4] else '🟢'} {r[1]}</td><td>{r[2] or '-'}</td><td>{r[3]}</td><td>{r[5][:10]}</td></tr>" for r in rels)
                html = f'''<!DOCTYPE html><html><head><title>Release Tracker</title>
<style>body{{font-family:system-ui;max-width:1000px;margin:0 auto;padding:20px;background:#0a0a0a;color:#eee}}
h1{{color:#ff6b35}}h2{{color:#4ecdc4}}.card{{background:#111;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #222}}th{{color:#ff6b35;font-size:.85em}}
tr:hover{{background:#161616}}code{{background:#222;padding:2px 6px;border-radius:4px}}</style></head><body>
<h1>🚀 Release Tracker</h1><div class="card">
Tracked: <strong>{stats["tracked"]}</strong> | Releases: <strong>{stats["releases"]}</strong> | Last poll: <strong>{stats["last_poll"] or "Never"}</strong></div>
<div class="card"><h2>Latest per Repo</h2><table><tr><th>Repo</th><th>Tag</th><th>Name</th><th>Published</th></tr>{lr}</table></div>
<div class="card"><h2>Recent Releases</h2><table><tr><th>Repo</th><th>Tag</th><th>Name</th><th>Author</th><th>Date</th></tr>{rr}</table></div>
<p style="color:#666;font-size:.8em">Poke Labs v1 | Port {PORT}</p></body></html>'''
                self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(html.encode())
            elif self.path == "/api/health":
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump({"ok":True,"v":1,"port":PORT,"name":"release-tracker"}, self.wfile)
            elif self.path == "/api/stats":
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump(get_stats(conn), self.wfile)
            elif self.path == "/api/poll":
                results = do_poll(conn)
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump({"polled": results}, self.wfile)
            elif self.path == "/api/releases":
                rels = get_all_releases(conn, 100)
                cols = ["repo","tag","name","author","prerelease","published_at","fetched_at"]
                data = [dict(zip(cols, r)) for r in rels]
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump(data, self.wfile)
            else:
                self.send_response(404); self.end_headers()
        finally:
            conn.close()
    def log_message(self, *_): pass

if __name__ == "__main__":
    init_db()
    srv = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Release Tracker on {PORT}")
    srv.serve_forever()
