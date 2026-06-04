#!/usr/bin/env python3
"""Poke Labs API Gateway — Single entry point for all services. x402 payments. Port 8700."""
import http.server, json, os
import urllib.request

PORT = 8700
FREE_LIMIT = 3
DATA_DIR = "/tmp/gateway-data"
os.makedirs(DATA_DIR, exist_ok=True)
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

SERVICES = {
    "link-preview": {"port": 8765, "price": 0.01},
    "a2a-discover": {"port": 8780, "price": 0.005},
}

def load(p, d):
    try: return json.load(open(p))
    except: return d
def save(p, d): json.dump(d, open(p,"w"), indent=2)
def usage(ip):
    u=load(f"{DATA_DIR}/usage.json",{})
    if u.get(ip,0)>=FREE_LIMIT: return True,u.get(ip,0)
    u[ip]=u.get(ip,0)+1; save(f"{DATA_DIR}/usage.json",u); return False,u[ip]

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poke Labs API Gateway</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}
.h{background:linear-gradient(135deg,#0f0f23,#1a1a3e);padding:3rem 2rem;text-align:center;border-bottom:1px solid #2a2a5a}
h1{font-size:2.5rem;background:linear-gradient(90deg,#00d4ff,#7b2ff7,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#8892b0;margin-top:.5rem;font-size:1.1rem}.c{max-width:900px;margin:0 auto;padding:2rem}
.svc{background:#12122a;border:1px solid #2a2a5a;border-radius:12px;padding:1.5rem;margin:1rem 0}
.svc h3{color:#00d4ff;margin-bottom:.3rem}
.svc .meta{display:flex;gap:1rem;margin:.5rem 0;font-size:.85rem;color:#8892b0}
.svc .price{color:#4ade80;font-weight:bold}.svc .free{color:#fbbf24}
.svc p{color:#a0a0c0;font-size:.9rem;margin:.5rem 0}
pre{background:#0a0a1a;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;overflow-x:auto;font-size:.8rem;color:#c0c0e0;margin-top:.5rem}
.try{background:linear-gradient(135deg,#1a1a3e,#12122a);border:1px solid #3a3a6a;border-radius:12px;padding:1.5rem;margin:2rem 0}
.try h3{color:#7b2ff7;margin-bottom:1rem}input,select{background:#0a0a1a;border:1px solid #3a3a6a;color:#e0e0e0;padding:.5rem .75rem;border-radius:6px;font-size:.9rem}
button{background:linear-gradient(135deg,#7b2ff7,#5a1fd4);color:#fff;border:none;padding:.5rem 1.5rem;border-radius:6px;cursor:pointer;font-weight:600;margin-left:.5rem}
button:hover{opacity:.9}#result{margin-top:1rem;background:#0a0a1a;border-radius:8px;padding:1rem;font-size:.8rem;white-space:pre-wrap;max-height:300px;overflow-y:auto}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1rem;margin:2rem 0}
.stat{background:#12122a;border:1px solid #2a2a5a;border-radius:8px;padding:1rem;text-align:center}
.stat .n{font-size:1.8rem;font-weight:bold;color:#00d4ff}.stat .l{color:#666;font-size:.75rem}
.footer{text-align:center;padding:2rem;color:#555;font-size:.8rem;border-top:1px solid #1a1a3a;margin-top:2rem}</style></head><body>
<div class="h"><h1>Poke Labs API Gateway</h1><p class="sub">One gateway. Multiple AI services. Pay with USDC on Base.</p></div>
<div class="c">
<div class="stats"><div class="stat"><div class="n">2</div><div class="l">Active Services</div></div>
<div class="stat"><div class="n">x402</div><div class="l">Payment Protocol</div></div>
<div class="stat"><div class="n">3</div><div class="l">Free Calls / IP</div></div>
<div class="stat"><div class="n">Base</div><div class="l">Chain</div></div></div>
<h2 style="color:#e0e0e0;margin:1.5rem 0 1rem">Services</h2>
<div class="svc"><h3>Link Preview</h3>
<div class="meta"><span>POST /api/v1/preview</span><span class="price">$0.01/call</span><span class="free">3 free</span></div>
<p>Extract title, description, image, site_name, favicon from any URL.</p>
<pre>curl -X POST /api/v1/preview -d '{"url":"https://github.com"}'</pre></div>
<div class="svc"><h3>A2A Agent Discovery</h3>
<div class="meta"><span>GET /api/v1/discover</span><span class="price">$0.005/call</span><span class="free">3 free</span></div>
<p>Discover AI agents on the Agent-to-Agent marketplace.</p>
<pre>curl /api/v1/discover?capability=search&limit=10</pre></div>
<div class="try"><h3>Try It</h3>
<div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center">
<select id="svc"><option value="preview">Link Preview</option><option value="discover">A2A Discover</option></select>
<input id="url" placeholder="https://github.com" style="flex:1;min-width:200px">
<button onclick="tryIt()">Call API</button></div>
<div id="result">Response will appear here...</div></div>
<div class="footer">Poke Labs - MIT License - Built by Poke for Alexander Wondwossen<br>Wallet: 0xca3d...6beF (Base)</div></div>
<script>
async function tryIt(){
  const svc=document.getElementById('svc').value;
  const url=document.getElementById('url').value;
  const el=document.getElementById('result');
  el.textContent='Calling...';
  try{
    let r;
    if(svc==='preview'){
      r=await fetch('/api/v1/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
    } else {
      r=await fetch('/api/v1/discover'+(url?'?capability='+encodeURIComponent(url):''));
    }
    const d=await r.json();
    el.textContent=JSON.stringify(d,null,2);
  }catch(e){ el.textContent='Error: '+e.message; }
}
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=self.path.split("?")[0].rstrip("/") or "/"
        if p in ("/","/index.html"): self._html(HTML)
        elif p=="/api/health": self._json(200,{"ok":True,"v":1,"services":list(SERVICES.keys())})
        elif p=="/api/v1/discover":
            ip=self.client_address[0];over,used=usage(ip)
            if over: self._json(402,{"error":"Free limit exceeded","wallet":WALLET,"chain":"base","price":"0.005 USDC/call","usage":{"used":used,"limit":FREE_LIMIT}}); return
            try:
                r=urllib.request.urlopen(f"http://localhost:8780{self.path.replace('/api/v1/discover','/api/discover')}",timeout=10)
                d=json.loads(r.read()); self._json(200,{**d,"_meta":{"free_remaining":FREE_LIMIT-used}})
            except Exception as e: self._json(502,{"error":str(e)})
        elif p=="/api/usage":
            ip=self.client_address[0];u=load(f"{DATA_DIR}/usage.json",{})
            self._json(200,{"used":u.get(ip,0),"limit":FREE_LIMIT,"services":SERVICES})
        else: self._json(404,{"error":"not found"})

    def do_POST(self):
        p=self.path.split("?")[0].rstrip("/")
        if p=="/api/v1/preview":
            ip=self.client_address[0];over,used=usage(ip)
            if over: self._json(402,{"error":"Free limit exceeded","wallet":WALLET,"chain":"base","price":"0.01 USDC/call","usage":{"used":used,"limit":FREE_LIMIT}}); return
            try: body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            except: return self._json(400,{"error":"bad json"})
            url=body.get("url","").strip()
            if not url: return self._json(400,{"error":"url required"})
            try:
                req=urllib.request.Request("http://localhost:8765/api/preview",data=json.dumps({"url":url}).encode(),headers={"Content-Type":"application/json"},method="POST")
                r=urllib.request.urlopen(req,timeout=15); d=json.loads(r.read())
                self._json(200,{**d,"_meta":{"free_remaining":FREE_LIMIT-used}})
            except Exception as e: self._json(502,{"error":str(e)})
        else: self._json(404,{"error":"not found"})

    def _json(self,c,d):
        b=json.dumps(d).encode();self.send_response(c);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.end_headers();self.wfile.write(b)
    def _html(self,h): self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(h.encode())
    def log_message(self,*a): pass

print(f"Poke Labs Gateway on :{PORT}",flush=True)
http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
