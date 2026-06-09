#!/usr/bin/env python3
"""Webhook Tester v1.0 — Inspect, log, replay HTTP webhooks. Self-hosted."""
import http.server, json, hashlib, time, os, sqlite3
from urllib.parse import urlparse, parse_qs

PORT = 8778
DB = "/tmp/webhook-tester.db"

def init_db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, method TEXT, path TEXT, headers TEXT, body TEXT, ip TEXT, ts TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS bins (token TEXT PRIMARY KEY, created_at TEXT)")
    c.commit(); c.close()

def save_req(rid, method, path, headers, body, ip):
    c = sqlite3.connect(DB)
    c.execute("INSERT OR REPLACE INTO requests VALUES (?,?,?,?,?,?,?)",
        (rid, method, path, json.dumps(headers), body, ip, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
    c.commit(); c.close()

def get_requests(limit=50):
    c = sqlite3.connect(DB)
    rows = c.execute("SELECT id,method,path,body,ts FROM requests ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(zip(["id","method","path","body","ts"], r)) for r in rows]

def create_bin():
    token = hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]
    c = sqlite3.connect(DB)
    c.execute("INSERT INTO bins VALUES (?,?)", (token, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
    c.commit(); c.close()
    return token

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/":
            self.send_html(self.page())
        elif p == "/api/stats":
            c = sqlite3.connect(DB)
            total = c.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
            bins = c.execute("SELECT COUNT(*) FROM bins").fetchone()[0]
            c.close()
            self.send_json({"requests": total, "bins": bins})
        elif p == "/api/new":
            tok = create_bin()
            self.send_json({"token": tok, "url": "/" + tok})
        elif p == "/api/requests":
            self.send_json(get_requests())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")[:10000]
        rid = hashlib.sha256((str(time.time()) + body).encode()).hexdigest()[:16]
        hdrs = {k: v for k, v in self.headers.items()}
        save_req(rid, "POST", self.path, hdrs, body, self.client_address[0])
        self.send_json({"ok": True, "id": rid})

    do_PUT = do_PATCH = do_DELETE = do_POST

    def send_html(self, h):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(h.encode())

    def send_json(self, d):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

    def page(self):
        h = []
        h.append("<!DOCTYPE html><html><head><title>Webhook Tester</title>")
        h.append("<style>")
        h.append("body{font-family:system-ui,monospace;max-width:800px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}")
        h.append("h1{color:#a78bfa}button{background:#a78bfa;color:#000;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:700}")
        h.append(".card{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:14px;margin:10px 0}")
        h.append(".req{background:#111;border-radius:6px;padding:10px;margin:6px 0;font-size:.85em;word-break:break-all}")
        h.append(".m{color:#22c55e;font-weight:700}.t{color:#666;font-size:.8em}")
        h.append("</style></head><body>")
        h.append("<h1>Hook Webhook Tester</h1>")
        h.append('<div class="card"><p>Self-hosted webhook inspector. Create a bin, send webhooks, inspect payloads.</p>')
        h.append('<button onclick="n()">+ New Bin</button> <span id="u" style="margin-left:12px;font-family:monospace;color:#22c55e"></span></div>')
        h.append('<div id="r"><h2>Recent Requests</h2><p style="color:#666">Send a webhook to see it here.</p></div>')
        h.append("<script>")
        h.append("function n(){fetch('/api/new').then(function(r){return r.json()}).then(function(d){document.getElementById('u').textContent=d.url})}")
        h.append("function l(){fetch('/api/requests').then(function(r){return r.json()}).then(function(d){")
        h.append("var e=document.getElementById('r');")
        h.append("if(!d.length){e.innerHTML='<h2>Recent</h2><p style=color:#666>None yet.</p>';return}")
        h.append("e.innerHTML='<h2>Recent ('+d.length+')</h2>';")
        h.append("d.forEach(function(req){e.innerHTML+= '<div class=req><span class=m>'+req.method+'</span> '+req.path+' <span class=t>'+req.ts+'</span><br><small style=color:#666>'+(req.body||'').substring(0,200)+</small></div>'})")
        h.append("})}")
        h.append("l();setInterval(l,5000);")
        h.append("</script></body></html>")
        return "".join(h)

    def log_message(self, *a): pass

if __name__ == "__main__":
    init_db()
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print("Webhook Tester: http://localhost:" + str(PORT) + "/", flush=True)
    s.serve_forever()
