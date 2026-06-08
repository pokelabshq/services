#!/usr/bin/env python3
"""Health Aggregator v1.0 — Monitors all Poke Labs services. Port: 8790. Zero deps."""
import http.server, json, os, socket, html as h, time, urllib.request, urllib.error, urllib.parse

PORT = 8790
SERVICES_DIR = "/home/alx/services"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
_start = time.time()

# Known service ports — manually defined for reliability
SERVICE_PORTS = {
    "link-preview": 8765, "pokelabs-site": 8766, "poke-bot": 8770,
    "poke-hub": 8775, "telegram-bot": 8777, "skills-hub": 8780,
    "skills-marketplace": 8781, "registry": 8785, "pricing": 8790,
    "billing": 8795, "health-aggregator": 8799, "digest": 8776,
    "auto-reply": 8775, "github-reply-bot": 8775,
}

def check_port(port, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def probe_http(port, timeout=3):
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode()
            return True, json.loads(data)
    except urllib.error.HTTPError as e:
        return True, {"status": e.code, "ok": False}
    except:
        return False, None

def scan_all():
    results = []
    total = len(SERVICE_PORTS)
    up = 0
    down = 0
    for name, port in sorted(SERVICE_PORTS.items()):
        if name == "health-aggregator":
            continue
        alive = check_port(port)
        health_data = None
        if alive:
            http_ok, health_data = probe_http(port)
            status = "healthy" if http_ok else "responding"
            up += 1
        else:
            status = "down"
            down += 1
        results.append({"name": name, "port": port, "status": status, "alive": alive, "health": health_data})
    return {
        "services": results,
        "summary": {"total": total - 1, "up": up, "down": down,
                     "pct": round(up/(total-1)*100, 1) if total > 1 else 0},
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            self.json({"ok": True, "v": 1, "port": PORT, "uptime_s": int(time.time()-_start), "wallet": WALLET})
        elif path == "/api/status":
            data = scan_all()
            self.json({"ok": True, "ts": time.time(), **data})
        elif path == "/" or path == "/dashboard":
            self.serve_dashboard()
        else:
            self.json({"error": "Not found", "endpoints": ["/", "/api/health", "/api/status"]}, 404)

    def serve_dashboard(self):
        data = scan_all()
        summary = data["summary"]
        services = data["services"]
        uptime_pct = summary["pct"]
        overall_color = "#00d4ff" if uptime_pct >= 90 else "#ffaa00" if uptime_pct >= 50 else "#ff4444"
        rows = ""
        for s in services:
            color = "#00d4ff" if s["status"]=="healthy" else "#ffaa00" if s["status"]=="responding" else "#ff4444"
            icon = "✓" if s["status"]=="healthy" else "~" if s["status"]=="responding" else "✗"
            health_str = json.dumps(s["health"])[:80] if s.get("health") else "-"
            rows += f'<tr><td><strong>{h.escape(s["name"])}</strong></td><td><code>{s["port"]}</code></td><td style="color:{color};font-weight:700">{icon} {s["status"].title()}</td><td style="font-size:.7rem;color:#666">{health_str}</td></tr>'
        body = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Health Dashboard — Poke Labs</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}.hd{{padding:40px 20px 30px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(0,212,255,0.1) 0%,transparent 60%)}}h1{{font-size:2rem;color:#00d4ff;margin-bottom:6px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;max-width:900px;margin:0 auto;padding:20px}}.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px;text-align:center}}.card .num{{font-size:2.5rem;font-weight:700;color:{overall_color}}}.card .label{{color:#666;font-size:.85rem;margin-top:4px}}table{{width:100%;max-width:1000px;margin:0 auto;border-collapse:collapse;padding:0 20px 20px}}th{{text-align:left;padding:12px 16px;color:#666;font-size:.8rem;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.06)}}td{{padding:10px 16px;border-bottom:1px solid rgba(255,255,255,0.03)}}tr:hover td{{background:rgba(255,255,255,0.02)}}.ft{{text-align:center;padding:30px;color:#444;font-size:.8rem}}</style></head><body><div class="hd"><h1>🏥 Health Dashboard</h1><p style="color:#666">Monitoring {summary["total"]} Poke Labs services</p></div><div class="grid"><div class="card"><div class="num">{summary["total"]}</div><div class="label">Total Services</div></div><div class="card"><div class="num" style="color:#00d4ff">{summary["up"]}</div><div class="label">Healthy</div></div><div class="card"><div class="num" style="color:#ff4444">{summary["down"]}</div><div class="label">Down</div></div><div class="card"><div class="num">{uptime_pct}%</div><div class="label">Uptime</div></div></div><table><thead><tr><th>Service</th><th>Port</th><th>Status</th><th>Health</th></tr></thead><tbody>{rows}</tbody></table><div class="ft">🐾 Poke Labs Health Aggregator v1.0</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body.encode())

    def json(self, d, code=200):
        body=json.dumps(d).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self, *a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Health Aggregator v1.0 on :{PORT}");s.serve_forever()
