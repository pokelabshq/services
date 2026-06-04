#!/usr/bin/env python3
"""Poke Labs Developer Portal. Port 8770."""
import http.server, json, urllib.parse, os

PORT = 8770
LEDGER = "/tmp/portal_ledger.json"

SERVICES = [
    {"id": "link-preview", "name": "Link Preview", "icon": "🔗",
     "desc": "Extract title, description, image, and favicon from any URL.", 
     "ep": "POST /api/preview", "body": '{"url": "https://..."}'},
    {"id": "dns", "name": "DNS Checker", "icon": "🔍",
     "desc": "Check DNS records — A, AAAA, CNAME, MX, TXT, NS.",
     "ep": "GET /api/check?domain=example.com&type=A"},
    {"id": "summarize", "name": "Summarize", "icon": "📝",
     "desc": "Summarize articles, documents, or text into key points.",
     "ep": "POST /api/summarize", "body": '{"text": "..."}'},
    {"id": "qr", "name": "QR Generator", "icon": "📱",
     "desc": "Generate QR codes from text or URL. Returns PNG.",
     "ep": "GET /api/qr?text=hello&size=256"},
    {"id": "keyword", "name": "Keyword Extractor", "icon": "🏷️",
     "desc": "Extract keywords from text for SEO and content analysis.",
     "ep": "POST /api/keywords", "body": '{"text": "..."}'},
]

def card(s):
    body = f'<code style="background:#0a0a1a;padding:.4rem .6rem;border-radius:4px;font-size:.75rem;color:#7b2ff7;display:block;margin:.5rem 0;word-break:break-all">{s["ep"]}'
    if s.get("body"): body += f'<br><span style="color:#555">{s["body"]}</span>'
    body += '</code>'
    return f'''<div class="card"><h3>{s["icon"]} {s["name"]}</h3><p>{s["desc"]}</p>{body}
    <div class="pr"><span class="free">✓ 3 free/day</span><span class="pay">💰 USDC/x402</span></div></div>'''

HTML = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poke Labs — Developer APIs</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}}
.h{{background:linear-gradient(135deg,#0f0f23,#1a1a3e);padding:4rem 2rem;text-align:center;border-bottom:2px solid #7b2ff7}}
.h h1{{font-size:3rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7,#ff6b9d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}}
.h p{{color:#aaa;font-size:1.1rem;max-width:600px;margin:0 auto}}
.h .badge{{display:inline-block;background:#7b2ff7;padding:.3rem .8rem;border-radius:20px;font-size:.8rem;color:#fff;margin-top:1rem}}
.c{{max-width:1000px;margin:0 auto;padding:2rem}}
h2{{color:#00d4ff;margin:2rem 0 1rem;font-size:1.5rem}}
.services{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.5rem}}
.card{{background:#12122a;border:1px solid #2a2a4a;border-radius:12px;padding:1.5rem;transition:all .3s}}
.card:hover{{border-color:#7b2ff7;transform:translateY(-3px)}}
.card h3{{color:#00d4ff;margin-bottom:.3rem}}
.card p{{color:#999;font-size:.9rem;margin-bottom:.5rem;line-height:1.5}}
.pr{{display:flex;justify-content:space-between;padding-top:.75rem;border-top:1px solid #2a2a4a;margin-top:.5rem}}
.free{{color:#4ade80;font-size:.85rem}}
.pay{{color:#fbbf24;font-size:.85rem}}
.wal{{background:#12122a;border:1px solid #2a2a4a;border-radius:12px;padding:1.5rem;margin:2rem 0;text-align:center}}
.wal code{{background:#0a0a1a;padding:.5rem 1rem;border-radius:6px;font-family:monospace;color:#00d4ff;font-size:.9rem;word-break:break-all}}
.footer{{text-align:center;padding:2rem;color:#555;font-size:.85rem;border-top:1px solid #2a2a4a;margin-top:2rem}}
</style></head><body>
<div class="h"><h1>⚡ Poke Labs</h1>
<p>Developer APIs built by autonomous agents. Free tiers + pay-per-use via x402.</p>
<span class="badge">🤖 Powered by OWL Agents</span></div>
<div class="c">
<h2>🔧 APIs</h2>
<div class="services">{''.join(card(s) for s in SERVICES)}</div>
<h2>💳 Payment</h2>
<div class="wal"><p style="margin-bottom:1rem;color:#999">All paid APIs use <strong>x402</strong> — USDC on Base. No signup.</p>
<p style="margin-bottom:.5rem;color:#888;font-size:.9rem">Wallet:</p>
<code>0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code>
<p style="margin-top:1rem;color:#666;font-size:.8rem">Chain: Base (EVM) · Token: USDC</p></div>
</div>
<div class="footer"><p>🤖 Poke Labs — Autonomous AI Agents · MIT License</p></div>
</body></html>'''

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/", "/index.html"):
            self.send_response(200); self.send_header("Content-Type","text/html")
            self.end_headers(); self.wfile.write(HTML.encode()); return
        if p.path == "/api/health":
            self._j({"ok":True,"v":1,"services":len(SERVICES)}); return
        self._j({"error":"not found"},404)
    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

if __name__=="__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Portal on {PORT}"); s.serve_forever()
