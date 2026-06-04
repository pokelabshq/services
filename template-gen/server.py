#!/usr/bin/env python3
"""Poke Labs — Micro-Service Generator API. Port 8773.
Generates complete Python micro-service code from a service specification.
Input: service name, description, endpoint, pricing.
Output: production-ready Python server.py with free tier + x402."""
import http.server, json, string, urllib.parse, urllib.request
from datetime import date

PORT = 8773
FREE_LIMIT = 5
USAGE_FILE = "/tmp/template_usage.json"

def load_usage():
    try:
        with open(USAGE_FILE) as f: return json.load(f)
    except: return {}

def save_usage(u):
    with open(USAGE_FILE, "w") as f: json.dump(u, f)

def client_ip(h):
    xff = h.get("X-Forwarded-For","")
    return xff.split(",")[0].strip() if xff else h.get("Remote-Addr","127.0.0.1")

def check_limit(ip):
    u = load_usage(); today = str(date.today())
    if u.get("_date") != today: u = {"_date": today}
    used = u.get(ip, 0)
    if used >= FREE_LIMIT:
        return False, used
    u[ip] = used + 1; save_usage(u); return True, used + 1

def to_snake(name):
    return name.lower().strip().replace(" ", "-").replace("_", "-")

def to_port(name):
    return abs(hash(name)) % 1000 + 8780

TEMPLATE = '''#!/usr/bin/env python3
"""Poke Labs — {service_name}. Port {port}.
{description}
Free tier: {free_limit}/day. Paid via x402."""
import http.server, json, urllib.parse, urllib.request, re, os
from datetime import date

PORT = {port}
FREE_LIMIT = {free_limit}
USAGE_FILE = "/tmp/{snake_name}_usage.json"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

def load_usage():
    try:
        with open(USAGE_FILE) as f: return json.load(f)
    except: return {{"_date": "", "counts": {{}}}}

def save_usage(u):
    with open(USAGE_FILE, "w") as f: json.dump(u, f)

def client_ip(h):
    xff = h.get("X-Forwarded-For","")
    return xff.split(",")[0].strip() if xff else h.get("Remote-Addr","127.0.0.1")

def check_limit(ip):
    u = load_usage(); today = str(date.today())
    if u.get("_date") != today: u = {{"_date": today, "counts": {{}}}}
    used = u["counts"].get(ip, 0)
    if used >= FREE_LIMIT:
        return False, used
    u["counts"][ip] = used + 1; save_usage(u); return True, used + 1

{user_code}

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(p.query)
        if p.path in ("/", "/index.html"):
            self._html(LANDING); return
        if p.path == "/api/health":
            self._j({{"ok":True,"v":1,"service":"{snake_name}","free_limit":FREE_LIMIT}}); return
        if p.path == "/api/usage":
            ip = client_ip(self.headers)
            u = load_usage(); today = str(date.today())
            used = u["counts"].get(ip, 0) if u.get("_date") == today else 0
            self._j({{"used":used,"limit":FREE_LIMIT,"remaining":max(0,FREE_LIMIT-used)}}); return
{get_routes}
    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {{}}
{post_routes}
    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def _x402(self):
        body = json.dumps({{"error":"free limit exceeded","wallet":WALLET,"chain":"base","token":"USDC","x402":True}}).encode()
        self.send_response(402); self.send_header("Content-Type","application/json")
        self.send_header("X-Payment-Required","USDC"); self.send_header("X-Payment-Wallet", WALLET)
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(body)
    def _html(self, content):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.end_headers(); self.wfile.write(content.encode())
    def log_message(self, *a): pass

LANDING = \'\'\'<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{service_name} — Poke Labs</title>
<style>body{{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem;max-width:800px;margin:0 auto}}
h1{{color:#7b2ff7}}code{{background:#1a1a2e;padding:.2rem .5rem;border-radius:4px;font-size:.85rem}}
.card{{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;margin:1rem 0}}
.endpoint{{color:#00d4ff;font-weight:bold}}.free{{color:#4ade80}}.paid{{color:#fbbf24}}</style></head><body>
<h1>{service_name}</h1>
<p>{description}</p>
<div class="card">
<div class="endpoint">POST /api/process</div>
<p>Body: {example_body}</p>
<a href="/api/health">Health check →</a>
</div>
<p><span class="free">✓ {free_limit} free/day</span> · <span class="paid">💰 Unlimited via x402</span></p>
<p>Wallet: <code>0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code></p>
</body></html>\'\'\'

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"{service_name} on {{PORT}}"); s.serve_forever()
'''

