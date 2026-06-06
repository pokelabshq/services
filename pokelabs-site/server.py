#!/usr/bin/env python3
"""Poke Labs v11 — Link Preview API + SEO Meta Checker + Paid API Keys + Dashboard"""
import http.server, json, urllib.request, urllib.parse, re, os, sqlite3, time, secrets

PORT = 8000
DB = "/tmp/usage_v11.db"
FREE_LIMIT = 3
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
CHAIN = "base"

TIERS = {
    "free":      {"limit": 3,      "price": 0},
    "hacker":    {"limit": 1000,   "price": 5},
    "pro":       {"limit": 10000,  "price": 25},
    "enterprise": {"limit": 100000,"price": 100},
}

conn = sqlite3.connect(DB)
conn.executescript("""
CREATE TABLE IF NOT EXISTS usage (ip TEXT, ts INTEGER);
CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY, tier TEXT DEFAULT 'free', created INTEGER, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS key_usage (key TEXT, ts INTEGER);
CREATE TABLE IF NOT EXISTS payments (tx_hash TEXT PRIMARY KEY, tier TEXT, amount REAL, ts INTEGER, processed INTEGER DEFAULT 0);
""")
conn.commit()

def usage_count(ip):
    d = int(time.time()) - 86400
    return conn.execute("SELECT COUNT(*) FROM usage WHERE ip=? AND ts>?",(ip,d)).fetchone()[0]

def usage_add(ip):
    conn.execute("INSERT INTO usage VALUES (?,?)",(ip,int(time.time()))); conn.commit()

def key_usage_count(key):
    d = int(time.time()) - 86400
    return conn.execute("SELECT COUNT(*) FROM key_usage WHERE key=? AND ts>?",(key,d)).fetchone()[0]

def key_usage_add(key):
    conn.execute("INSERT INTO key_usage VALUES (?,?)",(key,int(time.time()))); conn.commit()

def get_key_tier(key):
    r = conn.execute("SELECT tier FROM api_keys WHERE key=? AND active=1",(key,)).fetchone()
    return r[0] if r else None

