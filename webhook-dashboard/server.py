#!/usr/bin/env python3
"""GitHub Webhook Dashboard v1 — Real-time webhook event viewer."""
import http.server, json, hashlib, hmac, time, os, threading

PORT = 8771
SECRET = os.environ.get("GITHUB_SECRET", "")
lock = threading.Lock()
events = []

HTML = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Webhook Dashboard — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}
.h{background:linear-gradient(135deg,#0a0a1a,#1a1a3e);padding:40px 20px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.04)}
h1{font-size:2rem;color:#00ffaa;margin-bottom:6px}
.sub{color:#666;font-size:.85rem}
.stats{display:flex;justify-content:center;gap:24px;padding:14px;border-bottom:1px solid rgba(255,255,255,0.04)}
.st{text-align:center;font-size:.7rem;color:#666}.st b{color:#00ffaa;font-size:1.1rem;display:block}
.container{max-width:900px;margin:0 auto;padding:24px}
.event{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;margin:10px 0;border-left:3px solid #00ffaa}
.event.push{border-left-color:#6496ff}
.event.pr{border-left-color:#ff6b6a}
.event.issue{border-left-color:#ffd93d}
.event .meta{display:flex;justify-content:space-between;color:#555;font-size:.7rem;margin-bottom:6px}
.event .type{font-weight:700;color:#00ffaa;font-size:.8rem}
.event .data{font-family:monospace;font-size:.72rem;color:#888;background:rgba(0,0,0,0.3);border-radius:6px;padding:10px;margin-top:8px;overflow-x:auto;white-space:pre-wrap;word-break:break-all}
.empty{text-align:center;padding:60px;color:#444}
</style></head><body>
<div class="h">
<h1>📡 Webhook Dashboard</h1>
<p class="sub">Real-time GitHub webhook event viewer — Poke Labs</p>
</div>
<div class="stats">
<div class="st"><b id="total">0</b>Events</div>
<div class="st"><b id="push">0</b>Push</div>
<div class="st"><b id="pr">0</b>PRs</div>
<div class="st"><b id="issue">0</b>Issues</div>
</div>
<div class="container" id="events"><div class="empty">Waiting for webhook events...</div></div>
<script>
async function load(){
  const r=await fetch("/api/events");
  const d=await r.json();
  const evts=d.events||[];
  document.getElementById("total").textContent=evts.length;
  document.getElementById("push").textContent=evts.filter(e=>e.type==="push").length;
  document.getElementById("pr").textContent=evts.filter(e=>e.type==="pull_request").length;
  document.getElementById("issue").textContent=evts.filter(e=>e.type==="issues").length;
  const c=document.getElementById("events");
  if(!evts.length){c.innerHTML='<div class="empty">Waiting for webhook events...</div>';return}
  c.innerHTML=evts.slice().reverse().map(e=>{
    const cls=e.type==="push"?"push":e.type==="pull_request"?"pr":e.type==="issues"?"issue":"";
    return `<div class="event ${cls}"><div class="meta"><span>${new Date(e.ts*1000).toISOString()}</span><span>${e.delivery||""}</span></div><div class="type">${e.type}${e.action?" — "+e.action:""}</div><div class="data">${JSON.stringify(e.payload,null,2).slice(0,2000)}</div></div>`;
  }).join("");
}
load();setInterval(load,3000);
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        import urllib.parse
        p=urllib.parse.urlparse(self.path)
        if p.path=="/": self._html(HTML)
        elif p.path=="/api/events": self._json({"events":events,"total":len(events)})
        elif p.path=="/api/health": self._json({"ok":True,"v":1,"events":len(events),"port":PORT})
        else: self._json({"error":"not found"},404)

    def do_POST(self):
        import urllib.parse
        p=urllib.parse.urlparse(self.path)
        if p.path=="/webhook":
            try:
                length=int(self.headers.get("Content-Length",0))
                body=self.rfile.read(length)
                # Verify signature if secret set
                if SECRET:
                    sig=self.headers.get("X-Hub-Signature-256","")
                    expected="sha256="+hmac.new(SECRET.encode(),body,hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(sig,expected):
                        self._json({"error":"invalid signature"},401);return
                payload=json.loads(body)
                event_type=self.headers.get("X-GitHub-Event","unknown")
                delivery=self.headers.get("X-GitHub-Delivery","")
                with lock:
                    events.append({"ts":time.time(),"type":event_type,"action":payload.get("action",""),"delivery":delivery,"payload":payload})
                    if len(events)>500: events.pop(0)
                self._json({"ok":True,"type":event_type})
            except Exception as e: self._json({"error":str(e)},500)
        else: self._json({"error":"not found"},404)

    def _html(self,h,code=200):
        b=h.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers();self.wfile.write(b)

    def _json(self,d,code=200):
        b=json.dumps(d,default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers();self.wfile.write(b)

    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Webhook Dashboard v1 on :{PORT}")
    s.serve_forever()
