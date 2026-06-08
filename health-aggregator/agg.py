#!/usr/bin/env python3
"""Health Aggregator v1.0 — Monitors all Poke Labs services. Port: 8799. Zero deps."""
import http.server, json, os, socket, html as h, time, urllib.request, urllib.error, urllib.parse

PORT = 8799
SERVICES_DIR = "/home/alx/services"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
_start = time.time()

# Known service ports
SERVICE_PORTS = {
    "link-preview": 8765, "pokelabs-site": 8766, "poke-bot": 8770,
    "poke-hub": 8775, "telegram-bot": 8777, "skills-hub": 8780,
    "skills-marketplace": 8781, "registry": 8785, "billing": 8795,
    "health-aggregator": 8799,
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
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return True, {"status": e.code}
    except:
        return False, None

def scan_all():
    results = []
    up = down = 0
    for name, port in sorted(SERVICE_PORTS.items()):
        if name == "health-aggregator":
            continue
        alive = check_port(port)
        health = None
        if alive:
            ok, health = probe_http(port)
            status = "healthy" if ok else "responding"
            up += 1
        else:
            status = "down"
            down += 1
        results.append({"name": name, "port": port, "status": status, "health": health})
    total = up + down
    return {"services": results, "summary": {"total": total, "up": up, "down": down, "pct": round(up/total*100, 1) if total else 0}}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self.json({"ok": True, "v": 1, "port": PORT, "uptime_s": int(time.time()-_start)})
        elif parsed.path == "/api/status":
            self.json({"ok": True, **scan_all()})
        elif parsed.path in ("/", "/dashboard"):
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        data = scan_all()
        sm = data["summary"]
        pct = sm["pct"]
        clr = "#00d4ff" if pct >= 90 else "#ffaa00" if pct >= 50 else "#ff4444"
        rows = ""
        for s in data["services"]:
            c = "#00d4ff" if s["status"]=="healthy" else "#ffaa00" if s["status"]=="responding" else "#ff4444"
            ic = "✓" if s["status"]=="healthy" else "~" if s["status"]=="responding" else "✗"
            hs = str(s.get("health",""))[:60]
            rows += f'<tr><td>{h.escape(s["name"])}</td><td>{s["port"]}</td><td style="color:{c}">{ic} {s["status"]}</td><td style="color:#666;font-size:.75rem">{hs}</td></tr>'
        b = f'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs — Health Dashboard</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}.hd{{padding:40px 20px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(0,212,255,0.1) 0%,transparent 60%)}}h1{{font-size:2rem;color:#00d4ff}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;max-width:800px;margin:0 auto;padding:20px}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:20px;text-align:center}}.n{{font-size:2.2rem;font-weight:700;color:{clr}}}.l{{color:#666;font-size:.8rem}}table{{width:100%;max-width:900px;margin:0 auto;border-collapse:collapse;padding:0 20px 40px}}th{{text-align:left;padding:10px;color:#666;font-size:.75rem;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.06)}}td{{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,0.03);font-size:.85rem}}tr:hover td{{background:rgba(255,255,255,0.02)}}.ft{{text-align:center;padding:30px;color:#444;font-size:.75rem}}</style></head><body><div class="hd"><h1>🏥 Health Dashboard</h1><p style="color:#666">Monitoring {sm["total"]} services</p></div><div class="g"><div class="c"><div class="n">{sm["total"]}</div><div class="l">Total</div></div><div class="c"><div class="n" style="color:#00d4ff">{sm["up"]}</div><div class="l">Healthy</div></div><div class="c"><div class="n" style="color:#ff4444">{sm["down"]}</div><div class="l">Down</div></div><div class="c"><div class="n">{pct}%</div><div class="l">Uptime</div></div></div><table><thead><tr><th>Service</th><th>Port</th><th>Status</th><th>Detail</th></tr></thead><tbody>{rows}</tbody></table><div class="ft">🐾 Poke Labs © 2026 · MIT</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(b.encode())

    def json(self, d, code=200):
        body = json.dumps(d).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Health Aggregator v1.0 on :{PORT}");s.serve_forever()