def extract_html(url):
    req = urllib.request.Request(url, headers={"User-Agent":"PokeSEO/11.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8", errors="ignore")

def extract_meta(html):
    def og(prop):
        for pat in [rf'og:{prop}["\'].*?content=["\']([^"\']+)',rf'content=["\']([^"\']+)["\'].*?og:{prop}']:
            m = re.search(pat, html, re.I)
            if m: return m.group(1)
        return ""
    tm = re.search(r'<title>(.*?)</title>', html, re.I|re.S)
    dm = re.search(r'name=["\']description["\'][^>]*content=["\']([^"\']+)', html, re.I)
    if not dm: dm = re.search(r'content=["\']([^"\']+)["\'][^>]*name=["\']description', html, re.I)
    fm = re.search(r'rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)', html, re.I)
    # Twitter cards
    tw_title = ""
    for pat in [rf'twitter:title["\'].*?content=["\']([^"\']+)',rf'content=["\']([^"\']+)["\'].*?twitter:title']:
        m = re.search(pat, html, re.I)
        if m: tw_title = m.group(1); break
    tw_desc = ""
    for pat in [rf'twitter:description["\'].*?content=["\']([^"\']+)',rf'content=["\']([^"\']+)["\'].*?twitter:description']:
        m = re.search(pat, html, re.I)
        if m: tw_desc = m.group(1); break
    tw_image = ""
    for pat in [rf'twitter:image["\'].*?content=["\']([^"\']+)',rf'content=["\']([^"\']+)["\'].*?twitter:image']:
        m = re.search(pat, html, re.I)
        if m: tw_image = m.group(1); break
    return {
        "title": tm.group(1).strip() if tm else "",
        "og_title": og("title"),
        "description": dm.group(1) if dm else "",
        "og_description": og("description"),
        "image": og("image"),
        "og_site_name": og("site_name"),
        "favicon": fm.group(1) if fm else "",
        "twitter_title": tw_title,
        "twitter_description": tw_desc,
        "twitter_image": tw_image,
    }

def seo_audit(url):
    try:
        html = extract_html(url)
        meta = extract_meta(html)
        issues = []
        score = 0
        # Title check
        if meta["og_title"]:
            score += 20
        elif meta["title"]:
            score += 15
            issues.append("Missing og:title — add Open Graph title for better social sharing")
        else:
            issues.append("Missing <title> tag — critical SEO issue")
        # Description check
        if meta["og_description"]:
            score += 20
        elif meta["description"]:
            score += 15
            issues.append("Missing og:description — add for better social previews")
        else:
            issues.append("Missing meta description — hurts SEO and social sharing")
        # Image check
        if meta["image"]:
            score += 20
        else:
            issues.append("Missing og:image — social shares will have no preview image")
        # Twitter cards
        if meta["twitter_title"] and meta["twitter_description"] and meta["twitter_image"]:
            score += 20
        else:
            missing = []
            if not meta["twitter_title"]: missing.append("twitter:title")
            if not meta["twitter_description"]: missing.append("twitter:description")
            if not meta["twitter_image"]: missing.append("twitter:image")
            if missing:
                issues.append(f"Missing Twitter Card tags: {', '.join(missing)}")
        # Favicon
        if meta["favicon"]:
            score += 10
        else:
            issues.append("Missing favicon")
        # Site name
        if meta["og_site_name"]:
            score += 10
        else:
            issues.append("Missing og:site_name")
        return {
            "url": url,
            "score": score,
            "grade": "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D" if score >= 30 else "F",
            "meta": meta,
            "issues": issues,
            "checks_passed": 7 - len(issues),
            "checks_total": 7,
        }
    except Exception as e:
        return {"url": url, "error": str(e)}

def url_to_fetch(body_url):
    url = body_url
    if not url.startswith("http"):
        url = "https://" + url
    return url

def serve_file(name, content_type="text/html; charset=utf-8"):
    path = os.path.join(os.path.dirname(__file__), name)
    if os.path.exists(path):
        with open(path) as f:
            body = f.read().encode()
        self = None  # will be set in handler
        return body, content_type
    return None, None

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok":True,"v":11,"free_limit":FREE_LIMIT,"wallet":WALLET,"chain":CHAIN})
        elif self.path == "/api/stats":
            c = conn.execute("SELECT COUNT(DISTINCT ip), COUNT(*) FROM usage"); ips, reqs = c.fetchone()
            kc = conn.execute("SELECT COUNT(*) FROM api_keys WHERE active=1 AND tier!='free'").fetchone()[0]
            rev = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE processed=1").fetchone()[0]
            self.send_json({"ips":ips,"reqs_24h":reqs,"free_limit":FREE_LIMIT,"active_keys":kc,"version":11,"revenue_usd":rev})
        elif self.path == "/api/usage":
            self.send_json({"used":usage_count(self.client_address[0]),"limit":FREE_LIMIT})
        elif self.path == "/dashboard":
            self.serve_static("dashboard.html")
        elif self.path == "/seo-checker":
            self.serve_static("seo-checker.html")
        else:
            self.serve_static("index.html")

    def do_POST(self):
        if self.path == "/api/preview":
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0)) or 0))
            url = url_to_fetch(body.get("url",""))
            api_key = self.headers.get("X-API-Key","")
            tier_name = get_key_tier(api_key) if api_key else None
            if tier_name:
                tier = TIERS.get(tier_name, TIERS["free"])
                used = key_usage_count(api_key)
                if used >= tier["limit"]:
                    self.send_json({"error":"rate_limit","tier":tier_name,"limit":tier["limit"]},429); return
                key_usage_add(api_key)
                data = {"url":url,"title":"","description":"","image":"","site_name":"","favicon":""}
                try:
                    html = extract_html(url)
                    meta = extract_meta(html)
                    data = {"url":url,"title":meta["og_title"] or meta["title"],"description":meta["og_description"] or meta["description"],"image":meta["image"],"site_name":meta["og_site_name"],"favicon":meta["favicon"]}
                except Exception as e:
                    data = {"url":url,"error":str(e)}
                data["tier"] = tier_name; data["remaining"] = max(0, tier["limit"]-used-1)
                self.send_json(data)
            else:
                ip = self.client_address[0]; used = usage_count(ip)
                if used >= FREE_LIMIT:
                    self.send_json({"error":"limit","wallet":WALLET,"chain":CHAIN,"tiers":{k:{"limit":v["limit"],"price":v["price"]} for k,v in TIERS.items() if k!="free"}},402); return
                usage_add(ip)
                data = {"url":url,"title":"","description":"","image":"","site_name":"","favicon":""}
                try:
                    html = extract_html(url)
                    meta = extract_meta(html)
                    data = {"url":url,"title":meta["og_title"] or meta["title"],"description":meta["og_description"] or meta["description"],"image":meta["image"],"site_name":meta["og_site_name"],"favicon":meta["favicon"]}
                except Exception as e:
                    data = {"url":url,"error":str(e)}
                data["free_remaining"] = max(0, FREE_LIMIT-used-1)
                self.send_json(data)
        elif self.path == "/api/seo-audit":
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0)) or 0))
            url = url_to_fetch(body.get("url",""))
            api_key = self.headers.get("X-API-Key","")
            tier_name = get_key_tier(api_key) if api_key else None
            if tier_name:
                tier = TIERS.get(tier_name, TIERS["free"])
                used = key_usage_count(api_key)
                if used >= tier["limit"]:
                    self.send_json({"error":"rate_limit"},429); return
                key_usage_add(api_key)
                result = seo_audit(url); result["tier"] = tier_name
                self.send_json(result)
            else:
                ip = self.client_address[0]; used = usage_count(ip)
                if used >= FREE_LIMIT:
                    self.send_json({"error":"limit","wallet":WALLET,"chain":CHAIN},402); return
                usage_add(ip)
                result = seo_audit(url); result["free_remaining"] = max(0, FREE_LIMIT-used-1)
                self.send_json(result)
        elif self.path == "/api/key/create":
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0)) or 0))
            tier = body.get("tier","hacker")
            if tier not in TIERS or tier == "free":
                self.send_json({"error":"Invalid tier"},400); return
            key = "pk_live_" + secrets.token_hex(24)
            conn.execute("INSERT INTO api_keys (key,tier,created) VALUES (?,?,?)",(key,tier,int(time.time()))); conn.commit()
            self.send_json({"key":key,"tier":tier,"limit":TIERS[tier]["limit"],"price":TIERS[tier]["price"],"wallet":WALLET,"chain":CHAIN,"message":f"Key created! Send ${TIERS[tier]['price']} USDC to activate."})
        pass  # route not matched below



    elif self.path.startswith("/api/og-generate"):
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        title = q.get("title", [""])[0][:120]
        desc = q.get("desc", [""])[0][:200]
        site = q.get("site", [""])[0][:60]
        bg1 = q.get("bg1", ["#667eea"])[0]
        bg2 = q.get("bg2", ["#764ba2"])[0]
        layout = q.get("layout", ["center"])[0]
        # Check rate limit
        api_key = self.headers.get("X-API-Key", "")
        tier_name = get_key_tier(api_key) if api_key else None
        if tier_name:
            tier = TIERS.get(tier_name, TIERS["free"])
            used = key_usage_count(api_key)
            if used >= tier["limit"]:
                self.send_json({"error": "rate_limit"}, 429); return
            key_usage_add(api_key)
        else:
            ip = self.client_address[0]; used = usage_count(ip)
            if used >= FREE_LIMIT:
                self.send_json({"error": "limit", "wallet": WALLET, "chain": CHAIN}, 402); return
            usage_add(ip)
        # Generate SVG-based OG image
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
        <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:{bg1}"/><stop offset="100%" style="stop-color:{bg2}"/>
        </linearGradient></defs>
        <rect width="1200" height="630" fill="url(#g)"/>
        <text x="100" y="280" font-family="system-ui,sans-serif" font-size="52" font-weight="800" fill="white">{title}</text>
        <text x="100" y="350" font-family="system-ui,sans-serif" font-size="28" fill="rgba(255,255,255,0.8)">{desc}</text>
        <text x="100" y="560" font-family="system-ui,sans-serif" font-size="22" fill="rgba(255,255,255,0.5)">{site}</text>
        </svg>'''
        body = svg.encode()
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def serve_static(self, name):
        path = os.path.join(os.path.dirname(__file__), name)
        if os.path.exists(path):
            with open(path) as f: body = f.read().encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)
        else:
            self.send_json({"error":f"{name} not found"},404)

    def do_OPTIONS(self):
        self.send_response(200)
        for k,v in [("Access-Control-Allow-Origin","*"),("Access-Control-Allow-Methods","GET,POST,OPTIONS"),("Access-Control-Allow-Headers","Content-Type,X-API-Key")]:
            self.send_header(k,v)
        self.end_headers()

    def send_json(self, d, code=200):
        body = json.dumps(d).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Labs v11 on :{PORT}")
    s.serve_forever()
# NOTE: server.py already complete above — this is a placeholder to confirm no changes needed
echo "Server already has all endpoints"