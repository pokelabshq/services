#!/usr/bin/env python3
"""Poke Labs Telegram Bot v1.
Sends daily morning briefings to Alexander.
Also responds to /status, /health, /repos commands."""

import json, os, urllib.request, urllib.parse
from datetime import datetime, timezone

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
PORT = int(os.environ.get("PORT", 8777))

def api(method, data=None):
    if not BOT_TOKEN:
        return {"ok": False, "error": "No BOT_TOKEN set"}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_message(text, chat_id=None):
    return api("sendMessage", {
        "chat_id": chat_id or CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })

def get_daily_briefing():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"🐾 *Poke Labs Morning Briefing*",
        f"_{now}_",
        "",
        "📊 *Services:*",
        "  • pokelabs.org — online",
        "  • Link Preview API — needs restart",
        "  • Poke Bot — needs restart",
        "  • Health Dashboard — needs restart",
        "",
        "📦 *Repos:*",
        "  • council — active (PRs open)",
        "",
        "💰 *Status:*",
        "  • Credits: depleted",
        "  • Awaiting funding to resume full operations",
        "",
        "Have a great day, Alexander! 🚀"
    ]
    return "\n".join(lines)

def handle_update(update):
    if "message" not in update:
        return
    msg = update["message"]
    text = msg.get("text", "")
    chat_id = str(msg["chat"]["id"])

    if text == "/start":
        send_message("🐾 Poke Labs Bot is online! Commands: /status /health /repos /briefing", chat_id)
    elif text == "/status":
        send_message("🐾 Poke is alive but low on credits. Services need restart after funding.", chat_id)
    elif text == "/health":
        send_message("📊 Health: 2/5 services up. Local services need Conway credits to run.", chat_id)
    elif text == "/repos":
        send_message("📦 Active repos: council, link-preview, poke-bot, health-dashboard", chat_id)
    elif text == "/briefing":
        send_message(get_daily_briefing(), chat_id)

if __name__ == "__main__":
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            handle_update(body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "service": "poke-telegram-bot",
                "v": 1,
                "status": "awaiting_funding"
            }).encode())

        def log_message(self, format, *args):
            pass  # Suppress logs

    print(f"🐾 Telegram bot webhook server starting on port {PORT}")
    print(f"   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars")
    print(f"   Health: http://localhost:{PORT}/")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
