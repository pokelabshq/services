#!/usr/bin/env python3
"""Poke Labs Gateway v3.0 — Landing page + Link Preview API + Dashboard on one port."""
import http.server, json, urllib.request, urllib.parse, time, html as H, re, os

PORT = 8766
VERSION = 3
START = time.time()
REQS = 0

def track(): global REQS; REQS += 1

def preview(url):
    track()
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (PokeLabs/3.0)"})
        resp = urllib.request.urlopen(req, timeout=10)
        ct = resp.headers.get("Content-Type","")
        if "text/html" not in ct:
            return {"url":url,"title":url.split("/")[-1] or url,"description":"Content-Type: "+ct,"image":"","site_name":""}
        data = resp.read().decode("utf-8",errors="ignore")
        title = _og(data,"title") or _tag(data,"title") or url
        desc = _og(data,"description") or _meta(data,"description") or ""
        image = _og(data,"image") or ""
        site = _og(data,"site_name") or (url.split("/")[2] if "/" in url else "")
        if image and not image.startswith("http"):
            base = url.split("/")[0]+"//"+url.split("/")[2]
            image = base+("" if image.startswith("/") else "/")+image
        return {"url":url,"title":title[:200],"description":desc[:500],"image":image,"site_name":site}
    except Exception as e:
        return {"url":url,"error":str(e)}

