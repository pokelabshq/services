#!/usr/bin/env python3
"""Link Preview API v5 — Extract title, description, image from any URL"""
import http.server, json, urllib.request, urllib.parse, re, os, sqlite3, time
from http import HTTPStatus

PORT = 8765
DB = "/tmp/lp_usage.db"
FREE_LIMIT = 3

conn = sqlite3.connect(DB)
conn.execute("CREATE TABLE IF NOT EXISTS usage (ip TEXT, ts INTEGER)")
conn.commit()

def usage_count(ip):
    day_ago = int(time.time()) - 86400
    c = conn.execute("SELECT COUNT(*) FROM usage WHERE ip=? AND ts>?", (ip, day_ago))
    return c.fetchone()[0]

def usage_add(ip):
    conn.execute("INSERT INTO usage VALUES (?,?)", (ip, int(time.time())))
    conn.commit()

def extract(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PokePreview/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        
        def og(prop):
            m = re.search(rf'og:{prop}["\'].*?content=["\']([^"\']+)', html, re.I)
            if not m:
                m = re.search(rf'content=["\']([^"\']+)["\'].*?og:{prop}', html, re.I)
            return m.group(1) if m else ""
        
        title_m = re.search(r'<title>(.*?)</title>', html, re.I|re.S)
        desc_m = re.search(r'name=["\']description["\'][^>]*content=["\']([^"\']+)', html, re.I)
        if not desc_m:
            desc_m = re.search(r'content=["\']([^"\']+)["\'][^>]*name=["\']description', html, re.I)
        
        fav_m = re.search(r'rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']+)', html, re.I)
        
        return {
            "title": title_m.group(1).strip() if title_m else og("title"),
            "description": desc_m.group(1) if desc_m else og("description"),
            "image": og("image"),
            "site_name": og("site_name"),
            "favicon": fav_m.group(1) if fav_m else "",
            "url": url,
        }
    except Exception as e:
        return {"error": str(e), "url": url}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok": True, "v": 5, "free_limit": FREE_LIMIT})
        elif self.path == "/api/usage":
            ip = self.client_address[0]
            self.send_json({"used": usage_count(ip), "limit": FREE_LIMIT})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/api/preview":
            ip = self.client_address[0]
            used = usage_count(ip)
            if used >= FREE_LIMIT:
                self.send_json({
                    "error": "Free limit exceeded",
                    "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF",
                    "chain": "base",
                    "message": "Send USDC via x402 for unlimited access"
                }, 402)
                return
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            url = body.get("url", "")
            if not url.startswith("http"):
                url = "https://" + url
            usage_add(ip)
            data = extract(url)
            data["free_remaining"] = max(0, FREE_LIMIT - used - 1)
            self.send_json(data)
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_json(self, d, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Link Preview API v5 on :{PORT}")
    s.serve_forever()
