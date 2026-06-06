#!/usr/bin/env python3
"""Poke Labs Uptime Monitor v1 — pings all services, logs uptime, alerts on downtime"""
import http.server, json, time, os, urllib.request, urllib.parse, threading, socket

PORT = 8799
LOG_DIR = "/home/alx/briefing"
os.makedirs(LOG_DIR, exist_ok=True)

ENDPOINTS = [
    {"name": "link-preview", "url": "http://127.0.0.1:8765/api/health"},
    {"name": "site",         "url": "http://127.0.0.1:8766/api/health"},
    {"name": "poke-bot",     "url": "http://127.0.0.1:8770/"},
    {"name": "discord",      "url": "http://127.0.0.1:8775/api/health"},
    {"name": "telegram",     "url": "http://127.0.0.1:8777/api/health"},
    {"name": "skills-hub",   "url": "http://127.0.0.1:8780/api/health"},
    {"name": "registry",     "url": "http://127.0.0.1:8785/api/health"},
    {"name": "pricing",      "url": "http://127.0.0.1:8790/api/health"},
    {"name": "billing",      "url": "http://127.0.0.1:8795/api/health"},
]

def check_endpoint(ep):
    try:
        req = urllib.request.urlopen(ep["url"], timeout=5)
        data = json.loads(req.read())
        return {"name": ep["name"], "url": ep["url"], "status": "up",
                "code": req.status, "response": data, "latency_ms": 0}
    except urllib.error.HTTPError as e:
        return {"name": ep["name"], "url": ep["url"], "status": "error",
                "code": e.code, "error": str(e), "latency_ms": 0}
    except Exception as e:
        return {"name": ep["name"], "url": ep["url"], "status": "down",
                "code": 0, "error": str(e)[:100], "latency_ms": 0}

def run_checks():
    results = [check_endpoint(ep) for ep in ENDPOINTS]
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {"timestamp": ts, "total": len(results),
              "up": sum(1 for r in results if r["status"] == "up"),
              "down": sum(1 for r in results if r["status"] != "up"),
              "results": results}
    # Append to log
    log_file = f"{LOG_DIR}/uptime.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(report) + "\n")
    return report

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "monitor": "uptime"})
        elif p.path == "/api/check":
            report = run_checks()
            self.send_json(report)
        elif p.path == "/api/history":
            try:
                with open(f"{LOG_DIR}/uptime.jsonl") as f:
                    lines = f.readlines()[-50:]
                history = [json.loads(l) for l in lines]
                self.send_json({"checks": len(history), "history": history})
            except FileNotFoundError:
                self.send_json({"checks": 0, "history": []})
        elif p.path == "/":
            self.send_html(self.dashboard())
        else:
            self.send_json({"error": "not found"}, 404)

    def dashboard(self):
        return f"""<!DOCTYPE html><html><head><title>Poke Labs Uptime</title>
<style>body{{font-family:system-ui;background:#0a0a1a;color:#ddd;padding:2rem}}
h1{{color:#a78bfa}} .r{{display:flex;gap:1rem;align-items:center;padding:.5rem;border-bottom:1px solid #222}}
.dot{{width:10px;height:10px;border-radius:50%}} .green{{background:#22c55e}} .red{{background:#ef4444}}
code{{background:#1a1a2e;padding:.15rem .4rem;border-radius:4px;font-size:.8rem}}
button{{background:#7c3aed;color:#fff;border:none;padding:.5rem 1rem;border-radius:8px;cursor:pointer}}
</style></head><body>
<h1>🐾 Poke Labs Uptime Monitor</h1>
<p>Monitoring {len(ENDPOINTS)} services. <button onclick="runCheck()">Run Check</button></p>
<div id="results">Click "Run Check" to test all endpoints.</div>
<script>
function runCheck(){{
  fetch('/api/check').then(r=>r.json()).then(d=>{
    let h='<h2>'+d.up+'/'+d.total+' up — '+d.timestamp+'</h2>';
    d.results.forEach(r=>{
      h+='<div class="r"><span class="dot '+(r.status==='up'?'green':'red')+'"></span>'+
         '<strong>'+r.name+'</strong> <code>'+r.url+'</code> '+
         (r.status==='up'?'✅ '+JSON.stringify(r.response):'❌ '+(r.error||r.status))+'</div>';
    }});
    document.getElementById('results').innerHTML=h;
  });
}}
</script></body></html>"""

    def send_json(self, d, code=200):
        self.send_response(code)
        for h,v in [("Content-Type","application/json"),("Access-Control-Allow-Origin","*")]:
            self.send_header(h,v)
        self.end_headers()
        self.wfile.write(json.dumps(d, indent=2).encode())

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    import subprocess
    subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
    time.sleep(1)
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Labs Uptime Monitor v1 on :{PORT}")
    s.serve_forever()