def _og(h,p):
    m = re.search(f'<meta[^>]+property=["\'']og:{p}["\'']([^>]+)>',h,re.I)
    if not m: m = re.search(f'<meta[^>]+content=["\'']([^"\'']*)["\''].*?property=["\'']og:{p}["\'']>',h,re.I)
    if m:
        c = re.search(r'content=["\'']([^"\'']*)["\'']>',m.group(0),re.I)
        return c.group(1) if c else ""
    return ""
def _meta(h,n):
    m = re.search(f'<meta[^>]+name=["\'']{n}["\'']([^>]+)>',h,re.I)
    if m:
        c = re.search(r'content=["\'']([^"\'']*)["\'']>',m.group(0),re.I)
        return c.group(1) if c else ""
    return ""
def _tag(h,t):
    m = re.search(f'<{t}[^>]*>(.*?)</{t}>',h,re.I|re.S)
    return m.group(1).strip()[:200] if m else ""

def up():
    s=time.time()-START; h,r=divmod(int(s),3600); m,sec=divmod(r,60)
    return f"{h}h {m}m {sec}s"

def jr(h,d,c=200):
    b=json.dumps(d,default=str).encode()
    h.send_response(c); h.send_header("Content-Type","application/json")
    h.send_header("Access-Control-Allow-Origin","*"); h.send_header("Content-Length",str(len(b)))
    h.end_headers(); h.wfile.write(b)

def hr(h,ht,c=200):
    b=ht.encode()
    h.send_response(c); h.send_header("Content-Type","text/html")
    h.send_header("Content-Length",str(len(b)))
    h.end_headers(); h.wfile.write(b)

NAV='<nav style="display:flex;justify-content:space-between;align-items:center;padding:14px 24px;background:rgba(10,10,26,0.95);backdrop-filter:blur(12px);position:sticky;top:0;z-index:100;border-bottom:1px solid rgba(255,255,255,0.06)"><span style="color:#00ffaa;font-weight:700;font-size:1.1rem">Poke Labs</span><div style="display:flex;gap:20px;font-size:.85rem"><a href="/" style="color:#888;text-decoration:none">Home</a><a href="/dashboard" style="color:#888;text-decoration:none">Dashboard</a><a href="/api/docs" style="color:#888;text-decoration:none">API</a><a href="https://github.com/pokelabshq" style="color:#888;text-decoration:none">GitHub</a></div></nav>'

FOOT='<footer style="text-align:center;padding:40px 20px;color:#444;font-size:.75rem;border-top:1px solid rgba(255,255,255,0.04)"><p>2026 Poke Labs — Built by Alexander Wondwossen</p><p style="margin-top:6px"><a href="https://github.com/pokelabshq" style="color:#00ffaa">GitHub</a> &middot; MIT Licensed</p></footer>'

CSS='<style>*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}a{color:#00ffaa;text-decoration:none}a:hover{opacity:.8}</style>'

def landing(qs):
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs — Open Source AI Agent Ecosystem</title>{CSS}<style>.hero{{text-align:center;padding:70px 20px 50px;background:radial-gradient(ellipse at 50% 0%,rgba(0,255,170,0.07) 0%,transparent 60%)}}h1{{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:800;line-height:1.2;margin-bottom:12px}}h1 span{{color:#00ffaa}}.sub{{color:#666;font-size:1rem;max-width:550px;margin:0 auto 24px}}.btn{{display:inline-block;padding:10px 24px;border-radius:10px;font-weight:600;font-size:.9rem;cursor:pointer;border:none}}.btn-primary{{background:#00ffaa;color:#0a0a1a}}.btn-secondary{{background:transparent;color:#e0e0e2;border:1px solid rgba(255,255,255,0.1)}}.stats{{display:flex;justify-content:center;gap:32px;padding:24px;border-top:1px solid rgba(255,255,255,0.04);border-bottom:1px solid rgba(255,255,255,0.04);flex-wrap:wrap}}.stat{{text-align:center}}.stat .n{{font-size:1.4rem;font-weight:700;color:#00ffaa}}.stat .l{{color:#555;font-size:.7rem}}.section{{padding:50px 20px}}.section h2{{text-align:center;font-size:1.4rem;margin-bottom:6px}}.section .sub2{{text-align:center;color:#666;font-size:.85rem;margin-bottom:30px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;max-width:1000px;margin:0 auto}}.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;transition:transform .2s,border-color .2s}}.card:hover{{transform:translateY(-2px);border-color:#00ffaa}}.card h3{{font-size:.95rem;margin-bottom:6px}}.card p{{color:#666;font-size:.8rem}}.tag{{display:inline-block;background:rgba(0,255,170,0.08);color:#00ffaa;padding:2px 8px;border-radius:8px;font-size:.65rem;margin:2px}}.pwrap{{max-width:600px;margin:30px auto}}.pinput{{display:flex;gap:8px;margin-bottom:16px}}.pinput input{{flex:1;padding:12px 16px;border-radius:10px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.03);color:#e0e0e2;outline:none;font-size:.9rem}}.pinput input:focus{{border-color:#00ffaa}}.pinput button{{padding:12px 20px;background:#00ffaa;color:#0a0a1a;border-radius:10px;border:none;font-weight:600;cursor:pointer}}.presult{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;display:none}}.presult.show{{display:block}}.presult img{{max-width:100%;border-radius:8px;margin-bottom:12px}}.presult h3{{color:#00ffaa;margin-bottom:4px}}.presult p{{color:#888;font-size:.85rem}}.presult .err{{color:#ff6b6b}}</style></head><body>{NAV}<section class="hero"><h1>AI Agents that <span>work for you</span></h1><p class="sub">Open-source microservices, GitHub automation, and AI tools — built by the Poke Labs ecosystem.</p><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><a href="#try" class="btn btn-primary">Try Link Preview</a><a href="https://github.com/pokelabshq" class="btn btn-secondary">View on GitHub</a></div></section><div class="stats"><div class="stat"><div class="n">55+</div><div class="l">Services</div></div><div class="stat"><div class="n">12</div><div class="l">Skills</div></div><div class="stat"><div class="n">MIT</div><div class="l">License</div></div><div class="stat"><div class="n">{REQS}</div><div class="l">Requests</div></div></div><section class="section" id="try"><h2>Try Link Preview</h2><p class="sub2">Extract title, description, and image from any URL — free, no signup.</p><div class="pwrap"><div class="pinput"><input type="text" id="urlInput" placeholder="Enter a URL... (e.g. https://github.com)" value="https://github.com"><button onclick="doPreview()">Preview</button></div><div id="result" class="presult"></div></div></section><section class="section" style="background:rgba(255,255,255,0.01)"><h2>Services</h2><p class="sub2">Everything you need to build with AI agents.</p><div class="grid"><div class="card"><h3>Link Preview API</h3><p>Extract metadata from any URL. Perfect for chat apps and social feeds.</p><div><span class="tag">API</span><span class="tag">Metadata</span><span class="tag">x402</span></div></div><div class="card"><h3>Poke Hub</h3><p>All-in-one GitHub bot: auto-reply, stale closer, auto-labeler, and dashboard.</p><div><span class="tag">GitHub</span><span class="tag">Automation</span></div></div><div class="card"><h3>AI Council</h3><p>Automated repo management: stale issues, PR reviews, dependency updates.</p><div><span class="tag">Management</span><span class="tag">Multi-repo</span></div></div><div class="card"><h3>Prometheus Metrics</h3><p>Monitor all services with Prometheus-compatible /metrics endpoint.</p><div><span class="tag">Monitoring</span><span class="tag">Prometheus</span></div></div><div class="card"><h3>x402 Payments</h3><p>Accept USDC micropayments via x402 protocol across all services.</p><div><span class="tag">Payments</span><span class="tag">USDC</span></div></div><div class="card"><h3>Skills Marketplace</h3><p>Discover and install skills to extend your AI agent capabilities.</p><div><span class="tag">Skills</span><span class="tag">Marketplace</span></div></div></div></section>{FOOT}<script>async function doPreview(){{const url=document.getElementById("urlInput").value.trim();if(!url)return;const r=document.getElementById("result");r.classList.add("show");r.innerHTML="<p style=\"color:#888\">Loading...</p>";try{{const resp=await fetch("/api/preview",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{url:url}})}});const data=await resp.json();if(data.error){{r.innerHTML="<p class=\"err\">"+data.error+"</p>"}}else{{let img=data.image?'<img src="'+data.image+'" alt="preview">':"";r.innerHTML=img+"<h3>"+(data.title||url)+"</h3><p>"+(data.description||"")+"</p><p style=\"color:#555;font-size:.7rem\">"+(data.site_name||"")+"</p>"}}}}catch(e){{r.innerHTML="<p class=\"err\">Failed: "+e.message+"</p>"}}}}document.getElementById("urlInput").addEventListener("keydown",e=>{{if(e.key==="Enter")doPreview()}});</script></body></html>'

def dashboard():
    return f'<!DOCTYPE html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Dashboard — Poke Labs</title>{CSS}<style>.dash{{max-width:900px;margin:0 auto;padding:30px 20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:20px 0}}.metric{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;text-align:center}}.metric .val{{font-size:1.6rem;font-weight:700;color:#00ffaa}}.metric .lbl{{color:#555;font-size:.7rem;margin-top:4px}}.log{{background:rgba(0,0,0,0.3);border-radius:8px;padding:16px;font-family:monospace;font-size:.75rem;color:#888}}h2{{color:#e0e0e2;margin:24px 0 12px;font-size:1rem}}</style></head><body>{NAV}<div class="dash"><h1 style="color:#00ffaa;font-size:1.5rem">Dashboard</h1><p style="color:#666;font-size:.85rem">Poke Labs Gateway v{VERSION} — Real-time metrics</p><div class="grid"><div class="metric"><div class="val">v{VERSION}</div><div class="lbl">Version</div></div><div class="metric"><div class="val">{REQS}</div><div class="lbl">Requests</div></div><div class="metric"><div class="val">{up()}</div><div class="lbl">Uptime</div></div><div class="metric"><div class="val">{PORT}</div><div class="lbl">Port</div></div><div class="metric"><div class="val">55+</div><div class="lbl">Services</div></div><div class="metric"><div class="val">12</div><div class="lbl">Skills</div></div></div><h2>API Endpoints</h2><div class="log"><div><span style="color:#00ffaa">GET</span> / — Landing page</div><div><span style="color:#00ffaa">GET</span> /dashboard — Dashboard</div><div><span style="color:#00ffaa">GET</span> /api/health — Health</div><div><span style="color:#00ffaa">POST</span> /api/preview — Preview</div><div><span style="color:#00ffaa">GET</span> /api/stats — Stats</div><div><span style="color:#00ffaa">GET</span> /api/docs — Docs</div></div><h2>Funding</h2><div class="metric" style="border-color:rgba(255,68,68,0.3)"><div class="val" style="color:#ff6b6b">$-0.01</div><div class="lbl">NEEDS FUNDING</div></div><p style="color:#666;font-size:.8rem;margin-top:8px">Wallet: <code style="background:rgba(255,255,255,0.03);padding:2px 6px;border-radius:4px">0xca3d86e4EDE205E6d72496BC2919c88b994B6beF</code> (Base)</p></div>{FOOT}</body></html>'

def docs():
    return f'<!DOCTYPE html><head><meta charset="UTF-8"><title>API Docs — Poke Labs</title>{CSS}<style>.docs{{max-width:700px;margin:0 auto;padding:30px 20px}}.ep{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;margin:16px 0}}.m{{display:inline-block;background:#00ffaa;color:#0a0a1a;padding:2px 10px;border-radius:6px;font-size:.75rem;font-weight:700;margin-right:8px}}pre{{background:rgba(0,0,0,0.3);border-radius:8px;padding:16px;font-size:.8rem;overflow-x:auto;color:#ccc;margin-top:12px}}</style></head><body>{NAV}<div class="docs"><h1 style="color:#00ffaa">API Docs</h1><p style="color:#666;font-size:.85rem">Poke Labs Gateway v{VERSION}</p><div class="ep"><span class="m">POST</span> <code>/api/preview</code><p style="color:#888;font-size:.8rem;margin-top:8px">Extract metadata from any URL.</p><pre>Request:\n{{"url": "https://github.com"}}\n\nResponse:\n{{"title": "GitHub", "description": "...", "image": "...", "site_name": "github.com"}}</pre></div><div class="ep"><span class="m">GET</span> <code>/api/health</code><p style="color:#888;font-size:.8rem;margin-top:8px">Health check.</p><pre>{{"ok": true, "v": {VERSION}, "uptime": "{up()}", "requests": {REQS}}}</pre></div><div class="ep"><span class="m">GET</span> <code>/api/stats</code><p style="color:#888;font-size:.8rem;margin-top:8px">Usage stats.</p><pre>{{"version": {VERSION}, "uptime": "{up()}", "total_requests": {REQS}, "port": {PORT}}}</pre></div></div>{FOOT}</body></html>'

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=urllib.parse.urlparse(self.path); qs=urllib.parse.parse_qs(p.query)
        if p.path=="/": hr(self,landing(qs))
        elif p.path=="/dashboard": hr(self,dashboard())
        elif p.path=="/api/health": jr(self,{"ok":True,"v":VERSION,"uptime":up(),"requests":REQS,"port":PORT})
        elif p.path=="/api/stats": jr(self,{"version":VERSION,"uptime":up(),"total_requests":REQS,"port":PORT})
        elif p.path=="/api/docs": hr(self,docs())
        else: jr(self,{"error":"Not found"},404)
    def do_POST(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/api/preview":
            try:
                body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
                url=body.get("url","").strip()
                if not url: jr(self,{"error":"Missing url"},400); return
                if not url.startswith("http"): url="https://"+url
                jr(self,preview(url))
            except json.JSONDecodeError: jr(self,{"error":"Invalid JSON"},400)
            except Exception as e: jr(self,{"error":str(e)},500)
        else: jr(self,{"error":"Not found"},404)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()
    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Poke Labs Gateway v{VERSION} on :{PORT}"); s.serve_forever()
