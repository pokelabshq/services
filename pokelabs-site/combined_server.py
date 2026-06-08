#!/usr/bin/env python3
\"\"\"Poke Labs Combined Server v1.0 — Serves landing page + Link Preview API.\"\"\"
import http.server, json, re, urllib.request, urllib.parse, html, os, time, socket

PORT = int(os.environ.get("PORT", 8766))
FREE_LIMIT = 3
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
ips = {}
reqs_24h = []

def get_ip(h):
    return h.headers.get("X-Forwarded-For", h.client_address[0])

def check_limit(ip):
    now = time.time()
    reqs_24h[:] = [t for t in reqs_24h if now - t < 86400]
    return ips.get(ip, 0) < FREE_LIMIT

def extract_meta(url, content):
    def og(p):
        m = re.search(r'og:' + p + r'''["'].*?content=["']([^"']+)''', content, re.I)
        return m.group(1) if m else ""
    tm = re.search(r'<title[^>]*>([^<]+)</title>', content, re.I)
    title = tm.group(1).strip() if tm else og("title") or "No title"
    desc_m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)', content, re.I)
    desc = og("description") or (desc_m.group(1) if desc_m else "No description")
    image = og("image") or ""
    site = og("site_name") or urllib.parse.urlparse(url).netloc
    fm = re.search(r'rel="(?:shortcut )?icon"[^>]*href="([^"]+)', content, re.I)
    fav = ""
    if fm:
        fav = fm.group(1)
        if fav.startswith("/"):
            parsed = urllib.parse.urlparse(url)
            fav = parsed.scheme + "://" + parsed.netloc + fav
    return {
        "title": html.unescape(title),
        "description": html.unescape(desc),
        "image": image,
        "site_name": site,
        "favicon": fav,
        "url": url
    }

DASH_HTML = open("/home/alx/public/index.html").read() if os.path.exists("/home/alx/public/index.html") else "<h1>Poke Labs</h1><p>Dashboard loading...</p>"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html(DASH_HTML)
        elif self.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "wallet": WALLET})
        elif self.path == "/api/usage":
            ip = get_ip(self)
            self.send_json({"used": ips.get(ip, 0), "limit": FREE_LIMIT})
        elif self.path == "/api/stats":
            now = time.time()
            reqs_24h[:] = [t for t in reqs_24h if now - t < 86400]
            unique_ips = len(set(ips.keys()))
            self.send_json({"ips": unique_ips, "reqs_24h": len(reqs_24h), "free_limit": FREE_LIMIT})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/preview":
            self.send_error(404)
            return
        ip = get_ip(self)
        if not check_limit(ip):
            self.send_json({"error": "Free limit reached. Pay via x402.", "wallet": WALLET}, 402)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            url = data["url"]
        except:
            self.send_json({"error": 'Provide {"url": "..."}'}, 400)
            return
        ips[ip] = ips.get(ip, 0) + 1
        reqs_24h.append(time.time())
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PokeBot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode("utf-8", errors="ignore")
            self.send_json(extract_meta(url, content))
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, content):
        body = content.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Labs Combined Server v1.0 on :{PORT}")
    server.serve_forever()
