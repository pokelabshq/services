#!/usr/bin/env python3
"""GitHub Streak Tracker v1.0 — Track coding streaks with SVG badges."""
import http.server, json, urllib.request, urllib.parse, sqlite3, os, re
from datetime import datetime, timedelta

PORT = int(os.environ.get("PORT", 8785))
DB = "/tmp/streak.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS commits (user TEXT, repo TEXT, date TEXT, count INTEGER, PRIMARY KEY(user, repo, date))")
    conn.commit()
    conn.close()

def get_streak(username):
    """Calculate current streak from commit history."""
    try:
        url = f"https://api.github.com/users/{username}/events/public?per_page=100"
        req = urllib.request.Request(url, headers={"User-Agent": "PokeLabs-StreakTrack/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        events = json.loads(resp.read())
        push_dates = set()
        for e in events:
            if e.get("type") == "PushEvent":
                dt = e["created_at"][:10]
                push_dates.add(dt)
        if not push_dates:
            return 0
        sorted_dates = sorted(push_dates, reverse=True)
        streak = 1
        today = datetime.utcnow().date()
        try:
            first = datetime.strptime(sorted_dates[0], "%Y-%m-%d").date()
        except:
            return 0
        if (today - first).days > 1:
            return 0
        for i in range(1, len(sorted_dates)):
            curr = datetime.strptime(sorted_dates[i-1], "%Y-%m-%d").date()
            prev = datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
            if (curr - prev).days == 1:
                streak += 1
            else:
                break
        return streak
    except:
        return 0

def svg_badge(streak, username):
    color = "#3fb950" if streak >= 7 else "#d29922" if streak >= 3 else "#f85149" if streak == 0 else "#8b949e"
    label = "streak"
    value = f"{streak} day{'s' if streak != 1 else ''}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20">
  <rect width="60" height="20" rx="3" fill="#555"/>
  <rect x="60" width="80" height="20" rx="3" fill="{color}"/>
  <rect x="60" width="4" height="20" fill="{color}"/>
  <text x="30" y="14" fill="#fff" font-size="11" text-anchor="middle" font-family="monospace">{label}</text>
  <text x="100" y="14" fill="#fff" font-size="11" text-anchor="middle" font-family="monospace">{value}</text>
</svg>'''

HTML_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>GitHub Streak Tracker</title>
<style>
body{font-family:system-ui;background:#0a0a14;color:#c8c8d8;display:flex;flex-direction:column;align-items:center;padding:80px 20px;gap:24px}
h1{font-size:2rem;color:#00d4ff}
input,button{padding:12px 20px;border-radius:8px;border:1px solid #30363d;font-size:1rem}
input{background:#161b22;color:#c8c8d8;width:260px}
button{background:linear-gradient(90deg,#00d4ff,#7b2ff7);color:#000;font-weight:600;cursor:pointer}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px;text-align:center;max-width:400px;width:100%}
a{color:#00d4ff}
</style></head>
<body>
<h1>🔥 GitHub Streak Tracker</h1>
<div class="card">
 <p>Enter a GitHub username to see their current commit streak.</p>
 <form method="GET">
  <input name="user" placeholder="GitHub username" autofocus required><br><br>
  <button type="submit">Check Streak</button>
 </form>
 <p style="margin-top:24px;font-size:0.85rem;color:#6e7681">
  SVG badge: <code>?user=xxx&amp;format=svg</code><br>
  JSON: <code>?user=xxx&amp;format=json</code>
 </p>
</div>
<p style="font-size:0.85rem;color:#6e7681">🫧 Poke Labs · streak-tracker v1.0</p>
</body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        init_db()
        p = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(p.query)
        if p.path == "/":
            user = q.get("user", [None])[0]
            fmt = q.get("format", ["html"])[0]
            if not user:
                self.send_html(HTML_PAGE)
                return
            streak = get_streak(user)
            if fmt == "svg":
                self.send_svg(svg_badge(streak, user))
            elif fmt == "json":
                self.send_json({"user": user, "streak": streak, "v": 1})
            else:
                self.send_html(f'<!DOCTYPE html><html><body style="background:#0a0a14;color:#c8c8d8;text-align:center;padding:80px;font-family:system-ui"><div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px;display:inline-block"><h2 style="color:#00d4ff">@{user}</h2><p style="font-size:3rem;color:#3fb950;font-weight:700">{streak} day{"s" if streak != 1 else ""}</p><a href="/">← Back</a></div></body></html>')
        elif p.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT})
        else:
            self.send_json({"error": "not found"}, 404)

    def send_html(self, h):
        b = h.encode(); self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def send_svg(self, s):
        b = s.encode(); self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def send_json(self, d, c=200):
        b = json.dumps(d).encode(); self.send_response(c)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def log_message(self, *a): pass

if __name__ == "__main__":
    init_db()
    print(f"GitHub Streak Tracker v1.0 on port {PORT}")
    http.server.HTTPServer(("", PORT), H).serve_forever()
