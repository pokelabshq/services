#!/usr/bin/env python3
"""Residual Income Engine v1.0 — Automated revenue generation dashboard.
Tracks all Poke Labs revenue streams, calculates projections, and provides
actionable insights for maximizing income. Port 8798. Zero deps."""

import http.server, json, urllib.request, urllib.parse, time, os, html as H

PORT = 8798
VERSION = 1

# Revenue streams data
STREAMS = [
    {
        "name": "Link Preview API (x402)",
        "type": "pay-per-use",
        "price": "$0.01/request",
        "free_tier": "3/day",
        "status": "ready",
        "port": 8765,
        "potential_daily": "$5-50",
        "effort": "low",
        "url": "/api/preview"
    },
    {
        "name": "Skills Marketplace",
        "type": "marketplace",
        "price": "Free + Premium",
        "free_tier": "All skills free",
        "status": "ready",
        "port": 8781,
        "potential_daily": "$10-100",
        "effort": "medium",
        "url": "/"
    },
    {
        "name": "GitHub Bot Services",
        "type": "b2b-saas",
        "price": "$9-99/mo",
        "free_tier": "Self-host free",
        "status": "ready",
        "port": 8775,
        "potential_daily": "$3-30",
        "effort": "high",
        "url": "/"
    },
    {
        "name": "Health Dashboard",
        "type": "monitoring",
        "price": "$0 (lead gen)",
        "free_tier": "Unlimited",
        "status": "ready",
        "port": 8799,
        "potential_daily": "$0 (indirect)",
        "effort": "low",
        "url": "/"
    },
    {
        "name": "GraphQL Gateway",
        "type": "api-gateway",
        "price": "$0.005/request",
        "free_tier": "100/day",
        "status": "ready",
        "port": 8768,
        "potential_daily": "$2-20",
        "effort": "medium",
        "url": "/graphql"
    },
    {
        "name": "Prometheus Metrics",
        "type": "monitoring",
        "price": "$0 (open source)",
        "free_tier": "Unlimited",
        "status": "ready",
        "port": 8792,
        "potential_daily": "$0 (indirect)",
        "effort": "low",
        "url": "/metrics"
    }
]

def check_service(port):
    try:
        urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=2)
        return True
    except:
        return False

def get_system_stats():
    try:
        with open("/proc/loadavg") as f:
            load = f.read().split()[:3]
    except:
        load = ["0", "0", "0"]
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        total = int(lines[0].split()[1])
        avail = int(lines[2].split()[1])
        mem_pct = round((1 - avail/total) * 100, 1)
    except:
        mem_pct = 0
    try:
        st = os.statvfs("/")
        total_d = st.f_blocks * st.f_frsize
        avail_d = st.f_bavail * st.f_frsize
        disk_pct = round((1 - avail_d/total_d) * 100, 1)
    except:
        disk_pct = 0
    return {"load": load, "mem_pct": mem_pct, "disk_pct": disk_pct}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)

        if p.path == "/api/health":
            self.json({"ok": True, "v": VERSION, "port": PORT, "role": "residual-income"})
        elif p.path == "/api/streams":
            result = []
            for s in STREAMS:
                result.append({**s, "running": check_service(s["port"])})
            self.json({"streams": result, "total": len(result)})
        elif p.path == "/api/stats":
            self.json(get_system_stats())
        elif p.path == "/api/action-plan":
            self.json({
                "immediate": [
                    "Start link-preview service (port 8765) — highest revenue potential",
                    "Start skills-marketplace (port 8781) — showcase all skills",
                    "Start poke-hub (port 8775) — GitHub automation value",
                    "Expose all running services via Conway API"
                ],
                "short_term": [
                    "Set up GitHub webhooks for auto-reply bot",
                    "Create landing page with pricing tiers",
                    "Add x402 payment links to all paid services"
                ],
                "long_term": [
                    "Build subscription billing system",
                    "Create affiliate program for skills marketplace",
                    "Add analytics dashboard for revenue tracking"
                ]
            })
        elif p.path == "/":
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        stats = get_system_stats()
        streams_data = []
        for s in STREAMS:
            running = check_service(s["port"])
            streams_data.append({**s, "running": running})

        running_count = sum(1 for s in streams_data if s["running"])
        total_count = len(streams_data)

        stream_cards = ""
        for s in streams_data:
            status_color = "#00ffaa" if s["running"] else "#ff4444"
            status_text = "🟢 RUNNING" if s["running"] else "🔴 DOWN"
            btn = f'<a href="http://localhost:{s["port"]}{s["url"]}" class="btn">Visit</a>' if s["running"] else '<span class="btn off">Offline</span>'
            stream_cards += f"""
            <div class="stream-card">
                <div class="stream-header">
                    <h3>{H.escape(s["name"])}</h3>
                    <span class="status" style="color:{status_color}">{status_text}</span>
                </div>
                <div class="stream-meta">
                    <span class="badge type">{H.escape(s["type"])}</span>
                    <span class="badge price">{H.escape(s["price"])}</span>
                    <span class="badge potential">{H.escape(s["potential_daily"])}/day</span>
                </div>
                <div class="stream-effort">Effort: {H.escape(s["effort"])} | Port: {s["port"]} | Free: {H.escape(s["free_tier"])}</div>
                {btn}
            </div>"""

        page = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Residual Income Engine — Poke Labs</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a1a; color: #e0e0e2; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 100%); padding: 30px 20px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.06); }}
