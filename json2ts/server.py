#!/usr/bin/env python3
"""Poke Labs — JSON to TypeScript Generator. Port 8775.
Converts JSON objects to TypeScript interfaces/types.
Free tier: 5/day. Paid via x402."""
import http.server, json, urllib.parse, urllib.request, re
from datetime import date

PORT = 8775
FREE_LIMIT = 5
USAGE_FILE = "/tmp/json2ts_usage.json"
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

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

def ts_type(val):
    if val is None: return "null"
    if isinstance(val, bool): return "boolean"
    if isinstance(val, int): return "number"
    if isinstance(val, float): return "number"
    if isinstance(val, str):
        if re.match(r'^\d{4}-\d{2}-\d{2}', val): return "Date"
        if re.match(r'^https?://', val): return "string // URL"
        return "string"
    if isinstance(val, list):
        if not val: return "any[]"
        types = set(ts_type(v) for v in val)
        if len(types) == 1:
            return f"{list(types)[0]}[]"
        return f"({' | '.join(sorted(types))})[]"
    if isinstance(val, dict):
        return None  # nested object, handle separately
    return "any"

def to_pascal(name):
    return ''.join(w.capitalize() for w in re.split(r'[_\-\s]+', name))

def generate_ts(obj, name="Root", indent=0):
    lines = []
    prefix = "  " * indent
    if isinstance(obj, dict):
        lines.append(f"{prefix}export interface {name} {{")
        for key, val in obj.items():
            optional = ""
            ts = ts_type(val)
            if ts is None:
                nested_name = to_pascal(key)
                nested = generate_ts(val, nested_name, indent + 1)
                lines.append(f"{prefix}  {key}{optional}: {nested_name};")
                # We'll collect nested separately
            else:
                lines.append(f"{prefix}  {key}{optional}: {ts};")
        lines.append(f"{prefix}}}")
    return "\n".join(lines)

def generate_full_ts(obj, root_name="Root"):
    """Generate complete TS with nested interfaces."""
    interfaces = []
    def _gen(o, name):
        if not isinstance(o, dict):
            return ts_type(o)
        lines = [f"export interface {name} {{"]
        for key, val in o.items():
            ts = ts_type(val)
            if ts is None:
                nested_name = to_pascal(key)
                _gen(val, nested_name)
                lines.append(f"  {key}: {nested_name};")
            elif isinstance(val, list) and val and isinstance(val[0], dict):
                nested_name = to_pascal(key.rstrip('s')) + "Item"
                _gen(val[0], nested_name)
                lines.append(f"  {key}: {nested_name}[];")
            else:
                lines.append(f"  {key}: {ts};")
        lines.append("}")
        interfaces.append("\n".join(lines))
    _gen(obj, root_name)
    return "\n\n".join(reversed(interfaces))

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/", "/index.html"):
            self._html(LANDING); return
        if p.path == "/api/health":
            self._j({"ok":True,"v":1,"service":"json2ts","free_limit":FREE_LIMIT}); return
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

        if p.path == "/api/convert":
            ok, used = check_limit(client_ip(self.headers))
            if not ok:
                self._x402(); return
            data = body.get("json")
            root_name = body.get("rootName", "Root")
            if data is None:
                self._j({"error":"missing 'json' field"}, 400); return
            if not isinstance(data, (dict, list)):
                self._j({"error":"'json' must be an object or array"}, 400); return
            if isinstance(data, list):
                if not data:
                    self._j({"typescript": f"export type {rootName} = any[]", "remaining": FREE_LIMIT - used}); return
                data = data[0] if len(data) == 0 else data[0]
                root_name = to_pascal(root_name.rstrip('s')) + "Item"
            ts = generate_full_ts(data, to_pascal(root_name))
            self._j({"typescript": ts, "rootName": to_pascal(root_name), "remaining": FREE_LIMIT - used})
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

LANDING = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JSON→TS — Poke Labs</title>
<style>body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem;max-width:800px;margin:0 auto}
h1{color:#7b2ff7}textarea,input,button{padding:.5rem;margin:.25rem;border-radius:4px;border:1px solid #2a2a4a;background:#0a0a0f;color:#e0e0e0}
textarea{width:100%;height:150px;font-family:monospace}button{background:#7b2ff7;border:none;cursor:pointer;padding:.75rem 1.5rem}
pre{background:#141428;padding:1rem;border-radius:8px;overflow-x:auto;white-space:pre-wrap}
.free{color:#4ade80}.paid{color:#fbbf24}code{background:#0a0a1a;padding:.2rem .4rem;border-radius:4px}</style></head><body>
<h1>📦 JSON → TypeScript</h1>
<p>Convert JSON objects to TypeScript interfaces. Handles nested objects, arrays, dates, URLs.</p>
<textarea id="input">{
  "name": "Poke",
  "age": 1,
  "active": true,
  "wallet": "0xca3d...",
  "created": "2026-06-03",
  "services": [
    {"name": "Link Preview", "port": 8765, "up": true}
  ]
}</textarea><br>
<input id="root" value="Agent" placeholder="Root interface name">
<button onclick="convert()">Convert</button>
<pre id="output"></pre>
<p><span class="free">✓ 5 free/day</span> · <span class="paid">💰 Unlimited via x402</span></p>
<p>Wallet: <code>0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code></p>
<script>
async function convert(){
  const j = JSON.parse(document.getElementById('input').value);
  const root = document.getElementById('root').value || 'Root';
  const r = await fetch('/api/convert',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({json:j,rootName:root})});
  const d = await r.json();
  document.getElementById('output').textContent = d.typescript || JSON.stringify(d,null,2);
}
</script></body></html>'''

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"JSON2TS on {PORT}"); s.serve_forever()
