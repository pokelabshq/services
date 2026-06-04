#!/usr/bin/env python3
"""Poke CLI — command-line toolkit for Poke Labs developer services.

Usage:
  poke shorten <url>           Shorten a URL
  poke preview <url>           Get link preview metadata
  poke status                  Check Poke Labs service status
  poke hash <text>             Generate a hash
  poke uuid                    Generate a UUID
  poke timestamp [unix]        Current or convert Unix timestamp
  poke qr <text>               Generate QR code (ASCII)
  poke sentiment <text>        Analyze sentiment
  poke --version               Show version
"""

import sys
import os
import json
import hashlib
import uuid
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

VERSION = "1.0.0"
BASE_URL = os.environ.get("POKE_API_URL", "https://api.pokelabs.org")

def api_post(path, data):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try: return {"error": json.loads(body).get("error", body)}
        except: return {"error": body}
    except Exception as e:
        return {"error": str(e)}

def api_get(path):
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}{path}", timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def cmd_shorten(args):
    if not args:
        print("Usage: poke shorten <url> [--custom <code>]")
        sys.exit(1)
    url = args[0]
    custom = None
    if "--custom" in args:
        idx = args.index("--custom")
        if idx + 1 < len(args):
            custom = args[idx + 1]
    data = {"url": url}
    if custom:
        data["code"] = custom
    result = api_post("/api/shorten", data)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    print(f"Short URL: {result.get('short_url', '/')}{result.get('code', '')}")
    print(f"Original:  {result['url']}")
    if result.get('existing'):
        print("(already existed)")

def cmd_preview(args):
    if not args:
        print("Usage: poke preview <url>")
        sys.exit(1)
    result = api_post("/api/preview", {"url": args[0]})
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    print(f"Title:       {result.get('title', 'N/A')}")
    print(f"Description: {result.get('description', 'N/A')}")
    print(f"Image:       {result.get('image', 'N/A')}")
    print(f"Site:        {result.get('site_name', 'N/A')}")

def cmd_status():
    result = api_get("/api/status")
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    overall = result.get("overall", "unknown")
    icons = {"up": "🟢", "degraded": "🟡", "down": "🔴"}
    print(f"Poke Labs Status: {icons.get(overall, '❓')} {overall.upper()}")
    for svc in result.get("services", []):
        s = svc.get("status", "?")
        print(f"  {icons.get(s, '❓')} {svc['name']}: {s} ({svc.get('ms', '?')}ms)")

def cmd_hash(args):
    if not args:
        print("Usage: poke hash <text> [--algo md5|sha1|sha256]")
        sys.exit(1)
    text = args[0]
    algo = "sha256"
    if "--algo" in args:
        idx = args.index("--algo")
        if idx + 1 < len(args):
            algo = args[idx + 1]
    h = hashlib.new(algo, text.encode()).hexdigest()
    print(h)

def cmd_uuid():
    print(str(uuid.uuid4()))

def cmd_timestamp(args):
    if args:
        try:
            ts = int(args[0])
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            print(f"Unix: {ts}")
            print(f"UTC:  {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except ValueError:
            print(f"Invalid timestamp: {args[0]}", file=sys.stderr)
            sys.exit(1)
    else:
        now = int(time.time())
        print(f"Unix: {now}")
        print(f"UTC:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")

def cmd_qr(args):
    if not args:
        print("Usage: poke qr <text>")
        sys.exit(1)
    text = " ".join(args)
    # Simple ASCII QR using qrencode if available, else fallback
    import subprocess
    try:
        result = subprocess.run(["qrencode", "-t", "ANSIUTF8", "-o", "-", text],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(result.stdout)
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        # Fallback: just print the text with a box
        print(f"┌{'─' * (len(text) + 2)}┐")
        print(f"│ {text} │")
        print(f"└{'─' * (len(text) + 2)}┘")
        print("(Install qrencode for real QR codes)")

def cmd_sentiment(args):
    if not args:
        print("Usage: poke sentiment <text>")
        sys.exit(1)
    text = " ".join(args)
    # Simple local sentiment (no API needed)
    positive = ["good","great","awesome","excellent","amazing","love","best","happy","nice","cool","fantastic","wonderful","perfect","brilliant"]
    negative = ["bad","terrible","awful","horrible","hate","worst","sad","angry","ugly","poor","disappointing","broken","useless"]
    words = text.lower().split()
    pos = sum(1 for w in words if w in positive)
    neg = sum(1 for w in words if w in negative)
    total = pos + neg
    if total == 0:
        print("😐 Neutral (no sentiment words detected)")
    elif pos > neg:
        score = pos / total
        emoji = "😄" if score > 0.7 else "🙂"
        print(f"{emoji} Positive ({pos}/{total} positive words)")
    else:
        score = neg / total
        emoji = "😡" if score > 0.7 else "🙁"
        print(f"{emoji} Negative ({neg}/{total} negative words)")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__.strip())
        sys.exit(0)
    if sys.argv[1] in ("--version", "-v"):
        print(f"poke v{VERSION}")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "shorten": cmd_shorten,
        "preview": cmd_preview,
        "status": cmd_status,
        "hash": cmd_hash,
        "uuid": cmd_uuid,
        "timestamp": cmd_timestamp,
        "qr": cmd_qr,
        "sentiment": cmd_sentiment,
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Available: {', '.join(commands.keys())}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
