#!/usr/bin/env python3
"""PTelegram v1.0 — Daily briefing sender for Poke Labs."""
import json, urllib.request, urllib.parse, datetime, os, subprocess, sys

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
BASE = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""

def api(method, data=None):
    if not BASE: return {}
    url = f"{BASE}/{method}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read())
    except: return {}

def send(text):
    return api("sendMessage", {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})

def morning_briefing():
    now = datetime.datetime.utcnow().strftime("%B %d, %Y")
    repos, issues = [], []
    try:
        r = subprocess.run(["gh","api","users/pokelabshq/repos","--jq",".[] | {name,open_issues: .open_issues_count,stars: .stargazers_count}"], capture_output=True, text=True, timeout=10)
        repos = [json.loads(l) for l in r.stdout.strip().split('\n') if l.strip()][:5]
    except: pass
    try:
        r = subprocess.run(["gh","search","issues","--repo","pokelabshq/services","--state","open","--limit","5","--json","number,title"], capture_output=True, text=True, timeout=10)
        issues = json.loads(r.stdout) if r.stdout.strip() else []
    except: pass

    m = f"🌅 <b>Poke Labs Briefing</b>\n📅 {now}\n\n📊 <b>Repos:</b>\n"
    for r in repos:
        m += f"  • <code>{r.get('name','?')}</code> ⭐{r.get('stars',0)} 🐛{r.get('open_issues',0)}\n"
    m += "\n🐛 <b>Issues:</b>\n"
    for i in issues[:5]:
        m += f"  • #{i.get('number','?')} {i.get('title','?')[:50]}\n"
    m += "\n💰 <b>Funding:</b> $35 USDC needed\n   <code>0xca3d86...beF</code> (Base)\n"
    m += f"\n📦 github.com/pokelabshq/services\n— Poke 🤖"
    return m

if __name__ == "__main__":
    if "--send" in sys.argv: send(morning_briefing())
    else: print(morning_briefing())
