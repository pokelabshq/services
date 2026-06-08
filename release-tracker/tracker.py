#!/usr/bin/env python3
"""
Release Tracker v1 — Monitor GitHub repos for new releases.
Tracks watched repos, detects new releases, maintains changelog.
Stdlib only. Port 8782.
"""
import http.server, json, sqlite3, os, urllib.request, urllib.error, datetime

PORT = 8782
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "releases.db")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

DEFAULT_REPOS = [
    "pokelabshq/council",
    "pokelabshq/cli",
    "conway-research/automaton",
]

def gh_api(url):
    req = urllib.request.Request(url)
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS repos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT UNIQUE, display_name TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS releases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_id INTEGER, tag_name TEXT, name TEXT,
        body TEXT, published_at TEXT, html_url TEXT,
        detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(repo_id) REFERENCES repos(id))""")
    for r in DEFAULT_REPOS:
        conn.execute("INSERT OR IGNORE INTO repos(full_name, display_name) VALUES (?,?)", (r, r.split("/")[1]))
    conn.commit()
    return conn

def check_releases(conn, repo_name):
    data = gh_api(f"https://api.github.com/repos/{repo_name}/releases/latest")
    if "error" in data or "tag_name" not in data:
        return None
    row = conn.execute("SELECT id FROM repos WHERE full_name=?", (repo_name,)).fetchone()
    if not row:
        conn.execute("INSERT INTO repos(full_name, display_name) VALUES (?,?)",
                     (repo_name, repo_name.split("/")[1]))
        repo_id = conn.execute("SELECT id FROM repos WHERE full_name=?", (repo_name,)).fetchone()[0]
    else:
        repo_id = row[0]
    existing = conn.execute("SELECT id FROM releases WHERE repo_id=? AND tag_name=?",
                            (repo_id, data["tag_name"])).fetchone()
    if not existing:
        conn.execute("""INSERT INTO releases(repo_id, tag_name, name, body, published_at, html_url)
            VALUES (?,?,?,?,?,?)""",
            (repo_id, data["tag_name"], data.get("name",""), data.get("body","")[:2000],
             data.get("published_at",""), data.get("html_url","")))
        conn.commit()
        return {"new": True, "tag": data["tag_name"], "repo": repo_name}
    return {"new": False, "tag": data["tag_name"], "repo": repo_name}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        conn = init_db()
        try:
            path = self.path.split("?")[0]
            if path in ("/", "/dashboard"):
                repos = conn.execute("SELECT r.full_name, r.display_name, r.added_at, COUNT(rel.id) as cnt FROM repos r LEFT JOIN releases rel ON rel.repo_id=r.id GROUP BY r.id ORDER BY r.added_at").fetchall()
                recent = conn.execute("""SELECT rel.tag_name, rel.name, rel.published_at, rel.html_url, r.full_name
                    FROM releases rel JOIN repos r ON rel.repo_id=r.id ORDER BY rel.detected_at DESC LIMIT 20""").fetchall()
                repo_rows = "".join(
                    f'<tr><td><a href="https://github.com/{r[0]}" style="color:#4ecdc4">{r[0]}</a></td>'
                    f'<td>{r[1]}</td><td>{r[3]}</td><td>{r[2][:10]}</td></tr>' for r in repos)
                release_rows = "".join(
                    f'<tr><td><a href="{r[4]}" style="color:#4ecdc4">{r[4]}</a></td>'
                    f'<td style="color:#ff6b35;font-weight:bold">{r[0]}</td>'
                    f'<td>{r[1][:50] if r[1] else ""}</td><td>{r[2][:10] if r[2] else ""}</td>'
                    f'<td><a href="{r[3]}" style="color:#666">view</a></td></tr>' for r in recent)
                html = f'''<!DOCTYPE html><html><head><title>Release Tracker</title>
<style>body{{font-family:system-ui;max-width:1000px;margin:0 auto;padding:20px;background:#0a0a0a;color:#eee}}
h1{{color:#ff6b35}}h2{{color:#4ecdc4}}table{{width:100%;border-collapse:collapse;margin:10px 0}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #222}}th{{color:#ff6b35;font-size:.85em}}
tr:hover{{background:#161616}}a{{text-decoration:none}}</style></head><body>
<h1>📦 Release Tracker v1</h1>
<p style="color:#888">Monitoring GitHub repos for new releases · Port {PORT}</p>
<h2>Watched Repos ({len(repos)})</h2>
<table><tr><th>Repo</th><th>Name</th><th>Releases</th><th>Added</th></tr>{repo_rows}</table>
<h2>Recent Releases</h2>
<table><tr><th>Repo</th><th>Tag</th><th>Title</th><th>Date</th><th>Link</th></tr>{release_rows}</table>
<p style="color:#555;font-size:.8em">Poke Labs Release Tracker v1 | MIT</p>
</body></html>'''
                self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
                self.wfile.write(html.encode())
            elif path == "/api/health":
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump({"ok":True,"v":1,"port":PORT,"name":"release-tracker"}, self.wfile)
            elif path == "/api/check":
                results = []
                repos = conn.execute("SELECT full_name FROM repos").fetchall()
                for (name,) in repos:
                    r = check_releases(conn, name)
                    if r:
                        results.append(r)
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump({"checked": len(repos), "new": [r for r in results if r and r.get("new")], "all": results}, self.wfile)
            elif path == "/api/releases":
                releases = conn.execute("""SELECT rel.tag_name, rel.name, rel.body, rel.published_at, rel.html_url, rel.detected_at, r.full_name
                    FROM releases rel JOIN repos r ON rel.repo_id=r.id ORDER BY rel.detected_at DESC LIMIT 50""").fetchall()
                cols = ["tag","name","body","published","url","detected","repo"]
                data = [dict(zip(cols, r)) for r in releases]
                self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
                json.dump(data, self.wfile)
            elif path == "/api/repos":
                repos = conn.execute("SELECT full_name, display_name, added_at FROM repos ORDER BY added_at").fetchall()
                cols = ["full_name","display_name","added_at"]
                data = [dict(zip(cols, r)) for r in repos]
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
