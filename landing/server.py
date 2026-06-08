#!/usr/bin/env python3
"""Poke Labs Landing Page v1.0 — Professional landing + service catalog. Port: 8750. Zero deps."""
import http.server, json, os, time, socket

PORT = 8750

def check_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        r = s.connect_ex(('127.0.0.1', port))
        s.close()
        return r == 0
    except:
        return False

SERVICES = [
    ("Link Preview API", "/api/preview", "Extract title, description, image from any URL. Free tier: 3/day. Unlimited via x402 USDC."),
    ("Poke Bot", "GitHub App", "Auto-triage GitHub issues with priority labels. Auto-size PRs. Responds to !poke commands."),
    ("Poke Hub", "GitHub App", "All-in-one bot: auto-reply, auto-label, stale issue closer, and dashboard."),
    ("AI Council", "", "Monitors all Poke Labs repos for stale issues, outdated deps, and CI failures."),
    ("Webhook Bot", "/webhook", "Receive GitHub webhooks and auto-reply to issues and PRs."),
    ("URL Shortener", "/s/", "Shorten URLs. Zero dependencies."),
    ("QR Generator", "/qr", "Generate QR codes from text or URLs."),
    ("Hash API", "/hash", "SHA256, MD5, SHA1 hashing. Send data, get hash."),
    ("Color API", "/color", "Convert hex↔rgb↔hsl. Generate palettes."),
    ("JSON to TS", "/json2ts", "Paste JSON, get TypeScript interfaces."),
]

FEATURED = [SERVICES[0], SERVICES[1], SERVICES[2], SERVICES[3]]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Labs — AI-Powered Open Source Tools</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#08080c;color:#d0d0d0;line-height:1.6}}
.hero{{background:linear-gradient(160deg,#0d1117 0%,#161b22 50%,#0d1117 100%);padding:80px 24px 60px;text-align:center;border-bottom:1px solid #21262d}}
.hero h1{{font-size:42px;font-weight:800;color:#fff;margin-bottom:12px}}
.hero h1 em{{color:#00d4ff;font-style:normal}}
.hero p{{font-size:18px;color:#8b949e;max-width:600px;margin:0 auto 28px}}
.badges{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:20px}}
.badge{{background:#161b22;border:1px solid #30363d;padding:4px 12px;border-radius:16px;font-size:12px;color:#8b949e}}
.badge.green{{color:#3fb950;border-color:#23863655}}
.btn{{display:inline-block;padding:10px 24px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;margin:4px}}
.btn-primary{{background:#238636;color:#fff}}
.btn-secondary{{background:#21262d;color:#c9d1d9;border:1px solid #30363d}}
.container{{max-width:960px;margin:0 auto;padding:32px 24px}}
h2{{font-size:22px;color:#fff;margin:32px 0 16px;padding-bottom:8px;border-bottom:1px solid #21262d}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-top:16px}}
.card{{background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:20px;transition:border-color .2s}}
.card:hover{{border-color:#388bfd44}}
.card h3{{font-size:15px;color:#fff;margin-bottom:6px}}
.card .meta{{font-size:11px;color:#388bfd;font-family:monospace;margin-bottom:8px}}
.card p{{font-size:13px;color:#8b949e;line-height:1.5}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0}}
.stat{{text-align:center;padding:16px;background:#0d1117;border:1px solid #21262d;border-radius:8px}}
.stat .num{{font-size:28px;font-weight:700;color:#00d4ff}}
.stat .lbl{{font-size:11px;color:#6e7681;margin-top:4px}}
.about{{background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:24px;margin-top:24px}}
.about p{{font-size:14px;color:#8b949e;margin-bottom:10px}}
.about strong{{color:#c9d1d9}}
.footer{{text-align:center;padding:32px;color:#6e7681;font-size:12px;border-top:1px solid #21262d;margin-top:40px}}
.footer a{{color:#388bfd;text-decoration:none}}
</style>
</head>
<body>
<div class="hero">
  <h1>🐾 <em>Poke</em> Labs</h1>
  <p>AI-powered open source tools — built by a 13-year-old dev and an autonomous AI agent. Zero dependencies. MIT licensed.</p>
  <div class="badges">
    <span class="badge green">● Python stdlib only</span>
    <span class="badge">MIT License</span>
    <span class="badge">{count}+ Services</span>
    <span class="badge">4 GitHub Repos</span>
    <span class="badge">x402 Payments</span>
  </div>
  <div>
    <a href="https://github.com/pokelabshq" class="btn btn-primary">View on GitHub</a>
    <a href="#services" class="btn btn-secondary">Explore Services</a>
    <a href="#about" class="btn btn-secondary">About</a>
  </div>
</div>

<div class="container">
  <div class="stats">
    <div class="stat"><div class="num">{count}</div><div class="lbl">Microservices</div></div>
    <div class="stat"><div class="num">0</div><div class="lbl">Dependencies</div></div>
    <div class="stat"><div class="num">4</div><div class="lbl">Repos</div></div>
    <div class="stat"><div class="num">5</div><div class="lbl">Skills</div></div>
  </div>

  <a id="services"></a>
  <h2>Featured Services</h2>
  <div class="grid">
    {featured}
  </div>

  <h2>All Services</h2>
  <div class="grid">
    {all_services}
  </div>

  <a id="about"></a>
  <h2>About</h2>
  <div class="about">
    <p><strong>Poke Labs</strong> is a collaboration between <strong>Alexander Wondwossen</strong> (13, Toronto) and <strong>Poke</strong> (autonomous AI agent). We build practical open-source tools that anyone can run.</p>
    <p>Every service is <strong>pure Python stdlib</strong> — no <code>pip install</code> needed. Just clone, run, and go. Perfect for hobbyists, students, and anyone who wants to self-host useful tools.</p>
    <p>Services like Link Preview API support <strong>x402 USDC payments</strong> (Base chain) for unlimited usage. Free tier available for testing.</p>
    <p>All code is <strong>MIT licensed</strong>. Contributions welcome — check our <a href="https://github.com/pokelabshq" style="color:#388bfd">GitHub org</a>.</p>
  </div>

  <div class="footer">
    <p>🐾 Built with &lt;3 by <strong>Poke Labs</strong> — Alexander Wondwossen & Poke the automaton</p>
    <p style="margin-top:8px">{ts} · <a href="https://github.com/pokelabshq">GitHub</a> · MIT License</p>
  </div>
</div>
</body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        cards = ""
        for name, meta, desc in SERVICES:
            meta_html = f'<div class="meta">{meta}</div>' if meta else ''
            cards += f'<div class="card"><h3>{name}</h3>{meta_html}<p>{desc}</p></div>'
        
        featured = ""
        for name, meta, desc in FEATURED:
            meta_html = f'<div class="meta">{meta}</div>' if meta else ''
            featured += f'<div class="card"><h3>{name}</h3>{meta_html}<p>{desc}</p></div>'
        
        html = TEMPLATE.format(
            count=len(SERVICES),
            featured=featured,
            all_services=cards,
            ts=time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
        )
        self.send_response(200)
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())
    def log_message(self,*a):pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Poke Labs Landing v1.0 on :{PORT}")
    s.serve_forever()
