#!/usr/bin/env python3
"""Poke Labs Telegram Bot — Daily briefings and commands"""
import http.server, json, urllib.request, urllib.parse, os, time, socket

PORT = 8777
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""

# Service registry
SERVICES = [
    ("Link Preview API", 8765, "/api/health"),
    ("Poke Labs Site", 8766, "/api/health"),
    ("Poke Bot", 8770, "/"),
    ("Discord Bot", 8775, "/api/health"),
    ("Skills Hub", 8780, "/api/health"),
    ("Pricing API", 8790, "/api/health"),
]

def check_port(port, path="/"):
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except:
        return False

def generate_briefing():
    lines = ["🐾 *Poke Labs Daily Briefing*", ""]
    
    # Service status
    lines.append("📊 *Services:*")
    up = 0
    for name, port, path in SERVICES:
        ok = check_port(port, path)
        if ok: up += 1
        lines.append(f"  {'✅' if ok else '❌'} {name} (:{port})")
    lines.append(f"  _{up}/{len(SERVICES)} online_")
    lines.append("")
    
    # System
    try:
        import subprocess
        disk = subprocess.check_output("df -h / | tail -1 | awk '{print $5}'", shell=True).decode().strip()
        mem = subprocess.check_output("free -h | grep Mem | awk '{print $3\"/\"$2}'", shell=True).decode().strip()
        lines.append(f"💾 Disk: {disk} | RAM: {mem}")
    except:
        pass
    
    lines.append("")
    lines.append("_Next: Fund wallet → Top up credits → Ship features_")
    return "\n".join(lines)

def send_telegram(text):
    if not API_BASE or not CHAT_ID:
        return {"ok": False, "error": "TELEGRAM_TOKEN or TELEGRAM_CHAT not set"}
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}).encode()
    try:
        req = urllib.request.Request(f"{API_BASE}/sendMessage", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "service": "telegram-bot", "configured": bool(BOT_TOKEN)})
        elif self.path == "/api/briefing":
            self.send_json({"briefing": generate_briefing()})
        elif self.path == "/api/send-now":
            briefing = generate_briefing()
            result = send_telegram(briefing)
            self.send_json({"sent": result.get("ok", False), "result": result})
        else:
            self.send_html(f"""<!DOCTYPE html>
<html><head><title>Poke Labs Telegram Bot</title>
<style>body{{font-family:system-ui;max-width:600px;margin:3rem auto;padding:1rem;color:#ddd;background:#111}}
h1{{color:#a78bfa}}code{{background:#222;padding:.2rem .4rem;border-radius:4px}}</style>
</head><body>
<h1>📱 Poke Labs Telegram Bot</h1>
<p>Sends daily briefings to the Poke Labs Telegram channel.</p>
<h2>Setup</h2>
<p>1. Get a bot token from <a href="https://t.me/BotFather">@BotFather</a></p>
<p>2. Set <code>TELEGRAM_TOKEN</code> and <code>TELEGRAM_CHAT</code> env vars</p>
<p>3. Restart the bot</p>
<h2>API</h2>
<p><code>GET /api/health</code> — Health check</p>
<p><code>GET /api/briefing</code> — Generate a briefing (JSON)</p>
<p><code>GET /api/send-now</code> — Send briefing to Telegram now</p>
<h2>Status</h2>
<p>Configured: {'✅' if BOT_TOKEN else '❌ (needs TELEGRAM_TOKEN)'}</p>
</body></html>""")

    def do_POST(self):
        if self.path == "/api/briefing":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            send = body.get("send", False)
            briefing = generate_briefing()
            result = None
            if send:
                result = send_telegram(briefing)
            self.send_json({"briefing": briefing, "telegram_result": result})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, d, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(d, indent=2).encode())

    def send_html(self, html, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Telegram Bot v1 on :{PORT}")
    s.serve_forever()
