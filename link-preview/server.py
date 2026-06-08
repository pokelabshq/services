
#!/usr/bin/env python3
"""Link Preview API v4 — Extract title, description, image from URLs.
Zero dependencies. Free tier: 3/day per IP. x402 USDC for unlimited."""
import http.server, json, re, urllib.request, urllib.parse, html, os, time, socket

PORT = 8765
FREE_LIMIT = 3
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
ips = {}
reqs = []

def get_ip(h):
    return h.headers.get("X-Forwarded-For", h.client_address[0])

def check_limit(ip):
    now = time.time()
    reqs[:] = [t for t in reqs if now - t < 86400]
    ips[ip] = ips.get(ip, 0)
    return ips[ip] < FREE_LIMIT

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok": True, "v": 4, "free_limit": FREE_LIMIT})
        elif self.path == "/api/usage":
            ip = get_ip(self)
            n = sum(1 for t in reqs if t > time.time() - 86400)
            self.send_json({"used": ips.get(ip, 0), "limit": FREE_LIMIT})
        elif self.path == "/":
            self.send_html(LANDING)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/preview":
            self.send_error(404); return
        ip = get_ip(self)
        if not check_limit(ip):
            self.send_json({"error": "Free limit reached. Pay via x402 for unlimited.", "wallet": WALLET}, 402); return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            url = data["url"]
        except:
            self.send_json({"error": "Provide {"url": "..."}"}, 400); return
        ips[ip] = ips.get(ip, 0) + 1
        reqs.append(time.time())
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PokeBot/4.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode("utf-8", errors="ignore")
            def og(prop):
                m = re.search(r"og:" + prop + r"["'].*?content=["']([^"']+)", content, re.I)
                return m.group(1) if m else ""
            tm = re.search(r"<title[^>]*>([^<]+)</title>", content, re.I)
            title = tm.group(1).strip() if tm else og("title") or "No title"
            desc = og("description") or re.search(r"<meta[^>]*name="description"[^>]*content="([^"]+)", content, re.I)
            desc = desc.group(1) if hasattr(desc, "group") else (desc or "No description")
            image = og("image") or ""
            site = og("site_name") or urllib.parse.urlparse(url).netloc
            fav = ""
            fm = re.search(r"rel="(?:shortcut )?icon"[^>]*href="([^"]+)", content, re.I)
            if fm:
                fav = fm.group(1)
                if fav.startswith("/"): fav = urllib.parse.urlparse(url).scheme + "://" + urllib.parse.urlparse(url).netloc + fav
            title = html.unescape(title)
            desc = html.unescape(desc)
            self.send_json({"title": title, "description": desc, "image": image, "site_name": site, "favicon": fav, "url": url})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html_content):
        body = html_content.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

LANDING = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Link Preview API</title>
<style>body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:40px;max-width:700px;margin:0 auto}
h1{color:#00d4ff}code{background:#141420;padding:2px 8px;border-radius:4px;font-size:13px}
pre{background:#141420;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px}
.btn{background:#238636;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin:8px 0}
.card{background:#141420;border:1px solid #2a2a3a;border-radius:8px;padding:16px;margin:12px 0}
</style></head>
<body>
<h1>📦 Link Preview API v4</h1>
<p>Extract title, description, image, favicon from any URL. Zero dependencies. Pure Python.</p>
<div class="card"><strong>Free:</strong> 3 requests/day per IP | <strong>Unlimited:</strong> x402 USDC (Base)</div>
<h2>Try It</h2>
<pre>curl -X POST http://localhost:8765/api/preview   -H "Content-Type: application/json"   -d '{"url": "https://github.com"}'</pre>
<h2>Response</h2>
<pre>{"title": "GitHub", "description": "Where the world builds software", "image": "https://...", "site_name": "github.com", "favicon": "https://...", "url": "https://github.com"}</pre>
<h2>Pricing</h2>
<div class="card">Free: 3/day | Hacker  | Pro 5 | Enterprise 00/Wallet: 0xca3d...6beF (Base)</div>
</body></html>"""

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Link Preview API v4 on :{PORT}")
    server.serve_forever()
