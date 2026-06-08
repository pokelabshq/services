#!/usr/bin/env python3
"""Poke Labs Webhook Relay — Receives webhooks, forwards to multiple endpoints with retry."""
import http.server, json, urllib.request, urllib.error, threading, time, datetime, os, hashlib, hmac

PORT = 8775
DATA_FILE = "/home/alx/services/webhook-relay/relays.json"

lock = threading.Lock()
store = {"relays": [], "deliveries": [], "stats": {"total": 0, "success": 0, "failed": 0}}

def load():
    global store
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            store = json.load(f)

def save():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(store, f, indent=2)

def add_relay(name, url, secret="", events=None):
    r = {"id": hashlib.md5(f"{name}{url}".encode()).hexdigest()[:8], "name": name, "url": url,
         "secret": secret, "events": events or ["*"], "active": True, "created": datetime.datetime.now().isoformat(),
         "delivered": 0, "failed": 0}
    with lock:
        store["relays"].append(r)
        save()
    return r

def forward(relay, payload, event_type):
    body = json.dumps({"event": event_type, "payload": payload, "ts": datetime.datetime.now().isoformat()}).encode()
    headers = {"Content-Type": "application/json", "X-Poke-Event": event_type, "X-Poke-Relay": relay["id"]}
    if relay.get("secret"):
        sig = hmac.new(relay["secret"].encode(), body, hashlib.sha256).hexdigest()
        headers["X-Poke-Signature"] = f"sha256={sig}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(relay["url"], data=body, headers=headers, method="POST")
            resp = urllib.request.urlopen(req, timeout=10)
            with lock:
                relay["delivered"] += 1
                store["stats"]["total"] += 1
                store["stats"]["success"] += 1
                store["deliveries"].append({"relay": relay["id"], "event": event_type, "status": resp.status, "ts": datetime.datetime.now().isoformat()})
                if len(store["deliveries"]) > 200: store["deliveries"] = store["deliveries"][-200:]
                save()
            return True
        except Exception as e:
            if attempt == 2:
                with lock:
                    relay["failed"] += 1
                    store["stats"]["total"] += 1
                    store["stats"]["failed"] += 1
                    store["deliveries"].append({"relay": relay["id"], "event": event_type, "status": 0, "error": str(e)[:100], "ts": datetime.datetime.now().isoformat()})
                    save()
            time.sleep(1)
    return False

def dispatch(event_type, payload):
    with lock:
        relays = [r for r in store["relays"] if r["active"] and ("*" in r["events"] or event_type in r["events"])]
    threads = []
    for r in relays:
        t = threading.Thread(target=forward, args=(r, payload, event_type))
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=15)

PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Poke Labs Webhook Relay</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0a0a0f;color:#e0e0e0;max-width:900px;margin:0 auto;padding:2rem}
h1{color:#00d4ff;margin-bottom:1rem}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:2rem}
.card{background:#111;border:1px solid #222;border-radius:10px;padding:1rem;text-align:center}
.card .v{font-size:1.8rem;font-weight:700;color:#00d4ff}.card .l{color:#666;font-size:.75rem}
table{width:100%;border-collapse:collapse}th,td{padding:.5rem;border-bottom:1px solid #222;text-align:left;font-size:.85rem}
th{color:#00d4ff}form{background:#111;border:1px solid #222;border-radius:10px;padding:1.5rem;margin-bottom:2rem}
input,select{width:100%;padding:.5rem;margin:.3rem 0;border:1px solid #333;border-radius:6px;background:#0a0a0f;color:#fff}
button{background:linear-gradient(135deg,#00d4ff,#7b2ff7);color:#fff;border:none;padding:.6rem 1.5rem;border-radius:6px;cursor:pointer;font-size:.9rem}
.ok{color:#00ff88}.err{color:#ff4444}</style></head><body>
<h1>🐾 Webhook Relay</h1>
<div class="grid"><div class="card"><div class="v" id="t">0</div><div class="l">Total</div></div>
<div class="card"><div class="v" id="s" style="color:#00ff88">0</div><div class="l">Delivered</div></div>
<div class="card"><div class="v" id="f" style="color:#ff4444">0</div><div class="l">Failed</div></div></div>
<h2>Add Relay</h2>
<form onsubmit="addRelay(event)">
<input id="name" placeholder="Name (e.g. Discord)" required>
<input id="url" placeholder="Webhook URL" required>
<input id="secret" placeholder="Secret (optional)">
<input id="events" placeholder="Events (comma-separated, * for all)">
<button type="submit">Add Relay</button>
</form>
<h2>Relays</h2><table><tr><th>Name</th><th>URL</th><th>Events</th><th>Delivered</th><th>Failed</th></tr><tbody id="r"></tbody></table>
<h2>Recent Deliveries</h2><table><tr><th>Relay</th><th>Event</th><th>Status</th><th>Time</th></tr><tbody id="d"></tbody></table>
<script>
async function load(){
  const s=await(await fetch('/api/stats')).json();
  document.getElementById('t').textContent=s.total;document.getElementById('s').textContent=s.success;document.getElementById('f').textContent=s.failed;
  const r=await(await fetch('/api/relays')).json();
  document.getElementById('r').innerHTML=r.map(x=>`<tr><td>${x.name}</td><td style="font-size:.75rem;color:#666">${x.url.substring(0,50)}</td><td>${x.events.join(',')}</td><td class="ok">${x.delivered}</td><td class="err">${x.failed}</td></tr>`).join('');
  const d=await(await fetch('/api/deliveries')).json();
  document.getElementById('d').innerHTML=d.slice(-10).reverse().map(x=>`<tr><td>${x.relay}</td><td>${x.event}</td><td class="${x.status>=200&&x.status<300?'ok':'err'}">${x.status||x.error||'err'}</td><td>${x.ts?.substring(11,19)||''}</td></tr>`).join('');
}
async function addRelay(e){
  e.preventDefault();
  const r=await fetch('/api/relays',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:document.getElementById('name').value,url:document.getElementById('url').value,
    secret:document.getElementById('secret').value,events:document.getElementById('events').value.split(',').map(s=>s.trim())})});
  if(r.ok){e.target.reset();load();}
}
load();setInterval(load,10000);</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=self.path.split("?")[0]
        if p in ("/",""):
            self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(PAGE.encode())
        elif p=="/api/stats":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps(store["stats"]).encode())
        elif p=="/api/relays":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps(store["relays"]).encode())
        elif p=="/api/deliveries":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps(store["deliveries"][-50:]).encode())
        elif p=="/api/health":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"v":1,"relays":len(store["relays"])}).encode())
        else:self.send_response(404);self.end_headers()

    def do_POST(self):
        cl=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(cl)
        p=self.path.split("?")[0]
        try:
            data=json.loads(body) if body else {}
        except:data={}
        if p=="/api/relays":
            r=add_relay(data.get("name",""),data.get("url",""),data.get("secret",""),data.get("events",["*"]))
            self.send_response(201);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps(r).encode())
        elif p=="/api/dispatch":
            event=data.get("event","test")
            payload=data.get("payload",{})
            threading.Thread(target=dispatch,args=(event,payload),daemon=True).start()
            self.send_response(202);self.send_header("Content-Type","application/json");self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"event":event,"relays":len([r for r in store["relays"] if r["active"]])}).encode())
        elif p=="/webhook":
            event=self.headers.get("X-GitHub-Event","unknown")
            threading.Thread(target=dispatch,args=(event,data),daemon=True).start()
            self.send_response(202);self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:self.send_response(404);self.end_headers()
    def log_message(self,*a):pass

if __name__=="__main__":
    load()
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Webhook Relay on port {PORT}");s.serve_forever()