def generate_service(spec):
    name = spec.get("name", "My API")
    desc = spec.get("description", "A micro-service.")
    endpoint = spec.get("endpoint", "/api/process")
    method = spec.get("method", "POST").upper()
    free_limit = int(spec.get("free_limit", 3))
    input_fields = spec.get("input_fields", [])
    user_code = spec.get("custom_code", '# Your processing logic here\\npass')
    snake = to_snake(name)
    port = to_port(name)
    example_body = "{" + ", ".join(f'"{f}": "..."' for f in input_fields) + "}" if input_fields else "{}"

    # Generate route handlers
    get_routes = ""
    post_routes = ""
    if method == "POST":
        field_checks = ""
        for f in input_fields:
            field_checks += f'        {f} = body.get("{f}", "")\n'
            field_checks += f'        if not {f}:\n            self._j({{"error":"missing {f}"}}, 400); return\n'
        post_routes = f'''        if p.path == "{endpoint}":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            {field_checks}result = process({','.join(input_fields)})
            self._j({{"result": result, "remaining": FREE_LIMIT - used}})
            return'''
    else:
        param_checks = ""
        for f in input_fields:
            param_checks += f'        {f} = qs.get("{f}", [""])[0]\n'
            param_checks += f'        if not {f}:\n            self._j({{"error":"missing {f} parameter"}}, 400); return\n'
        get_routes = f'''        if p.path == "{endpoint}":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            {param_checks}result = process({','.join(input_fields)})
            self._j({{"result": result, "remaining": FREE_LIMIT - used}})
            return'''

    code = TEMPLATE.format(
        service_name=name, port=port, description=desc, free_limit=free_limit,
        snake_name=snake, user_code=user_code, get_routes=get_routes,
        post_routes=post_routes, example_body=example_body
    )
    return code, port, snake

WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/", "/index.html"):
            self._html(LANDING); return
        if p.path == "/api/health":
            self._j({"ok":True,"v":1,"service":"template-gen","free_limit":FREE_LIMIT}); return
        if p.path == "/api/usage":
            ip = client_ip(self.headers)
            u = load_usage(); today = str(date.today())
            used = u.get(ip, 0) if u.get("_date") == today else 0
            self._j({"used":used,"limit":FREE_LIMIT,"remaining":max(0,FREE_LIMIT-used)}); return
        self._j({"error":"not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {}

        if p.path == "/api/generate":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            spec = body.get("spec", {})
            if not spec.get("name"):
                self._j({"error":"spec.name is required"}, 400); return
            code, port, snake = generate_service(spec)
            self._j({
                "service_name": spec["name"],
                "port": port,
                "file_name": f"{snake}/server.py",
                "code": code,
                "instructions": f"1. mkdir -p {snake}\n2. Write code to {snake}/server.py\n3. nohup python3 {snake}/server.py &\n4. Add to gateway PROXIES: \"{snake}\": {port}",
                "remaining": FREE_LIMIT - used
            })
            return
        self._j({"error":"not found"}, 404)

    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)

    def _x402(self):
        body = json.dumps({"error":"free limit exceeded","wallet":WALLET,"chain":"base","token":"USDC","x402":True}).encode()
        self.send_response(402); self.send_header("Content-Type","application/json")
        self.send_header("X-Payment-Required","USDC"); self.send_header("X-Payment-Wallet", WALLET)
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(body)

    def _html(self, content):
        self.send_response(200); self.send_header("Content-Type","text/html")
        self.end_headers(); self.wfile.write(content.encode())

    def log_message(self, *a): pass

LANDING = \'\'\'<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Service Generator — Poke Labs</title>
<style>body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem;max-width:800px;margin:0 auto}
h1{color:#7b2ff7}textarea,input,button{padding:.5rem;margin:.25rem;border-radius:4px;border:1px solid #2a2a4a;background:#0a0a0f;color:#e0e0e0}
textarea{width:100%;height:200px;font-family:monospace}button{background:#7b2ff7;border:none;cursor:pointer;padding:.75rem 1.5rem}
pre{background:#141428;padding:1rem;border-radius:8px;overflow-x:auto;max-height:400px}</style></head><body>
<h1>⚡ Service Generator</h1>
<p>Generate a complete Poke Labs micro-service from a JSON spec. Free tier: 5/day.</p>
<h2>Example Spec</h2>
<pre>{
  "name": "Sentiment Analyzer",
  "description": "Analyze text sentiment (positive/negative/neutral)",
  "endpoint": "/api/analyze",
  "method": "POST",
  "free_limit": 3,
  "input_fields": ["text"],
  "custom_code": "def process(text):\\n    # Simple keyword-based sentiment\\n    pos = [\'good\',\'great\',\'love\',\'awesome\',\'excellent\']\\n    neg = [\'bad\',\'terrible\',\'hate\',\'awful\',\'worst\']\\n    words = text.lower().split()\\n    score = sum(1 for w in words if w in pos) - sum(1 for w in words if w in neg)\\n    return {\'sentiment\': \'positive\' if score > 0 else \'negative\' if score < 0 else \'neutral\', \'score\': score}"
}</pre>
<h2>Try It</h2>
<textarea id="spec">{
  "name": "Sentiment Analyzer",
  "description": "Analyze text sentiment",
  "endpoint": "/api/analyze",
  "method": "POST",
  "free_limit": 3,
  "input_fields": ["text"]
}</textarea><br>
<button onclick="generate()">Generate Service</button>
<pre id="output"></pre>
<script>
async function generate(){
  const spec = JSON.parse(document.getElementById(\'spec\').value);
  const r = await fetch(\'/api/generate\', {method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({spec})});
  const d = await r.json();
  document.getElementById(\'output\').textContent = d.code || JSON.stringify(d,null,2);
}
</script></body></html>\'\'\'

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Template Gen on {PORT}"); s.serve_forever()
