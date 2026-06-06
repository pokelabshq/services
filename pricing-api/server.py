#!/usr/bin/env python3
"""Pricing API v1 — Generate quotes for Poke Labs services"""
import http.server, json, urllib.parse, time

PORT = 8790

TIERS = {
    "freelancer": {"price": 0, "requests": 100, "projects": 3, "support": "community"},
    "startup": {"price": 29, "requests": 10000, "projects": 10, "support": "email"},
    "growth": {"price": 99, "requests": 100000, "projects": 50, "support": "priority"},
    "enterprise": {"price": 499, "requests": -1, "projects": -1, "support": "dedicated"},
}

SERVICES = {
    "link-preview": {"name": "Link Preview API", "unit_price": 0.001, "free_tier": 100},
    "ai-council": {"name": "AI Council", "unit_price": 0.01, "free_tier": 0},
    "webhooks": {"name": "Webhook Processing", "unit_price": 0.0005, "free_tier": 500},
}

def calc_quote(service_key, requests):
    svc = SERVICES.get(service_key)
    if not svc:
        return {"error": f"Unknown: {service_key}", "available": list(SERVICES.keys())}
    free = min(requests, svc["free_tier"])
    paid = max(0, requests - svc["free_tier"])
    cost = round(paid * svc["unit_price"], 4)
    suggested = next((n for n, t in TIERS.items() if t["requests"] >= requests or t["requests"] == -1), "enterprise")
    return {
        "service": svc["name"], "requests": requests,
        "free_requests": free, "paid_requests": paid,
        "unit_price": svc["unit_price"], "total_cost_usd": cost,
        "suggested_tier": suggested, "tier_price": TIERS[suggested]["price"],
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(p.query)
        if p.path == "/api/health":
            self.send_json({"ok": True, "v": 1})
        elif p.path == "/api/tiers":
            self.send_json({"tiers": TIERS})
        elif p.path == "/api/services":
            self.send_json({"services": SERVICES})
        elif p.path == "/api/quote":
            svc = q.get("service", [""])[0]
            reqs = int(q.get("requests", ["0"])[0])
            self.send_json(calc_quote(svc, reqs))
        else:
            self.send_html(f"""<!DOCTYPE html><html><head><title>Pricing API</title>
<style>body{{font-family:system-ui;max-width:600px;margin:3rem auto;padding:1rem;color:#ddd;background:#111}}
h1{{color:#a78bfa}}code{{background:#222;padding:.2rem .4rem;border-radius:4px}}</style>
</head><body><h1>💰 Pricing API</h1>
<p>Generate real-time quotes for Poke Labs services.</p>
<h2>Endpoints</h2>
<p><code>GET /api/tiers</code> — Pricing tiers</p>
<p><code>GET /api/services</code> — Service catalog</p>
<p><code>GET /api/quote?service=link-preview&requests=5000</code> — Get a quote</p>
<h2>Example</h2>
<pre>curl "http://localhost:{PORT}/api/quote?service=link-preview&requests=5000"</pre>
</body></html>""")
    def do_OPTIONS(self):
        self.send_response(200)
        for h,v in [("Access-Control-Allow-Origin","*"),("Access-Control-Allow-Methods","GET,OPTIONS"),("Access-Control-Allow-Headers","Content-Type")]: self.send_header(h,v)
        self.end_headers()
    def send_json(self,d,code=200):
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps(d,indent=2).encode())
    def send_html(self,h,code=200):
        self.send_response(code); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(h.encode())
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Pricing API v1 on :{PORT}"); s.serve_forever()
