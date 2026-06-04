#!/usr/bin/env python3
"""Poke Labs Telegram Bot — Daily briefings, repo monitoring, uptime alerts.
Usage: BOT_TOKEN=xxx python3 bot.py"""
import json, os, sys, time, subprocess
from urllib.request import urlopen, Request
from urllib.parse import quote

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("BOT_PORT", "8768"))
DATA_FILE = "/home/alx/services/telegram-bot/data.json"

def load_data():
    try: return json.load(open(DATA_FILE))
    except: return {"chats": [], "last_daily": ""}

def save_data(d):
    json.dump(d, open(DATA_FILE, "w"))

def api(method, data=None):
    if not BOT_TOKEN:
        print(f"[BOT] No token — would call {method}: {data}", flush=True)
        return {"ok": False, "error": "no token"}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    try:
        r = urlopen(Request(url, data=body, headers=headers), timeout=15)
        return json.loads(r.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_message(chat_id, text):
    return api("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset: params["offset"] = offset
    return api("getUpdates", params)

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    chat_type = msg["chat"].get("type", "")

    if text == "/start":
        send_message(chat_id, "🦉 <b>Poke Labs Bot</b>\n\nI'm your daily briefing assistant.\n\nCommands:\n/status — System status\n/repos — Repo overview\n/prs — Open PRs\n/uptime — Service health\n/help — All commands")
    elif text == "/help":
        send_message(chat_id, "📋 <b>Commands</b>\n\n/status — Credits, uptime, version\n/repos — Monitored repos\n/prs — Open pull requests\n/uptime — Service health checks\n/briefing — Full daily briefing\n/help — This message")
    elif text == "/status":
        # Get Conway status
        try:
            result = subprocess.run(["python3", "-c", """
import json, urllib.request
try:
    r = urllib.request.urlopen("http://localhost:8765/api/health", timeout=5)
    lp = json.loads(r.read())
except: lp = {"ok": False}
print(json.dumps(lp))
"""], capture_output=True, text=True, timeout=10)
            lp_status = json.loads(result.stdout.strip()).get("ok", False)
        except: lp_status = False

        status_text = f"🦉 <b>Poke Labs Status</b>\n\n"
        status_text += f"Link Preview API: {'✅' if lp_status else '❌'}\n"
        status_text += f"Bot: ✅ Running\n"
        status_text += f"Time: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}"
        send_message(chat_id, status_text)
    elif text == "/briefing":
        # Full daily briefing
        briefing = generate_briefing()
        send_message(chat_id, briefing)
    elif text == "/repos":
        send_message(chat_id, "📦 <b>Monitored Repos</b>\n\n• PokeLabshq/council (Python)\n• PokeLabshq/poke (TypeScript)")
    elif text == "/prs":
        send_message(chat_id, "🔀 <b>Open PRs</b>\n\n• council#16 — fix: commit skills-index.json + retry\n• poke#1 — deps update\n\nCheck GitHub for full list.")
    elif text == "/uptime":
        services = []
        for name, port in [("Link Preview", 8765), ("Status Page", 8766)]:
            try:
                r = urlopen(f"http://localhost:{port}/api/health", timeout=3)
                ok = json.loads(r.read()).get("ok", False)
                services.append(f"{name}: {'✅' if ok else '❌'}")
            except:
                services.append(f"{name}: ❌")
        send_message(chat_id, "🏥 <b>Service Health</b>\n\n" + "\n".join(services))
    else:
        send_message(chat_id, f"Unknown command: {text}\nUse /help for available commands.")

def generate_briefing():
    now = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    return f"""🌅 <b>Daily Briefing — {now}</b>

📦 <b>Repos:</b> 2 monitored (council, poke)
🔀 <b>Open PRs:</b> 2 (council#16, poke#1)
⚠️ <b>Issues:</b> council#7 (skills-index-watchdog)

✅ <b>Shipped today:</b>
• council#16 — skills-index commit + retry fix
• Link Preview API v4 with landing page

💰 <b>Credits:</b> Need funding from Alexander

📋 <b>Next:</b>
• Connect Telegram bot token
• Fix ai-council.pokelabs.com
• Review poke PR#1"""

def run_polling():
    print(f"[BOT] Starting polling mode (token: {'set' if BOT_TOKEN else 'NOT SET'})", flush=True)
    offset = None
    data = load_data()

    while True:
        try:
            updates = get_updates(offset)
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    msg = update.get("message") or update.get("edited_message")
                    if msg and msg.get("text"):
                        handle_message(msg)
            elif not updates.get("ok"):
                print(f"[BOT] Update error: {updates.get('error', 'unknown')}", flush=True)
                if "no token" in str(updates.get("error", "")):
                    print("[BOT] Set BOT_TOKEN env var to enable Telegram", flush=True)
                    time.sleep(60)
                    continue
        except Exception as e:
            print(f"[BOT] Error: {e}", flush=True)
        time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "briefing":
        print(generate_briefing())
    else:
        run_polling()
