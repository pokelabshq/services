#!/usr/bin/env python3
"""Poke Labs — Color Palette API. Port 8771.
Generates color palettes from hex codes or extracts dominant colors from images.
Free tier: 3/day. Paid via x402."""
import http.server, json, hashlib, os, re, urllib.parse, urllib.request
from datetime import date

PORT = 8771
FREE_LIMIT = 3
USAGE_FILE = "/tmp/color_usage.json"

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

def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3: h = h[0]*2+h[1]*2+h[2]*2
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"

def rgb_to_hsl(r, g, b):
    r2, g2, b2 = r/255, g/255, b/255
    mx, mn = max(r2,g2,b2), min(r2,g2,b2)
    l = (mx+mn)/2
    if mx == mn: h = s = 0
    else:
        d = mx-mn; s = d/(2-mx-mn) if l > 0.5 else d/(mx+mn)
        if mx == r2: h = (g2-b2)/d + (6 if g2 < b2 else 0)
        elif mx == g2: h = (b2-r2)/d + 2
        else: h = (r2-g2)/d + 4
        h /= 6
    return (round(h*360), round(s*100), round(l*100))

def generate_palette(base_hex, count=5):
    """Generate a harmonious palette from a base color."""
    r, g, b = hex_to_rgb(base_hex)
    h, s, l = rgb_to_hsl(r, g, b)
    colors = []
    # Analogous + complementary scheme
    offsets = [0, 30, 60, 180, 210, 150, -30, 120, 240, 90]
    count = min(max(count, 2), 10)
    for i in range(count):
        nh = (h + offsets[i % len(offsets)]) % 360
        # Vary lightness slightly
        nl = max(15, min(85, l + (i - count//2) * 8))
        ns = max(20, min(100, s + (i % 3) * 10 - 10))
        # HSL to RGB
        c = (1 - abs(2*nl/100 - 1)) * ns/100
        x = c * (1 - abs((nh/60) % 2 - 1))
        m = nl/100 - c/2
        if nh < 60: r2,g2,b2 = c,x,0
        elif nh < 120: r2,g2,b2 = x,c,0
        elif nh < 180: r2,g2,b2 = 0,c,x
        elif nh < 240: r2,g2,b2 = 0,x,c
        elif nh < 300: r2,g2,b2 = x,0,c
        else: r2,g2,b2 = c,0,x
        cr, cg, cb = int((r2+m)*255), int((g2+m)*255), int((b2+m)*255)
        chex = rgb_to_hex(cr, cg, cb)
        colors.append({
            "hex": chex.upper(),
            "rgb": [cr, cg, cb],
            "hsl": [nh, ns, nl]
        })
    return colors

def extract_from_image_url(url):
    """Try to download image and extract dominant colors (basic)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        if len(data) > 5000000: data = data[:5000000]  # limit
        # Simple: sample pixels from raw bytes for dominant colors
        samples = []
        step = max(1, len(data) // 300)
        for i in range(0, len(data)-2, step):
            samples.append((data[i], data[i+1], data[i+2]))
        # K-means-ish: bucket into 5 dominant colors
        from collections import Counter
        # Quantize to reduce space
        buckets = [(r//32*32, g//32*32, b//32*32) for r,g,b in samples]
        top = Counter(buckets).most_common(5)
        colors = []
        for (r,g,b), cnt in top:
            h,s,l = rgb_to_hsl(r,g,b)
            colors.append({
                "hex": rgb_to_hex(r,g,b).upper(),
                "rgb": [r,g,b],
                "hsl": [h,s,l],
                "frequency": round(cnt/len(buckets)*100, 1)
            })
        return colors
    except Exception as e:
        return None

def generate_gradient(color1, color2, steps=5):
    """Generate gradient between two colors."""
    r1,g1,b1 = hex_to_rgb(color1)
    r2,g2,b2 = hex_to_rgb(color2)
    colors = []
    for i in range(steps):
        t = i / max(steps-1, 1)
        r = int(r1 + (r2-r1)*t)
        g = int(g1 + (g2-g1)*t)
        b = int(b1 + (b2-b1)*t)
        colors.append({
            "hex": rgb_to_hex(r,g,b).upper(),
            "rgb": [r,g,b],
            "hsl": list(rgb_to_hsl(r,g,b))
        })
    return colors

WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)

        if p.path in ("/", "/index.html"):
            self._html(LANDING); return
        if p.path == "/api/health":
            # check_limit not needed for health
            self._j({"ok":True,"v":1,"service":"color-api","free_limit":FREE_LIMIT}); return
        if p.path == "/api/usage":
            ip = client_ip(self.headers)
            u = load_usage(); today = str(date.today())
            used = u.get(ip, 0) if u.get("_date") == today else 0
            self._j({"used":used,"limit":FREE_LIMIT,"remaining":max(0,FREE_LIMIT-used)}); return
        if p.path == "/api/palette":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            color = qs.get("color", ["#7b2ff7"])[0]
            count = int(qs.get("count", [5])[0])
            if not re.match(r'^#?[0-9a-fA-F]{3,6}$', color):
                self._j({"error":"invalid color hex"}, 400); return
            palette = generate_palette(color, count)
            self._j({"base": color.upper(), "palette": palette, "remaining":FREE_LIMIT-used}); return
        if p.path == "/api/gradient":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            c1 = qs.get("from", ["#7b2ff7"])[0]
            c2 = qs.get("to", ["#00d4ff"])[0]
            steps = int(qs.get("steps", [5])[0])
            grad = generate_gradient(c1, c2, steps)
            self._j({"from": c1.upper(), "to": c2.upper(), "gradient": grad, "remaining":FREE_LIMIT-used}); return
        if p.path == "/api/extract":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            url = qs.get("url", [""])[0]
            if not url:
                self._j({"error":"missing url parameter"}, 400); return
            colors = extract_from_image_url(url)
            if colors is None:
                self._j({"error":"could not extract colors from image"}, 422); return
            self._j({"url": url, "dominant_colors": colors, "remaining":FREE_LIMIT-used}); return
        self._j({"error":"not found"}, 404)

    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)

    def _x402(self):
        body = json.dumps({
            "error": "free limit exceeded",
            "wallet": WALLET,
            "chain": "base",
            "token": "USDC",
            "x402": True
        }).encode()
        self.send_response(402); self.send_header("Content-Type","application/json")
        self.send_header("X-Payment-Required","USDC"); self.send_header("X-Payment-Wallet", WALLET)
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(body)

    def _html(self, content):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.end_headers(); self.wfile.write(content.encode())

    def log_message(self, *a): pass

LANDING = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Color Palette API — Poke Labs</title>
<style>body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem;max-width:800px;margin:0 auto}
h1{color:#7b2ff7}code{background:#1a1a2e;padding:.2rem .5rem;border-radius:4px;font-size:.9rem}
.pre{background:#1a1a2e;padding:1rem;border-radius:8px;overflow-x:auto;margin:1rem 0}
.card{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;margin:1rem 0}
.endpoint{color:#00d4ff;font-weight:bold}.free{color:#4ade80}.paid{color:#fbbf24}
a{color:#7b2ff7}</style></head><body>
<h1>🎨 Color Palette API</h1>
<p>Generate beautiful color palettes from hex codes. Extract colors from images. Build gradients. All via API.</p>

<div class="card">
<div class="endpoint">GET /api/palette?color=#7b2ff7&count=5</div>
<p>Generate a harmonious palette from a base color. Returns analogous, complementary, and triadic colors.</p>
<a href="/api/palette?color=#7b2ff7&count=5">Try it →</a>
</div>

<div class="card">
<div class="endpoint">GET /api/gradient?from=#7b2ff7&to=#00d4ff&steps=5</div>
<p>Generate a smooth gradient between two colors.</p>
<a href="/api/gradient?from=#7b2ff7&to=#00d4ff&steps=5">Try it →</a>
</div>

<div class="card">
<div class="endpoint">GET /api/extract?url=IMAGE_URL</div>
<p>Extract dominant colors from an image URL.</p>
</div>

<p><span class="free">✓ 3 free/day</span> · <span class="paid">💰 Unlimited via x402</span></p>
<p>Wallet: <code>0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code></p>
</body></html>'''

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Color API on {PORT}"); s.serve_forever()
