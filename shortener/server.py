#!/usr/bin/env python3
"""Poke Labs URL Shortener — simple in-memory URL shortener with analytics."""
import json, os, hashlib, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import string, random

PORT = int(os.environ.get("PORT", 8767))
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.json")

# In-memory store: {short_code: {url, created, clicks, ips}}
_store = {}
_lock = threading.Lock()

def load_store():
    global _store
    try:
        with open(DATA_FILE) as f:
            _store = json.load(f)
    except:
        _store = {}

def save_store():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(_store, f, indent=2)
    except:
        pass

def gen_code(url, length=6):
    """Generate a short code from URL hash + random suffix."""
    h = hashlib.md5(url.encode()).hexdigest()[:4]
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length-4))
    return h + r

def check_url(url):
    """Verify URL is reachable."""
    try:
        r = urlopen(Request(url, method="HEAD"), timeout=5)
        return True
    except:
        return True  # Allow unreachable URLs (might be temporary)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        
        # API: /api/health
        if path == "/api/health":
            body = json.dumps({"ok": True, "v": 1, "urls": len(_store)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        
        # API: /api/list
        if path == "/api/list":
            with _lock:
                items = [{"code": k, "url": v["url"], "clicks": v.get("clicks", 0),
                          "created": v.get("created", "")} for k, v in _store.items()]
            body = json.dumps({"urls": items, "count": len(items)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        
        # API: /api/stats/{code}
        if path.startswith("/api/stats/"):
            code = path[len("/api/stats/"):]
            with _lock:
                entry = _store.get(code)
            if not entry:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "not found"}).encode())
                return
            body = json.dumps({
                "code": code, "url": entry["url"],
                "clicks": entry.get("clicks", 0),
                "created": entry.get("created", ""),
                "unique_ips": len(entry.get("ips", [])),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        
        # Redirect: /{code}
        if path != "/" and not path.startswith("/api/"):
            code = path.lstrip("/")
            with _lock:
                entry = _store.get(code)
            if entry:
                entry["clicks"] = entry.get("clicks", 0) + 1
                ips = entry.get("ips", [])
                ip = self.client_address[0]
                if ip not in ips:
                    ips.append(ip)
                entry["ips"] = ips
                save_store()
                self.send_response(302)
                self.send_header("Location", entry["url"])
                self.end_headers()
                return
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>404 - Not Found</h1><p>Short URL does not exist.</p>")
                return
        
        # Landing page
        self.serve_home()
    
    def do_POST(self):
        path = self.path.rstrip("/")
        
        if path == "/api/shorten":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "invalid JSON"}).encode())
                return
            
            url = data.get("url", "").strip()
            custom = data.get("code", "").strip()
            
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "url required"}).encode())
                return
            
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            
            # Validate URL format
            parsed = urlparse(url)
            if not parsed.netloc:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "invalid URL"}).encode())
                return
            
            with _lock:
                # Check if URL already exists
                for code, entry in _store.items():
                    if entry["url"] == url:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "code": code, "url": url, "short_url": f"/{code}",
                            "existing": True
                        }).encode())
                        return
                
                if custom:
                    if custom in _store:
                        self.send_response(409)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "code already taken"}).encode())
                        return
                    code = custom
                else:
                    code = gen_code(url + str(time.time()))
                    while code in _store:
                        code = gen_code(url + str(time.time()) + str(random.random()))
                
                _store[code] = {
                    "url": url,
                    "created": datetime.now(timezone.utc).isoformat(),
                    "clicks": 0,
                    "ips": [],
                }
                save_store()
            
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "code": code, "url": url, "short_url": f"/{code}",
                "existing": False
            }).encode())
            return
        
        self.send_response(404)
        self.end_headers()
    
    def serve_home(self):
        with _lock:
            count = len(_store)
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Labs URL Shortener</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem; }}
h1 {{ font-size: 2rem; margin-bottom: 0.5rem; color: #8b5cf6; }}
.sub {{ color: #888; margin-bottom: 2rem; }}
.card {{ background: #161616; border: 1px solid #333; border-radius: 12px; padding: 2rem; width: 100%; max-width: 500px; }}
input {{ width: 100%; padding: 0.75rem 1rem; background: #0a0a0a; border: 1px solid #333; border-radius: 8px; color: #e0e0e0; font-size: 1rem; margin-bottom: 0.75rem; }}
input:focus {{ outline: none; border-color: #8b5cf6; }}
button {{ width: 100%; padding: 0.75rem; background: #8b5cf6; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: bold; cursor: pointer; }}
button:hover {{ background: #7c3aed; }}
.result {{ margin-top: 1rem; padding: 1rem; background: #0a0a0a; border-radius: 8px; display: none; }}
.result a {{ color: #8b5cf6; word-break: break-all; }}
.stats {{ margin-top: 2rem; color: #666; font-size: 0.85rem; }}
</style>
</head>
<body>
<h1>Poke Labs</h1>
<p class="sub">URL Shortener</p>
<div class="card">
    <input type="text" id="url" placeholder="Paste a long URL..." />
    <input type="text" id="custom" placeholder="Custom code (optional)" />
    <button onclick="shorten()">Shorten</button>
    <div class="result" id="result"></div>
</div>
<p class="stats">{count} URLs shortened · <a href="/api/list" style="color:#8b5cf6;">API</a></p>
<script>
async function shorten() {{
    const url = document.getElementById('url').value.trim();
    const custom = document.getElementById('custom').value.trim();
    if (!url) return alert('Enter a URL');
    const res = await fetch('/api/shorten', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{url, code: custom || undefined}})
    }});
    const data = await res.json();
    const el = document.getElementById('result');
    if (res.ok) {{
        el.style.display = 'block';
        el.innerHTML = `<p>${{data.existing ? 'Already exists!' : 'Shortened!'}}</p><a href="/${{data.code}}" target="_blank">/${{data.code}}</a>`;
    }} else {{
        el.style.display = 'block';
        el.innerHTML = `<p style="color:#ef4444;">Error: ${{data.error}}</p>`;
    }}
}}
</script>
</body>
</html>"""
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    load_store()
    print(f"URL Shortener on :{PORT} ({len(_store)} URLs loaded)", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
