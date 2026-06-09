#!/usr/bin/env python3
"""
Link Preview API v4.1 — extracts title, description, image from URLs.
Pure Python stdlib. Zero deps.
"""
import http.server, json, re, os, urllib.request, urllib.parse
from http.cookies import SimpleCookie

PORT = 8765

def extract_meta(html, prop):
    """Extract OpenGraph or meta tag content."""
    # Try og:prop pattern
    patterns = [
        r'property="og:' + prop + r'"[^>]*content="([^"]*)"',
        r'content="([^"]*)"[^>]*property="og:' + prop + r'"',
        r'name="' + prop + r'"[^>]*content="([^"]*)"',
        r'content="([^"]*)"[^>]*name="' + prop + r'"',
    ]
    for p in patterns:
        m = re.search(p, html, re.I)
        if m:
            return m.group(1)
    return ""

def get_favicon(html, base_url):
    """Extract favicon URL."""
    patterns = [
        r'rel="shortcut icon"\s+href="([^"]+)"',
        r'rel="icon"\s+href="([^"]+)"',
        r'rel=\'shortcut icon\'\s+href=\'([^\']+)\'',
        r'rel=\'icon\'\s+href=\'([^\']+)\'',
    ]
    for p in patterns:
        m = re.search(p, html, re.I)
        if m:
            href = m.group(1)
            if href.startswith("http"):
                return href
            elif href.startswith("//"):
                return "https:" + href
            elif href.startswith("/"):
                parsed = urllib.parse.urlparse(base_url)
                return f"{parsed.scheme}://{parsed.netloc}{href}"
    # Default favicon
    parsed = urllib.parse.urlparse(base_url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.serve_file("public/index.html", "text/html")
        elif self.path == "/api/health":
            self.send_json({"ok": True, "v": 4.1, "free_limit": 3})
        elif self.path == "/api/usage":
            self.send_json({"used": 0, "limit": 3})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/api/preview":
            self.send_response(404); self.end_headers(); return
        
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except:
            self.send_json({"error": "Invalid JSON"}, 400); return
        
        url = data.get("url", "").strip()
        if not url:
            self.send_json({"error": "Provide url"}, 400); return
        if not url.startswith("http"):
            url = "https://" + url

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PokeBot/4.1"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
            title = title_m.group(1).strip() if title_m else extract_meta(html, "title") or "No title"
            desc = extract_meta(html, "description") or "No description"
            image = extract_meta(html, "image") or ""
            site = extract_meta(html, "site_name") or urllib.parse.urlparse(url).netloc
            fav = get_favicon(html, url)

            self.send_json({
                "ok": True,
                "title": title,
                "description": desc,
                "image": image or None,
                "site_name": site,
                "favicon": fav,
                "url": url
            })
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def serve_file(self, path, content_type):
        full = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full):
            with open(full) as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode())
        else:
            self.send_response(404); self.end_headers()

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Link Preview API: http://localhost:{PORT}/", flush=True)
    server.serve_forever()
