#!/usr/bin/env python3
"""Uptime Monitor for Poke Labs. Stdlib only."""
import http.client, json, os, ssl, sys, time
from datetime import datetime, timezone
from urllib.parse import urlparse

CHECK_URLS = ["https://pokelabs.org", "https://ai-council.pokelabs.com"]
TIMEOUT = 10
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
MAX_HISTORY = 1000
os.makedirs(DATA_DIR, exist_ok=True)

def check_url(url):
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"
    host = parsed.hostname
    port = parsed.port or (443 if is_https else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    start = time.time()
    status_code = None
    error = None
    try:
        if is_https:
            ctx = ssl.create_default_context()
            conn = http.client.HTTPSConnection(host, port, timeout=TIMEOUT, context=ctx)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
        conn.request("GET", path, headers={"User-Agent": "PokeLabs-UptimeBot/1.0"})
        resp = conn.getresponse()
        status_code = resp.status
        resp.read(1024)
        conn.close()
    except Exception as e:
        error = str(e)
    elapsed_ms = round((time.time() - start) * 1000)
    is_up = status_code is not None and 200 <= status_code < 400
    return {
        "url": url,
        "status_code": status_code,
        "response_time_ms": elapsed_ms,
        "is_up": is_up,
        "error": error,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {}

def save_history(h):
    for url in h:
        if len(h[url]) > MAX_HISTORY:
            h[url] = h[url][-MAX_HISTORY:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)

def run_checks():
    history = load_history()
    results = []
    for url in CHECK_URLS:
        r = check_url(url)
        results.append(r)
        history.setdefault(url, []).append(r)
    save_history(history)
    return results

def run_server():
    port = int(os.environ.get("PORT", 8766))
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            elif self.path in ("/api/check", "/api/status"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(run_checks(), indent=2).encode())
            elif self.path == "/":
                results = run_checks()
                html = "<html><head><title>Poke Labs Uptime</title></head><body>"
                html += "<h1>Poke Labs Uptime Monitor</h1><pre>"
                for r in results:
                    icon = "OK" if r["is_up"] else "FAIL"
                    html += f"{icon} {r['url']} | {r['status_code']} | {r['response_time_ms']}ms\n"
                html += f"\nChecked at: {datetime.now(timezone.utc).isoformat()}"
                html += "</pre></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, *a):
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Uptime monitor running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode == "check":
        for r in run_checks():
            s = "UP" if r["is_up"] else "DOWN"
            print(f"{s} | {r['url']} | {r['status_code']} | {r['response_time_ms']}ms")
    elif mode == "json":
        print(json.dumps(run_checks(), indent=2))
    elif mode == "server":
        run_server()
