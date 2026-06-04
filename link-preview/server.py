#!/usr/bin/env python3
"""Link Preview API — Extract title, description, image from any URL."""
import http.server, json, re, ssl, urllib.request, urllib.error
from html.parser import HTMLParser

PORT = 8765

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
        self.send_html(LANDING)

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

LANDING = """<!DOCTYPE html>
<html><head><title>Link Preview API</title>
<style>
body{font-family:system-ui;background:#0a0a1a;color:#e0e0e0;max-width:700px;margin:4rem auto;padding:0 2rem}
h1{color:#6c63ff}code{background:#1a1a3e;padding:.2rem .5rem;border-radius:4px;font-size:.9rem}
pre{background:#12122a;padding:1.5rem;border-radius:8px;overflow-x:auto}
input{padding:.75rem;width:100%;background:#1a1a3e;color:#e0e0e0;border:1px solid #6c63ff;border-radius:8px;font-size:1rem;box-sizing:border-box}
button{background:#6c63ff;color:#fff;border:none;padding:.75rem 2rem;border-radius:8px;cursor:pointer;margin-top:.75rem;font-size:1rem}
button:hover{transform:scale(1.02)}
</style></head>
<body>
<h1>🔗 Link Preview API</h1>
<p>Extract title, description, and image from any URL.</p>
<pre>POST /api/preview
Content-Type: application/json

{"url": "https://github.com"}</pre>
<input id="url" placeholder="https://github.com" value="https://github.com">
<button onclick="go()">Preview</button>
<pre id="out">{}</pre>
<script>
async function go(){
  const url=document.getElementById('url').value;
  const r=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
  document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2);
}
</script>
</body></html>"""

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Link Preview API on :{PORT}")
    server.serve_forever()
