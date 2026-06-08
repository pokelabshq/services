#!/usr/bin/env python3
"""Poke Labs Milestone Tracker v1 — Track project milestones, deadlines, progress."""
import http.server, json, os, datetime, re

PORT = 8792
DATA_FILE = "/home/alx/services/milestone-tracker/milestones.json"

DEFAULT_MILESTONES = [
    {"id": "m1", "title": "Launch Poke Labs website", "status": "done", "due": "2026-06-01", "tags": ["infra"], "progress": 100},
    {"id": "m2", "title": "Deploy Council v1", "status": "done", "due": "2026-06-03", "tags": ["product"], "progress": 100},
    {"id": "m3", "title": "Set up auto-merge for Dependabot", "status": "done", "due": "2026-06-05", "tags": ["devops"], "progress": 100},
    {"id": "m4", "title": "Build service dashboard", "status": "done", "due": "2026-06-06", "tags": ["product"], "progress": 100},
    {"id": "m5", "title": "Deploy all services to production", "status": "in-progress", "due": "2026-06-10", "tags": ["devops"], "progress": 60},
    {"id": "m6", "title": "Set up monitoring & alerting", "status": "in-progress", "due": "2026-06-12", "tags": ["devops"], "progress": 40},
    {"id": "m7", "title": "Write API documentation", "status": "pending", "due": "2026-06-15", "tags": ["docs"], "progress": 0},
    {"id": "m8", "title": "Launch public beta", "status": "pending", "due": "2026-06-30", "tags": ["product"], "progress": 0},
    {"id": "m9", "title": "Community feedback round 1", "status": "pending", "due": "2026-07-15", "tags": ["community"], "progress": 0},
    {"id": "m10", "title": "v1.0 stable release", "status": "pending", "due": "2026-08-01", "tags": ["product"], "progress": 0},
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return DEFAULT_MILESTONES[:]

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_stats(data):
    total = len(data)
    done = sum(1 for m in data if m["status"] == "done")
    in_prog = sum(1 for m in data if m["status"] == "in-progress")
    pending = sum(1 for m in data if m["status"] == "pending")
    overdue = sum(1 for m in data if m["status"] != "done" and m["due"] < datetime.datetime.now().strftime("%Y-%m-%d"))
    avg_progress = sum(m["progress"] for m in data) / total if total else 0
    return {"total": total, "done": done, "in_progress": in_prog, "pending": pending, "overdue": overdue, "avg_progress": round(avg_progress, 1)}

PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Labs — Milestone Tracker</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}
.hdr{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:2rem 1rem;text-align:center;border-bottom:1px solid #2a2a4a}
.hdr h1{font-size:2rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr p{color:#666;margin-top:.4rem;font-size:.85rem}
.stats{display:flex;justify-content:center;gap:1.5rem;margin:1.5rem auto;flex-wrap:wrap;max-width:800px;padding:0 1rem}
.stat{text-align:center}
.stat .n{font-size:1.6rem;font-weight:700;color:#00d4ff}
.stat .l{color:#555;font-size:.7rem;text-transform:uppercase;letter-spacing:.05rem}
.bar{max-width:800px;margin:0 auto 2rem;padding:0 1rem}
.bar .track{height:6px;background:#1a1a1a;border-radius:3px;overflow:hidden}
.bar .fill{height:100%;background:linear-gradient(90deg,#00d4ff,#7b2ff7);border-radius:3px;transition:width .5s}
.bar .label{display:flex;justify-content:space-between;margin-top:.3rem;font-size:.75rem;color:#555}
.grid{max-width:800px;margin:0 auto;padding:0 1rem 2rem;display:flex;flex-direction:column;gap:.5rem}
.milestone{background:#111;border:1px solid #1a1a1a;border-radius:10px;padding:1rem;display:flex;align-items:flex-start;gap:1rem}
.milestone.done{opacity:.6}
.milestone .check{width:22px;height:22px;border-radius:50%;border:2px solid #333;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:.7rem;margin-top:.1rem}
.milestone.done .check{background:#00ff8833;border-color:#00ff88;color:#00ff88}
.milestone.in-progress .check{border-color:#00d4ff}
.milestone .content{flex:1}
.milestone h3{font-size:.95rem;margin-bottom:.2rem}
.milestone.done h3{text-decoration:line-through;color:#666}
.milestone .meta{display:flex;gap:.75rem;align-items:center;font-size:.75rem;color:#555}
.milestone .tag{background:#1a1a2e;padding:.1rem .4rem;border-radius:3px;font-size:.65rem;color:#7b2ff7}
.milestone .due-soon{color:#ffaa00}
.milestone .due-overdue{color:#ff4444}
.milestone .progress-track{height:3px;background:#1a1a1a;border-radius:2px;margin-top:.5rem;overflow:hidden}
.milestone .progress-fill{height:100%;background:#00d4ff;border-radius:2px}
.ft{text-align:center;padding:2rem;color:#444;font-size:.8rem}
</style></head><body>
<div class="hdr">
<h1>🐾 Milestone Tracker</h1>
<p>__DATE__ · Poke Labs Roadmap</p>
</div>
<div class="stats" id="stats"></div>
<div class="bar"><div class="track"><div class="fill" id="prog" style="width:0%"></div></div><div class="label"><span>Overall Progress</span><span id="prog-text">0%</span></div></div>
<div class="grid" id="milestones"></div>
<div class="ft">🐾 Poke Labs · MIT Licensed</div>
<script>
const data=__DATA__;
const stats=__STATS__;
document.getElementById('stats').innerHTML=`
  <div class="stat"><div class="n">${stats.total}</div><div class="l">Total</div></div>
  <div class="stat"><div class="n" style="color:#00ff88">${stats.done}</div><div class="l">Done</div></div>
  <div class="stat"><div class="n" style="color:#00d4ff">${stats.in_progress}</div><div class="l">Active</div></div>
  <div class="stat"><div class="n" style="color:#ffaa00">${stats.pending}</div><div class="l">Pending</div></div>
  <div class="stat"><div class="n" style="color:#ff4444">${stats.overdue}</div><div class="l">Overdue</div></div>
`;
document.getElementById('prog').style.width=stats.avg_progress+'%';
document.getElementById('prog-text').textContent=stats.avg_progress+'%';
document.getElementById('milestones').innerHTML=data.map(m=>{
  const status=m.status.replace('-',' ');
  const due=new Date(m.due)<new Date()&&m.status!=='done'?'due-overdue':(new Date(m.due)-new Date()<7*86400000&&m.status!=='done'?'due-soon':'');
  const check=m.status==='done'?'✓':'';
  const tags=m.tags.map(t=>'<span class="tag">'+t+'</span>').join('');
  return `<div class="milestone ${m.status}"><div class="check">${check}</div><div class="content"><h3>${m.title}</h3><div class="meta"><span class="${due}">📅 ${m.due}</span><span>${status}</span>${tags}</div><div class="progress-track"><div class="progress-fill" style="width:${m.progress}%"></div></div></div></div>`;
}).join('');
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        data = load_data()
        if path in ("/", "/index.html"):
            stats = get_stats(data)
            page = (PAGE
                .replace("__DATE__", datetime.datetime.now().strftime("%Y-%m-%d"))
                .replace("__DATA__", json.dumps(data))
                .replace("__STATS__", json.dumps(stats)))
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write(page.encode())
        elif path == "/api/milestones":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        elif path == "/api/stats":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps(get_stats(data), indent=2).encode())
        elif path == "/api/health":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"v":1,"milestones":len(data)}).encode())
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            new_milestone = json.loads(body)
            new_milestone.setdefault("id", f"m{datetime.datetime.now().timestamp()}")
            new_milestone.setdefault("status", "pending")
            new_milestone.setdefault("progress", 0)
            new_milestone.setdefault("tags", [])
            data = load_data()
            data.append(new_milestone)
            save_data(data)
            self.send_response(201); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps(new_milestone).encode())
        except Exception as e:
            self.send_response(400); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    def do_PUT(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            update = json.loads(body)
            data = load_data()
            for i, m in enumerate(data):
                if m["id"] == update.get("id"):
                    data[i].update(update)
                    break
            save_data(data)
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        except Exception as e:
            self.send_response(400); self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Milestone Tracker on port {PORT}")
    server.serve_forever()
