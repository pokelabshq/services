#!/usr/bin/env python3
"""Poke Labs Analytics Service — Tracks API usage across all services."""
import http.server, json, os, time, datetime, threading, re, urllib.request

PORT = 8795
SERVICES_DIR = "/home/alx/services"

store = {"requests": [], "totals": {}, "errors": [], "start_time": datetime.datetime.now().isoformat()}
lock = threading.Lock()

def track(service, status, ms):
    entry = {"ts": datetime.datetime.now().isoformat(), "service": service, "status": status, "ms": ms}
    with lock:
        store["requests"].append(entry)
        store["totals"][service] = store["totals"].get(service, 0) + 1
        if status >= 400:
            store["errors"].append(entry)
            if len(store["errors"]) > 50: store["errors"] = store["errors"][-50:]
        if len(store["requests"]) > 5000: store["requests"] = store["requests"][-5000:]

def get_stats():
    with lock:
        day_ago = (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat()
        day = [r for r in store["requests"] if r["ts"] > day_ago]
        avg = sum(r["ms"] for r in day) / len(day) if day else 0
        errs = sum(1 for r in day if r["status"] >= 400)
        top = sorted(store["totals"].items(), key=lambda: -x[1])[:10]
        return {"total": len(store["requests"]), "last_24h": len(day), "avg_ms": round(avg,1), "error_rate": round(errs/len(day)*100,1) if day else 0, "top": [{"s":k,"n":v} for k,v in top], "errors": store["errors"][-5:]}

def poll():
    while True:
        if os.path.isdir(SERVICES_DIR):
            for name in os.listdir(SERVICES_DIR):
                skill = os.path.join(SERVICES_DIR, name, "SKILL.md")
                if not os.path.exists(skill): continue
                port = 0
                content = open(skill).read()
                pm = re.search(r'[Pp]ort[:\s]+(\d{4,5})', content)
                if pm: port = int(pm.group(1))
                if not port: continue
                t = time.time()
                try:
                    r = urllib.request.urlopen(f"http://localhost:{port}/api/health", timeout=3)
                    track(name, r.status, round((time.time()-t)*1000))
                except urllib.error.HTTPError as e:
                    track(name, e.code, round((time.time()-t)*1000))
                except:
                    track(name, 0, round((time.time()-t)*1000))
        time.sleep(30)

PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Poke Labs Analytics</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0a0a0f;color:#e0e0e0;max-width:800px;margin:0 auto;padding:2rem}
h1{color:#00d4ff;margin-bottom:1rem}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:2rem}
.card{background:#111;border:1px solid #222;border-radius:10px;padding:1rem;text-align:center}
.card .v{font-size:1.8rem;font-weight:700;color:#00d4ff}.card .l{color:#666;font-size:.75rem}
table{width:100%;border-collapse:collapse}th,td{padding:.5rem;border-bottom:1px solid #222;text-align:left;font-size:.85rem}
th{color:#00d4ff}.e{color:#ff4444}</style></head><body>
<h1>🐾 Analytics</h1><div class="grid" id="s"></div>
<h2>Top Services</h2><table><tr><th>Service</th><th>Requests</th></tr><tbody id="t"></tbody></table>
<h2>Recent Errors</h2><table><tr><th>Service</th><th>Status</th><th>ms</th></tr><tbody id="e"></tbody></table>
<script>
async function load(){
  const d=await(await fetch('/api/stats')).json();
  document.getElementById('s').innerHTML=`<div class="card"><div class="v">${d.total}</div><div class="l">Total</div></div><div class="card"><div class="v">${d.last_24h}</div><div class="l">24h</div></div><div class="card"><div class="v">${d.avg_ms}ms</div><div class="l">Avg</div></div><div class="card"><div class="v">${d.error_rate}%</div><div class="l">Errors</div></div>`;
  document.getElementById('t').innerHTML=d.top.map(x=>`<tr><td>${x.s}</td><td>${x.n}</td></tr>`).join('');
  document.getElementById('e').innerHTML=d.errors.map(x=>`<tr><td>${x.service}</td><td class="e">${x.status}</td><td>${x.ms}ms</td></tr>`).join('')||'<tr><td colspan="3"style="color:#555">None</td></tr>';
}
load();setInterval(load,15000);</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=self.path.split("?")[0]
        if p in ("/",""):
            self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(PAGE.encode())
        elif p=="/api/stats":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps(get_stats(),indent=2).encode())
        elif p=="/api/health":
            self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(json.dumps({"ok":True,"v":1}).encode())
        else:self.send_response(404);self.end_headers()
    def log_message(self,*a):pass

if __name__=="__main__":
    threading.Thread(target=poll,daemon=True).start()
    s=http.server.HTTPServer(("0.0.0.0",PORT),H)
    print(f"Analytics on {PORT}");s.serve_forever()
