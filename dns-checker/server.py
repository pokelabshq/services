#!/usr/bin/env python3
"""DNS Checker API — check DNS records for any domain. Port 8769."""
import http.server, json, subprocess, urllib.parse, re, os

PORT = 8769
LIMIT_FILE = "/tmp/dns_usage.json"
FREE_LIMIT = 3

HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DNS Checker — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh;display:flex;flex-direction:column;align-items:center}
.h{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:3rem 2rem;text-align:center;width:100%;border-bottom:1px solid #2a2a4a}
h1{font-size:2.5rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
form{margin:2rem auto;display:flex;gap:.5rem;flex-wrap:wrap;justify-content:center;max-width:600px;padding:0 1rem}
input{flex:1;min-width:200px;padding:.75rem 1rem;background:#141428;border:1px solid #2a2a4a;border-radius:8px;color:#e0e0e0;font-size:1rem}
input:focus{outline:none;border-color:#7b2ff7}
.s{padding:.75rem;background:#141428;border:1px solid #2a2a4a;border-radius:8px;color:#e0e0e0}
button{padding:.75rem 1.5rem;background:linear-gradient(135deg,#7b2ff7,#00d4ff);border:none;border-radius:8px;color:#fff;font-size:1rem;cursor:pointer}
button:hover{opacity:.9}
#r{width:100%;max-width:700px;margin:1rem;padding:0 1rem}
.rec{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;margin-bottom:.5rem}
.t{color:#00d4ff;font-weight:bold}
.v{color:#e0e0e0;margin-left:1rem;word-break:break-all}
.e{color:#ff6b6b;padding:1rem}
.f{margin:auto auto 1rem;color:#555;font-size:.85rem}
</style></head><body>
<div class="h"><h1>DNS Checker</h1><p style="color:#888;margin-top:.5rem">Check DNS records for any domain</p></div>
<form onsubmit="return chk()">
<input id="d" placeholder="example.com" required>
<select id="t" class="s"><option value="A">A</option><option value="AAAA">AAAA</option><option value="CNAME">CNAME</option><option value="MX">MX</option><option value="TXT">TXT</option><option value="NS">NS</option></select>
<button type="button" onclick="chk()">Check</button>
</form>
<div id="r"></div>
<div class="f">Poke Labs MIT</div>
<script>
async function chk(){
const d=document.getElementById('d').value.trim(),t=document.getElementById('t').value,e=document.getElementById('r');
e.innerHTML='<div class="rec" style="color:#888">Loading...</div>';
try{
const r=await fetch('/api/check?domain='+encodeURIComponent(d)+'&type='+t),j=await r.json();
if(Array.isArray(j))e.innerHTML=j.map(x=>'<div class="rec"><span class="t">'+x.type+'</span><span class="v">'+x.value+'</span></div>').join('');
else e.innerHTML='<div class="e">'+(j.error||'Error')+'</div>';
}catch(e){e.innerHTML='<div class="e">'+e.message+'</div>'}return false;
}
</script></body></html>"""

def get_usage(ip):
    try:
        with open(LIMIT_FILE) as f: return json.load(f).get(ip, 0)
    except: return 0

def inc_usage(ip):
    try:
        with open(LIMIT_FILE) as f: d = json.load(f)
    except: d = {}
    d[ip] = d.get(ip, 0) + 1
    with open(LIMIT_FILE, "w") as f: json.dump(d, f)

def check_dns(domain, rtype):
    domain = re.sub(r'[^a-zA-Z0-9.\-]', '', domain)
    if not domain: return []
    try:
        r = subprocess.run(["dig","+short",domain,rtype], capture_output=True, text=True, timeout=10)
        lines = [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]
        if not lines:
            r2 = subprocess.run(["nslookup","-type="+rtype,domain], capture_output=True, text=True, timeout=10)
            if "Can't find" in r2.stdout or "NXDOMAIN" in r2.stdout: return []
        return [{"type":rtype,"value":l} for l in lines if l]
    except Exception as e:
        return [{"type":"ERROR","value":str(e)}]

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path in ("/","/index.html"):
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers()
            self.wfile.write(HTML.encode()); return
        if p.path == "/api/health":
            self._j({"ok":True,"v":1,"free_limit":FREE_LIMIT}); return
        if p.path == "/api/usage":
            self._j({"used":get_usage(self.client_address[0]),"limit":FREE_LIMIT}); return
        if p.path == "/api/check":
            qs = urllib.parse.parse_qs(p.query)
            domain = qs.get("domain",[""])[0].strip()
            rtype = qs.get("type",["A"])[0].upper()
            if rtype not in ("A","AAAA","CNAME","MX","TXT","NS"): rtype = "A"
            ip = self.client_address[0]
            if get_usage(ip) >= FREE_LIMIT:
                self._j({"error":"Limit exceeded. Pay via x402.","wallet":"0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"},402); return
            inc_usage(ip)
            res = check_dns(domain, rtype)
            if res and res[0].get("type")=="ERROR": self._j({"error":res[0]["value"]},500)
            else: self._j(res); return
        self._j({"error":"not found"},404)
    def _j(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

if __name__=="__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"DNS Checker on {PORT}"); s.serve_forever()
