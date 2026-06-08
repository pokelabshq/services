#!/usr/bin/env python3
"""
Poke Labs Notification Hub v1
Unified notification service — send alerts to multiple channels from one API.

POST /notify
  Body: {"message": "...", "channels": ["telegram", "log"], "priority": "normal"}
  
GET /health
GET /channels — list configured channels
"""

import http.server, json, os, urllib.request, urllib.parse, datetime

PORT = int(os.environ.get("PORT", 8790))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
LOG_FILE = "/tmp/notify-hub.log"

CHANNELS = ["log"]
if TELEGRAM_TOKEN and TELEGRAM_CHAT:
    CHANNELS.append("telegram")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False, "not configured"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"}).encode()
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return True, json.loads(r.read()).get("result", {}).get("message_id", "sent")
    except Exception as e:
        return False, str(e)

def send_log(text):
    ts = datetime.datetime.now().isoformat()
    line = f"[{ts}] {text}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
        return True, "logged"
    except Exception as e:
        return False, str(e)

SENDERS = {
    "telegram": send_telegram,
    "log": send_log,
}

HTML_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Poke Labs — Notification Hub</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;max-width:700px;margin:0 auto;padding:2rem}
h1{color:#00d4ff;margin-bottom:1rem}
input,textarea{width:100%;padding:.75rem;border:1px solid #333;border-radius:8px;background:#111;color:#fff;margin:.5rem 0;font-size:1rem}
textarea{height:100px;resize:vertical}
button{padding:.75rem 2rem;background:linear-gradient(90deg,#7b2ff7,#00d4ff);border:none;border-radius:8px;color:#fff;font-size:1rem;cursor:pointer;margin-top:.5rem}
button:hover{opacity:.9}
pre{background:#111;padding:1rem;border-radius:8px;border:1px solid #222;overflow:auto;margin-top:1rem}
label{color:#888;font-size:.9rem}
</style></head><body>
<h1>🐾 Notification Hub</h1>
<label>Message</label>
<textarea id="msg" placeholder="Enter notification message..."></textarea>
<label>Channels (comma-separated)</label>
<input id="ch" value="log" placeholder="log, telegram">
<label>Priority</label>
<input id="pr" value="normal" placeholder="low, normal, high, critical">
<button onclick="send()">Send Notification</button>
<pre id="out">Response will appear here...</pre>
<script>
async function send(){
  const body={message:document.getElementById('msg').value,channels:document.getElementById('ch').value.split(',').map(s=>s.trim()),priority:document.getElementById('pr').value};
  try{
    const r=await fetch('/notify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2);
  }catch(e){document.getElementById('out').textContent='Error: '+e;}
}
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(HTML_PAGE.encode())
        elif path == "/health":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"v":1,"service":"notify-hub","channels":CHANNELS}).encode())
        elif path == "/channels":
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"channels":CHANNELS,"configured":{"telegram":"yes" if "telegram" in CHANNELS else "no","log":"yes"}}).encode())
        else:
            self.send_response(404); self.end_headers()
    
    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/notify":
            cl = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(cl)) if cl > 0 else {}
            message = body.get("message", "")
            channels = body.get("channels", ["log"])
            priority = body.get("priority", "normal")
            
            if not message:
                self.send_response(400); self.send_header("Content-Type","application/json"); self.end_headers()
                self.wfile.write(json.dumps({"error":"message required"}).encode())
                return
            
            full_msg = f"[{priority.upper()}] {message}"
            results = {}
            for ch in channels:
                sender = SENDERS.get(ch.strip())
                if sender:
                    ok, detail = sender(full_msg)
                    results[ch] = {"ok": ok, "detail": str(detail)}
                else:
                    results[ch] = {"ok": False, "detail": "unknown channel"}
            
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok":True,"sent":results,"message":full_msg}).encode())
        else:
            self.send_response(404); self.end_headers()
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Notification Hub v1 on port {PORT}")
    server.serve_forever()
