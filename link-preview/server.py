#!/usr/bin/env python3
"""Link Preview API — Extract title, description, image from any URL."""
import http.server
import os, json, re, ssl, urllib.request, urllib.error
from html.parser import HTMLParser

PORT = 8765
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.image = ""
        self.site_name = ""
        self.favicon = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            prop = attrs_dict.get("property", "").lower()
            name = attrs_dict.get("name", "").lower()
            content = attrs_dict.get("content", "")
            if prop == "og:title" or name == "title":
                if not self.title:
                    self.title = content
            elif prop == "og:description" or name == "description":
                if not self.description:
                    self.description = content
            elif prop == "og:image" or name == "twitter:image":
                if not self.image:
                    self.image = content
            elif prop == "og:site_name":
                if not self.site_name:
                    self.site_name = content
        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if "icon" in rel and not self.favicon:
                self.favicon = attrs_dict.get("href", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()

def extract(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; PokeBot/1.0)"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=8, context=ctx)
        charset = "utf-8"
        ct = resp.headers.get("Content-Type", "")
        m = re.search(r"charset=([\w-]+)", ct)
        if m:
            charset = m.group(1)
        html = resp.read(65536).decode(charset, errors="replace")
        p = MetaParser()
        p.feed(html)
        # Resolve relative favicon
        if p.favicon and p.favicon.startswith("/"):
            from urllib.parse import urljoin
            p.favicon = urljoin(url, p.favicon)
        if p.image and p.image.startswith("/"):
            from urllib.parse import urljoin
            p.image = urljoin(url, p.image)
        return {
            "title": p.title,
            "description": p.description,
            "image": p.image,
            "site_name": p.site_name,
            "favicon": p.favicon,
            "url": url
        }
    except Exception as e:
        return {"error": str(e), "url": url}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/api/health", "/health"):
            self.send_json({"ok": True, "v": 4})
            return
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        q = parse_qs(u.query)
        url = q.get("url", [None])[0]
        if url:
            self.send_json(extract(url))
            return
        # Serve static files from public/
        path = u.path.split("?")[0]
        if path == "/": path = "/index.html"
        filepath = os.path.join(PUBLIC_DIR, path.lstrip("/"))
        if os.path.isfile(filepath):
            ct = "text/html"
            if filepath.endswith(".css"): ct = "text/css"
            elif filepath.endswith(".js"): ct = "application/javascript"
            elif filepath.endswith(".png"): ct = "image/png"
            with open(filepath, "rb") as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/preview":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            url = body.get("url", "")
            if not url:
                self.send_json({"error": "url required"}, 400)
                return
            self.send_json(extract(url))
            return
        self.send_json({"error": "Not found"}, 404)

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Link Preview API on :{PORT}")
    server.serve_forever()
