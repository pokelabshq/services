#!/usr/bin/env python3
"""Poke Labs Service Registry v1.0 — Fleet control panel with live health checks."""
import http.server, json, urllib.request, urllib.parse, subprocess, os, socket
from datetime import datetime

PORT = int(os.environ.get("PORT", 8701))

# All known services with their ports
ALL_SERVICES = [
    {"name": "api-gateway",    "port": 8700, "desc": "Unified API gateway with rate limiting"},
    {"name": "registry",       "port": 8701, "desc": "This service — fleet control panel"},
    {"name": "landing",        "port": 8750, "desc": "Poke Labs landing page"},
    {"name": "dash-apps",      "port": 8760, "desc": "Application dashboard"},
    {"name": "link-preview",   "port": 8765, "desc": "URL metadata extraction + x402"},
    {"name": "poke-bot",       "port": 8770, "desc": "GitHub auto-triage bot"},
    {"name": "poke-hub",       "port": 8775, "desc": "All-in-one GitHub bot"},
    {"name": "readme-gen",     "port": 8780, "desc": "README.md generator"},
    {"name": "streak-tracker", "port": 8785, "desc": "GitHub streak tracker + SVG badges"},
    {"name": "trending-tracker","port": 8790, "desc": "GitHub trending repos tracker"},
    {"name": "residual-income","port": 8795, "desc": "Revenue dashboard"},
    {"name": "github-stats-api","port": 8812, "desc": "Repo statistics API"},
    {"name": "health-aggregator","port": 8816, "desc": "Unified health checks"},
    {"name": "color-api",      "port": 8817, "desc": "Color format conversion"},
    {"name": "base64",         "port": 8836, "desc": "Base64 encode/decode"},
    {"name": "hash-check",     "port": 8837, "desc": "Hash verification"},
    {"name": "jwt-gen",        "port": 8838, "desc": "JWT generation"},
    {"name": "markdown-render","port": 8840, "desc": "Markdown to HTML"},
    {"name": "qr-gen",         "port": 8841, "desc": "QR code generation"},
    {"name": "cron-scheduler", "port": 8842, "desc": "Cron job scheduler"},
    {"name": "dns-lookup",     "port": 8843, "desc": "DNS resolution"},
    {"name": "email-validator","port": 8844, "desc": "Email validation"},
    {"name": "favicon-gen",    "port": 8845, "desc": "Favicon generation"},
    {"name": "geo-ip",         "port": 8846, "desc": "GeoIP lookup"},
    {"name": "gravatar",       "port": 8847, "desc": "Gravatar URL generator"},
    {"name": "hex-to-rgb",     "port": 8848, "desc": "Color conversion"},
    {"name": "sentiment",      "port": 8849, "desc": "Text sentiment analysis"},
    {"name": "isitdown",       "port": 8850, "desc": "Website uptime checker"},
    {"name": "json-validator", "port": 8851, "desc": "JSON validation"},
    {"name": "lorem-ipsum",    "port": 8852, "desc": "Lorem ipsum generator"},
    {"name": "mime-type",      "port": 8853, "desc": "MIME type detection"},
    {"name": "password-gen",   "port": 8854, "desc": "Password generator"},
    {"name": "placeholder-img","port": 8855, "desc": "Placeholder image generator"},
    {"name": "qr-reader",      "port": 8856, "desc": "QR code reader"},
    {"name": "random-user",    "port": 8857, "desc": "Random user generator"},
    {"name": "regex-tester",   "port": 8858, "desc": "Regex testing"},
    {"name": "rss-reader",     "port": 8859, "desc": "RSS feed reader"},
    {"name": "screenshot",     "port": 8860, "desc": "Screenshot service"},
    {"name": "sitemap-gen",    "port": 8861, "desc": "Sitemap generator"},
    {"name": "slugify",        "port": 8862, "desc": "URL slug generator"},
    {"name": "url-shortener",  "port": 8863, "desc": "URL shortening"},
    {"name": "uuid-gen",       "port": 8864, "desc": "UUID generation"},
    {"name": "timestamp",      "port": 8865, "desc": "Timestamp conversion"},
    {"name": "uptime",         "port": 8866, "desc": "Uptime monitoring"},
    {"name": "user-agent",     "port": 8867, "desc": "User agent parser"},
    {"name": "weather",        "port": 8868, "desc": "Weather API"},
    {"name": "word-count",     "port": 8869, "desc": "Word counter"},
    {"name": "xml-to-json",    "port": 8870, "desc": "XML to JSON converter"},
]

