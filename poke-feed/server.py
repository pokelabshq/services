#!/usr/bin/env python3
"""
Poke Feed v1.0 — Unified activity stream for Poke Labs.
Aggregates events from all services into a single feed.

Port: 8745
API:
  GET /api/feed          — Get aggregated activity feed
  GET /api/feed?service=x — Filter by service
  POST /api/events       — Ingest event from a service
  GET /api/health        — Health check
"""
import http.server, json, os, socketserver, urllib.parse, datetime, threading

PORT = 8745
DATA_FILE = os.path.join(os.path.dirname(__file__), "feed.json")
LOCK = threading.Lock()

def load_feed():
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except: pass
    return {"events": [], "last_updated": datetime.datetime.utcnow().isoformat()}

def save_feed(data):
    with LOCK:
        with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def add_event(service, event_type, message, meta=None):
    data = load_feed()
    event = {
        "id": f"{datetime.datetime.utcnow().timestamp()}-{len(data['events'])}",
        "service": service,
        "type": event_type,
        "message": message,
        "meta": meta or {},
        "ts": datetime.datetime.utcnow().isoformat()
    }
    data["events"].insert(0, event)
    data["events"] = data["events"][:1000]  # Keep last 1000
    data["last_updated"] = event["ts"]
    save_feed(data)
    return event

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if p == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT})
        elif p == "/api/feed":
            data = load_feed()
            events = data["events"]
            if "service" in q:
                events = [e for e in events if e["service"] == q["service"][0]]
            if "type" in q:
                events = [e for e in events if e["type"] == q["type"][0]]
            if "limit" in q:
                events = events[:int(q["limit"][0])]
            self.send_json({"events": events, "total": len(data["events"]), "returned": len(events)})
        elif p == "/":
            self.send_html(self._page())
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if p == "/api/events":
            ev = add_event(
                body.get("service", "unknown"),
                body.get("type", "info"),
                body.get("message", ""),
                body.get("meta")
            )
            self.send_json({"ok": True, "event": ev})
        else:
            self.send_json({"error": "not found"}, 404)

    def send_json(self, d, c=200):
        b = json.dumps(d, default=str).encode()
        self.send_response(c); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)

    def send_html(self, h):
        b = h.encode()
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)

    def _page(self):
        return """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Feed — Activity Stream</title>
<style>body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;max-width:800px;margin:0 auto}
h1{color:#60a5fa}.event{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 16px;margin:8px 0}
.event .meta{font-size:.75em;color:#64748b;margin-bottom:4px}
.event .msg{font-size:.95em}.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:.7em;margin-right:4px}
.tag.deploy{background:#065f46;color:#6ee7b7}.tag.error{background:#7f1d1d;color:#fca5a5}
.tag.info{background:#1e3a5f;color:#93c5fd}.tag.revenue{background:#7c2d12;color:#fdba74}
</style></head><body>
<h1>📡 Poke Feed</h1><p style="color:#64748b">Unified activity stream · Port 8745</p>
<div id="feed">Loading...</div>
<script>
(async function load(){
  try{
    const d=await(await fetch('/api/feed?limit=50')).json();
    document.getElementById('feed').innerHTML=d.events.map(e=>`
      <div class="event">
        <div class="meta"><span class="tag ${e.type}">${e.type}</span> ${e.service} · ${new Date(e.ts).toLocaleString()}</div>
        <div class="msg">${e.message}</div>
      </div>`).join('')||'<p style="color:#64748b">No events yet</p>';
  }catch(e){document.getElementById('feed').innerHTML='<p>Failed to load</p>'}
})();
setInterval(()=>location.reload(),15000);
</script></body></html>"""
    def log_message(self,*a): pass

class R(socketserver.TCPServer): allow_reuse_address=True

if __name__=="__main__":
    add_event("poke-feed", "deploy", "Poke Feed v1.0 started")
    print(f"📡 Poke Feed v1.0 on port {PORT}")
    R(("",PORT),Handler).serve_forever()
