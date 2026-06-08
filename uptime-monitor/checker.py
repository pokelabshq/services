#!/usr/bin/env python3
"""Poke Labs Uptime Monitor — Checks all service endpoints and reports status."""
import urllib.request, json, time, datetime, os, re, threading

SERVICES_DIR = "/home/alx/services"
CHECK_INTERVAL = 60  # seconds
DATA_FILE = "/tmp/uptime-data.json"

def discover_endpoints():
    endpoints = []
    if not os.path.isdir(SERVICES_DIR):
        return endpoints
    for name in sorted(os.listdir(SERVICES_DIR)):
        skill = os.path.join(SERVICES_DIR, name, "SKILL.md")
        if not os.path.exists(skill):
            continue
        content = open(skill).read()
        port_match = re.search(r'[Pp]ort[:\s]+(\d{4,5})', content)
        if not port_match:
            continue
        port = int(port_match.group(1))
        # Find health endpoint
        health = f"http://localhost:{port}/api/health"
        if re.search(r'health', content, re.IGNORECASE):
            endpoints.append({"name": name, "url": health, "port": port})
        else:
            endpoints.append({"name": name, "url": f"http://localhost:{port}/", "port": port})
    return endpoints

def check_endpoint(ep):
    start = time.time()
    try:
        req = urllib.request.Request(ep["url"], method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        ms = round((time.time() - start) * 1000)
        return {"status": "up", "code": resp.status, "ms": ms}
    except urllib.error.HTTPError as e:
        ms = round((time.time() - start) * 1000)
        return {"status": "degraded" if e.code < 500 else "down", "code": e.code, "ms": ms}
    except Exception as e:
        ms = round((time.time() - start) * 1000)
        return {"status": "down", "code": 0, "ms": ms, "error": str(e)[:100]}

def run_checks():
    endpoints = discover_endpoints()
    results = []
    for ep in endpoints:
        result = check_endpoint(ep)
        result["name"] = ep["name"]
        result["url"] = ep["url"]
        result["checked_at"] = datetime.datetime.now().isoformat()
        results.append(result)
    # Save results
    with open(DATA_FILE, "w") as f:
        json.dump(results, f, indent=2)
    return results

def get_summary():
    if not os.path.exists(DATA_FILE):
        return {"total": 0, "up": 0, "down": 0, "degraded": 0, "checks": []}
    with open(DATA_FILE) as f:
        checks = json.load(f)
    up = sum(1 for c in checks if c["status"] == "up")
    down = sum(1 for c in checks if c["status"] == "down")
    degraded = sum(1 for c in checks if c["status"] == "degraded")
    return {"total": len(checks), "up": up, "down": down, "degraded": degraded, "checks": checks}

if __name__ == "__main__":
    print(f"Checking {len(discover_endpoints())} endpoints...")
    results = run_checks()
    up = sum(1 for r in results if r["status"] == "up")
    print(f"Results: {up}/{len(results)} up")
    for r in results:
        icon = "✅" if r["status"] == "up" else "⚠️" if r["status"] == "degraded" else "❌"
        print(f"  {icon} {r['name']}: {r['status']} ({r['code']}) {r['ms']}ms")