def check_port(port):
    """Check if a port is open."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('localhost', port))
        s.close()
        return result == 0
    except:
        return False

def check_health(port):
    """Try to get health info from a service."""
    try:
        resp = urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=3)
        data = json.loads(resp.read())
        return True, data.get('v', '?')
    except:
        return False, None

def get_service_status(svc):
    """Get full status of a service."""
    port = svc['port']
    is_up = check_port(port)
    health_ok, version = check_health(port) if is_up else (False, None)
    return {
        "name": svc['name'],
        "port": port,
        "desc": svc['desc'],
        "up": is_up,
        "health": health_ok,
        "version": version
    }

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Labs — Service Registry</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0a0a14;color:#c8c8d8;min-height:100vh;padding:40px 20px}
.container{max-width:1100px;margin:0 auto}
h1{font-size:2.5rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.subtitle{color:#6e7681;margin-bottom:32px}
.stats{display:flex;gap:24px;margin-bottom:32px;flex-wrap:wrap}
.stat{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px 24px;text-align:center;min-width:120px}
.stat .num{font-size:1.8rem;font-weight:700;color:#00d4ff}
.stat .label{font-size:0.8rem;color:#6e7681;margin-top:4px}
.filters{display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap}
.filter-btn{background:#161b22;border:1px solid #30363d;color:#8b949e;padding:6px 16px;border-radius:20px;cursor:pointer;font-size:0.85rem}
.filter-btn.active{border-color:#00d4ff;color:#00d4ff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;transition:all 0.2s}
.card:hover{border-color:#00d4ff;transform:translateY(-1px)}
.card .header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.card h3{color:#00d4ff;font-size:1rem}
.card .desc{font-size:0.85rem;color:#8b949e;margin-bottom:8px}
.card .meta{display:flex;gap:12px;font-size:0.75rem;color:#6e7681}
.status-dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px}
.status-up{background:#3fb950;box-shadow:0 0 6px #3fb950}
.status-down{background:#f85149}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:600}
.badge-up{background:#238636;color:#fff}
.badge-down{background:#da3633;color:#fff}
.footer{text-align:center;color:#6e7681;margin-top:40px;font-size:0.85rem}
</style>
</head>
<body>
<div class="container">
<h1>🫧 Poke Labs Registry</h1>
<p class="subtitle">Fleet control panel — all microservices in one place</p>
<div class="stats">
<div class="stat"><div class="num" id="total">""" + str(len(ALL_SERVICES)) + """</div><div class="label">Total Services</div></div>
<div class="stat"><div class="num" id="up-count" style="color:#3fb950">—</div><div class="label">Running</div></div>
<div class="stat"><div class="num" id="down-count" style="color:#f85149">—</div><div class="label">Down</div></div>
</div>
<div class="filters">
<button class="filter-btn active" onclick="filter('all')">All</button>
<button class="filter-btn" onclick="filter('up')">Running</button>
<button class="filter-btn" onclick="filter('down')">Down</button>
</div>
<div class="grid" id="services-grid"></div>
<div class="footer">🫧 Poke Labs · Service Registry v1.0 · <span id="ts"></span></div>
</div>
<script>
const SERVICES = """ + json.dumps(ALL_SERVICES) + """;
let statusData = [];

async function loadStatus() {
    const resp = await fetch('/api/status');
    statusData = await resp.json();
    render(statusData);
    document.getElementById('ts').textContent = new Date().toLocaleTimeString();
}

function render(data) {
    const grid = document.getElementById('services-grid');
    grid.innerHTML = '';
    let up = 0, down = 0;
    data.forEach(s => {
        s.up ? up++ : down++;
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.status = s.up ? 'up' : 'down';
        card.innerHTML = `
            <div class="header">
                <h3><span class="status-dot ${s.up ? 'status-up' : 'status-down'}"></span>${s.name}</h3>
                <span class="badge ${s.up ? 'badge-up' : 'badge-down'}">${s.up ? 'UP' : 'DOWN'}</span>
            </div>
            <div class="desc">${s.desc}</div>
            <div class="meta">
                <span>Port ${s.port}</span>
                ${s.version ? `<span>v${s.version}</span>` : ''}
            </div>
        `;
        grid.appendChild(card);
    });
    document.getElementById('up-count').textContent = up;
    document.getElementById('down-count').textContent = down;
}

function filter(type) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    const cards = document.querySelectorAll('.card');
    cards.forEach(c => {
        c.style.display = (type === 'all' || c.dataset.status === type) ? '' : 'none';
    });
}

loadStatus();
setInterval(loadStatus, 30000);
</script>
</body>
</html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/" or p.path == "/index.html":
            b = HTML_PAGE.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        elif p.path == "/api/status":
            statuses = [get_service_status(s) for s in ALL_SERVICES]
            self.send_json(statuses)
        elif p.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT, "services": len(ALL_SERVICES)})
        elif p.path == "/api/services":
            self.send_json(ALL_SERVICES)
        else:
            self.send_json({"error": "not found"}, 404)

    def send_json(self, d, c=200):
        b = json.dumps(d).encode()
        self.send_response(c); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"Service Registry v1.0 on port {PORT} — monitoring {len(ALL_SERVICES)} services")
    http.server.HTTPServer(("", PORT), H).serve_forever()
