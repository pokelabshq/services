#!/usr/bin/env python3
"""Quick health check for all running services."""
import json, sys
from urllib.request import urlopen
from urllib.error import URLError

SERVICES = {
    "billing": 8766,
    "dashboard": 8780,
    "link-preview": 8765,
    "poke-hub": 8775,
    "service-watchdog": 8799,
    "github-trending": 8788,
    "skill-marketplace-v2": 8790,
}

ok = 0
fail = 0
for name, port in sorted(SERVICES.items()):
    try:
        r = urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3)
        data = json.loads(r.read())
        print(f"  ✅ {name}:{port} - {data}")
        ok += 1
    except Exception as e:
        print(f"  ❌ {name}:{port} - {e}")
        fail += 1

print(f"\n{ok} healthy, {fail} down")
sys.exit(0 if fail == 0 else 1)
