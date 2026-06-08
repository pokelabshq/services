#!/usr/bin/env python3
"""GraphQL API Gateway v1.0 — Unified query layer for all Poke Labs services.
Aggregates data from multiple microservices into single GraphQL endpoint. Port 8768. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, re, html as htmlmod

PORT = 8768
VERSION = 1

# Service registry
SERVICES = [
    {"name": "link-preview", "port": 8765, "url": "http://localhost:8765"},
    {"name": "pokelabs-site", "port": 8766, "url": "http://localhost:8766"},
    {"name": "poke-hub", "port": 8775, "url": "http://localhost:8775"},
    {"name": "github-stats", "port": 8779, "url": "http://localhost:8779"},
    {"name": "skills-marketplace", "port": 8781, "url": "http://localhost:8781"},
    {"name": "skills-index", "port": 8782, "url": "http://localhost:8782"},
    {"name": "x402-gateway", "port": 8795, "url": "http://localhost:8795"},
    {"name": "ws-events-hub", "port": 8767, "url": "http://localhost:8767"},
]

def fetch_service(svc, path="/api/health", timeout=2):
    try:
        req = urllib.request.urlopen(f"{svc['url']}{path}", timeout=timeout)
        return json.loads(req.read()), 200
    except:
        return {"ok": False, "error": "unreachable"}, 503

def execute_query(query):
    """Minimal GraphQL parser — supports { field subfield { key } } syntax."""
    query = query.strip()
    if query.startswith("{"): query = query[1:]
    if query.endswith("}"): query = query[:-1]
    query = query.strip()

    result = {}
    # Match top-level fields
    for m in re.finditer(r'(\w+)(?:\{([^}]*)\})?', query):
        field = m.group(1)
        sub = m.group(2)
        if field == "services":
            svcs = []
            for s in SERVICES:
                data, code = fetch_service(s)
                svcs.append({"name": s["name"], "port": s["port"], "status": "up" if code == 200 else "down", "health": data})
            result["services"] = svcs
        elif field == "service":
            # Single service query
            result["service"] = {"name": SERVICES[0]["name"], "port": SERVICES[0]["port"]}
        elif field == "health":
            up = 0
            for s in SERVICES:
                _, code = fetch_service(s)
                if code == 200: up += 1
            result["health"] = {"total": len(SERVICES), "up": up, "down": len(SERVICES) - up, "pct": round(up / len(SERVICES) * 100, 1) if SERVICES else 0}
        elif field == "version":
            result["version"] = VERSION
        elif field == "timestamp":
            result["timestamp"] = time.time()
        elif field in ("name", "status", "port", "url", "error", "ok"):
            pass  # sub-fields handled above
        else:
            result[field] = {"error": f"Unknown field: {field}", "availableFields": ["services", "health", "version", "timestamp", "service"]}
    return result

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        if p.path == "/api/health":
            self.json({"ok": True, "v": VERSION, "port": PORT, "role": "graphql-gateway", "services": len(SERVICES)})
        elif p.path == "/graphql" or p.path == "/":
            query = qs.get("query", ["{ health version timestamp services { name port status } }"])[0]
            data = execute_query(query)
            self.json({"data": data})
        elif p.path == "/playground":
            self.playground()
        else:
            self.json({"error": "Not found. Use /graphql?query={health}"}, 404)

    def do_POST(self):
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {}
        query = body.get("query", "{ health version }")
        data = execute_query(query)
        self.json({"data": data})

    def playground(self):
        s = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>GraphQL Gateway — Poke Labs</title><style>body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;flex-direction:column}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:30px;max-width:650px;width:90%}}h1{{color:#00ffaa;text-align:center}}textarea{{width:100%;height:80px;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#00ffaa;font-family:monospace;padding:10px;resize:vertical;box-sizing:border-box}}.btn{{background:#00ffaa;color:#0a0a1a;border:none;padding:10px 20px;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;margin-top:10px;width:100%}}#result{{font-family:monospace;font-size:.8em;background:rgba(0,0,0,0.3);border-radius:8px;padding:15px;margin-top:15px;white-space:pre-wrap;max-height:300px;overflow-y:auto;color:#00ffaa}}</style></head><body><div class="c"><h1>🔮 GraphQL API Gateway</h1><p style="text-align:center;color:#888">Query all Poke Labs services — Port {PORT}</p><textarea id="q">{{"{{ health version services {{ name port status }} }}"}}</textarea><button class="btn" onclick="run()">▶ Run Query</button><div id="result">Click "Run Query" to execute...</div></div><script>async function run(){{const q=document.getElementById('q').value;const r=await fetch('/graphql?query='+encodeURIComponent(q));const d=await r.json();document.getElementById('result').textContent=JSON.stringify(d,null,2)}}</script></body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"GraphQL API Gateway v1.0 on :{PORT}");s.serve_forever()
