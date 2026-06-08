#!/usr/bin/env python3
"""
Poke Tweets — Twitter/X mention monitor for Poke Labs.
Tracks mentions, saves to SQLite, serves via HTTP.
No external deps — stdlib only.
"""

import http.server
import json
import sqlite3
import os
import datetime
import urllib.request, urllib.parse

DB_PATH = "/home/alx/services/poke-tweets/mentions.db"
PORT = 8780

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS mentions (
        id TEXT PRIMARY KEY,
        tweet_id TEXT,
        author TEXT,
        text TEXT,
        url TEXT,
        created_at TEXT,
        inserted_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS monitor_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    conn.commit()
    return conn

def get_state(conn, key):
    row = conn.execute("SELECT value FROM monitor_state WHERE key=?", (key,)).fetchone()
    return row[0] if row else None

def set_state(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO monitor_state(key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def get_mentions(conn):
    return conn.execute("SELECT * FROM mentions ORDER BY created_at DESC LIMIT 50").fetchall()

def get_stats(conn):
    total = conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
    today = datetime.date.today().isoformat()
    today_count = conn.execute("SELECT COUNT(*) FROM mentions WHERE date(created_at)=?", (today,)).fetchone()[0]
    return {"total": total, "today": today_count, "port": PORT, "v": 1}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        conn = init_db()
        try:
            if self.path == "/" or self.path == "/dashboard":
                mentions = get_mentions(conn)
                stats = get_stats(conn)
                html = f"""<!DOCTYPE html>
<html><head><title>Poke Tweets Monitor</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#0d0d0d;color:#e0e0e0}}
h1{{color:#ff6b35}} .stat{{background:#1a1a2e;padding:15px;border-radius:8px;margin:10px 0}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{padding:10px;text-align:left;border-bottom:1px solid #333}}
th{{color:#ff6b35}} tr:hover{{background:#1a1a2e}}
a{color:#4ecdc4;text-decoration:none}} a:hover{{text-decoration:underline}}
</style></head><body>
<h1>🐦 Poke Tweets Monitor</h1>
<div class="stat">
  <strong>Total mentions:</strong> {stats['total']} |
  <strong>Today:</strong> {stats['today']} |
  <strong>Port:</strong> {stats['port']}
</div>
<h2>Recent Mentions</h2>
<table><tr><th>Author</th><th>Text</th><th>Date</th><th>Link</th></tr>"""
                for m in mentions:
                    html += f"<tr><td>{m[2]}</td><td>{m[3][:100]}</td><td>{m[5]}</td><td><a href='{m[4]}' target='_blank'>View</a></td></tr>"
                html += "</table></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())

            elif self.path == "/api/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                json.dump({"ok": True, "v": 1, "port": PORT, "name": "poke-tweets"}, self.wfile)

            elif self.path == "/api/stats":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                json.dump(get_stats(conn), self.wfile)

            elif self.path == "/api/mentions":
                mentions = get_mentions(conn)
                cols = ["id","tweet_id","author","text","url","created_at","inserted_at"]
                data = [dict(zip(cols, m)) for m in mentions]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                json.dump(data, self.wfile)

            else:
                self.send_response(404)
                self.end_headers()
        finally:
            conn.close()

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    init_db()
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Tweets running on port {PORT}")
    server.serve_forever()