h1 {{ color: #00ffaa; font-size: 1.8rem; margin-bottom: 8px; }}
.subtitle {{ color: #888; font-size: 0.85rem; }}
.stats {{ display: flex; gap: 20px; justify-content: center; margin-top: 16px; }}
.stat {{ text-align: center; }}
.stat .n {{ font-size: 1.4rem; font-weight: 700; color: #00ffaa; }}
.stat .l {{ color: #666; font-size: 0.7rem; }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px; }}
.section-title {{ color: #e0e0e2; font-size: 1rem; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }}
.stream-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; transition: border-color 0.2s; }}
.stream-card:hover {{ border-color: #00ffaa; }}
.stream-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.stream-header h3 {{ font-size: 0.9rem; color: #e0e0e2; }}
.status {{ font-size: 0.75rem; font-weight: 600; }}
.stream-meta {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }}
.badge {{ padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 500; }}
.badge.type {{ background: rgba(0,255,170,0.08); color: #00ffaa; }}
.badge.price {{ background: rgba(100,150,255,0.1); color: #6496ff; }}
.badge.potential {{ background: rgba(255,170,0,0.1); color: #ffaa00; }}
.stream-effort {{ color: #666; font-size: 0.7rem; margin-bottom: 10px; }}
.btn {{ display: inline-block; background: #00ffaa; color: #0a0a1a; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.75rem; }}
.btn.off {{ background: #333; color: #666; cursor: default; }}
.action-list {{ list-style: none; }}
.action-list li {{ padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.85rem; color: #ccc; }}
.action-list li::before {{ content: "→ "; color: #00ffaa; }}
.footer {{ text-align: center; padding: 20px; color: #555; font-size: 0.7rem; }}
</style>
</head><body>
<div class="header">
    <h1>💰 Residual Income Engine</h1>
    <p class="subtitle">Poke Labs Revenue Dashboard — v{VERSION} | Port {PORT}</p>
    <div class="stats">
        <div class="stat"><div class="n">{running_count}/{total_count}</div><div class="l">Services Up</div></div>
        <div class="stat"><div class="n">{stats["load"][0]}</div><div class="l">Load</div></div>
        <div class="stat"><div class="n">{stats["mem_pct"]}%</div><div class="l">Memory</div></div>
        <div class="stat"><div class="n">{stats["disk_pct"]}%</div><div class="l">Disk</div></div>
    </div>
</div>
<div class="container">
    <h2 class="section-title">Revenue Streams</h2>
    <div class="grid">{stream_cards}</div>

    <h2 class="section-title">Action Plan</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">
        <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:16px">
            <h3 style="color:#00ffaa;font-size:.85rem;margin-bottom:8px">⚡ Immediate</h3>
            <ul class="action-list">
                <li>Start link-preview service (port 8765) — highest revenue potential</li>
                <li>Start skills-marketplace (port 8781) — showcase all skills</li>
                <li>Start poke-hub (port 8775) — GitHub automation value</li>
                <li>Expose all running services via Conway API</li>
            </ul>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:16px">
            <h3 style="color:#ffaa00;font-size:.85rem;margin-bottom:8px">📋 Short Term</h3>
            <ul class="action-list">
                <li>Set up GitHub webhooks for auto-reply bot</li>
                <li>Create landing page with pricing tiers</li>
                <li>Add x402 payment links to all paid services</li>
            </ul>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:16px">
            <h3 style="color:#6496ff;font-size:.85rem;margin-bottom:8px">🚀 Long Term</h3>
            <ul class="action-list">
                <li>Build subscription billing system</li>
                <li>Create affiliate program for skills marketplace</li>
                <li>Add analytics dashboard for revenue tracking</li>
            </ul>
        </div>
    </div>
</div>
<div class="footer">Poke Labs Residual Income Engine | {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}</div>
</body></html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Residual Income Engine v1.0 on :{PORT}")
    s.serve_forever()
