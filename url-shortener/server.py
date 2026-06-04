#!/usr/bin/env python3
"""Poke Labs — URL Shortener API. Port 8772.
Shorten URLs, track clicks, custom slugs. Free tier: 3/day. Paid via x402."""
import http.server, json, os, re, string, random, urllib.parse, urllib.request
from datetime import date, datetime

PORT = 8772
FREE_LIMIT = 3
DATA_FILE = "/tmp/url_shortener_data.json"
USAGE_FILE = "/tmp/url_usage.json"

def load_data():
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except: return {"urls": {}, "clicks": {}}

def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f, indent=2)

def load_usage():
    try:
        with open(USAGE_FILE) as f: return json.load(f)
    except: return {}

def save_usage(u):
    with open(USAGE_FILE, "w") as f: json.dump(u, f)

def client_ip(h):
    xff = h.get("X-Forwarded-For","")
    return xff.split(",")[0].strip() if xff else h.get("Remote-Addr","127.0.0.1")

def check_limit(ip):
    u = load_usage(); today = str(date.today())
    if u.get("_date") != today: u = {"_date": today}
    used = u.get(ip, 0)
    if used >= FREE_LIMIT:
        return False, used
    u[ip] = used + 1; save_usage(u); return True, used + 1

def gen_slug(length=6):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))

def is_valid_url(url):
    return re.match(r'^https?://[^\s/$.?#].[^\s]*$', url, re.IGNORECASE) is not None

WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
BASE_URL = f"http://localhost:{PORT}"

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)

        # Redirect short URLs: /s/XXXXXX
        m = re.match(r'^/s/([a-z0-9]+)$', p.path)
        if m:
            slug = m.group(1)
            data = load_data()
            if slug in data["urls"]:
                # Track click
                data["clicks"][slug] = data["clicks"].get(slug, 0) + 1
                save_data(data)
                self.send_response(302)
                self.send_header("Location", data["urls"][slug]["url"])
                self.end_headers()
                return
            self._j({"error": "not found"}, 404); return

        if p.path in ("/", "/index.html"):
            self._html(LANDING); return
        if p.path == "/api/health":
            self._j({"ok":True,"v":1,"service":"url-shortener","free_limit":FREE_LIMIT}); return
        if p.path == "/api/usage":
            ip = client_ip(self.headers)
            u = load_usage(); today = str(date.today())
            used = u.get(ip, 0) if u.get("_date") == today else 0
            self._j({"used":used,"limit":FREE_LIMIT,"remaining":max(0,FREE_LIMIT-used)}); return
        if p.path == "/api/stats":
            slug = qs.get("slug",[""])[0]
            if not slug:
                self._j({"error":"missing slug"}, 400); return
            data = load_data()
            if slug not in data["urls"]:
                self._j({"error":"not found"}, 404); return
            entry = data["urls"][slug]
            clicks = data["clicks"].get(slug, 0)
            self._j({"slug":slug,"url":entry["url"],"clicks":clicks,"created":entry.get("created","")}); return
        if p.path == "/api/list":
            data = load_data()
            urls = [{"slug":k,"url":v["url"],"clicks":data["clicks"].get(k,0),"created":v.get("created","")} for k,v in data["urls"].items()]
            self._j({"urls":urls,"count":len(urls)}); return
        self._j({"error":"not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {}

        if p.path == "/api/shorten":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            url = body.get("url", "")
            slug = body.get("slug", "")
            if not url:
                self._j({"error":"missing url"}, 400); return
            if not is_valid_url(url):
                self._j({"error":"invalid url — must start with http:// or https://"}, 400); return
            data = load_data()
            # Generate or validate slug
            if slug:
                if not re.match(r'^[a-z0-9]{3,20}$', slug):
                    self._j({"error":"slug must be 3-20 lowercase alphanumeric chars"}, 400); return
                if slug in data["urls"]:
                    self._j({"error":"slug already taken"}, 409); return
            else:
                for _ in range(20):
                    slug = gen_slug()
                    if slug not in data["urls"]: break
            data["urls"][slug] = {"url": url, "created": datetime.now().isoformat()}
            data["clicks"][slug] = 0
            save_data(data)
            self._j({
                "slug": slug,
                "short_url": f"{BASE_URL}/s/{slug}",
                "original_url": url,
                "remaining": FREE_LIMIT - used
            }, 201)
            return
        self._j({"error":"not found"}, 404)

    def do_DELETE(self):
        p = urllib.parse.urlparse(self.path)
        m = re.match(r'^/api/delete/([a-z0-9]+)$', p.path)
        if m:
            slug = m.group(1)
            data = load_data()
            if slug in data["urls"]:
                del data["urls"][slug]
                data["clicks"].pop(slug, None)
                save_data(data)
                self._j({"deleted": slug}); return
            self._j({"error":"not found"}, 404); return
        self._j({"error":"not found"}, 404)

    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)

    def _x402(self):
        body = json.dumps({"error":"free limit exceeded","wallet":WALLET,"chain":"base","token":"USDC","x402":True}).encode()
        self.send_response(402); self.send_header("Content-Type","application/json")
        self.send_header("X-Payment-Required","USDC"); self.send_header("X-Payment-Wallet", WALLET)
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(body)

    def _html(self, content):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.end_headers(); self.wfile.write(content.encode())

    def log_message(self, *a): pass

LANDING = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>URL Shortener — Poke Labs</title>
<style>body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem;max-width:800px;margin:0 auto}
h1{color:#7b2ff7}code{background:#1a1a2e;padding:.2rem .5rem;border-radius:4px;font-size:.9rem}
.card{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;margin:1rem 0}
.endpoint{color:#00d4ff;font-weight:bold}.free{color:#4ade80}.paid{color:#fbbf24}
a{color:#7b2ff7}input,button{padding:.5rem;margin:.25rem;border-radius:4px;border:1px solid #2a2a4a;background:#0a0a0f;color:#e0e0e0}
button{background:#7b2ff7;border:none;cursor:pointer}</style></head><body>
<h1>🔗 URL Shortener</h1>
<p>Shorten URLs with click tracking. Custom slugs. Free tier + x402.</p>
<div class="card">
<div class="endpoint">POST /api/shorten</div>
<p>Body: {"url": "https://example.com", "slug": "optional"}</p>
<form onsubmit="shorten(event)">
<input id="url" type="text" placeholder="https://example.com" size=40>
<input id="slug" type="text" placeholder="custom-slug (optional)" size=20>
<button type="submit">Shorten</button>
</form>
<pre id="result"></pre>
</div>
<div class="card">
<div class="endpoint">GET /api/stats?slug=XXXXXX</div>
<p>Get click stats for a short URL.</p>
</div>
<div class="card">
<div class="endpoint">GET /s/XXXXXX</div>
<p>Redirect to original URL.</p>
</div>
<p><span class="free">✓ 3 free/day</span> · <span class="paid">💰 Unlimited via x402</span></p>
<p>Wallet: <code>0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code></p>
<script>
async function shorten(e){
  e.preventDefault();
  const url=document.getElementById('url').value;
  const slug=document.getElementById('slug').value;
  const body={url};
  if(slug) body.slug=slug;
  const r=await fetch('/api/shorten',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  document.getElementById('result').textContent=JSON.stringify(d,null,2);
}
</script></body></html>'''

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"URL Shortener on {PORT}"); s.serve_forever()
