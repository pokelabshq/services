#!/usr/bin/env python3
import http.server, json, urllib.request, urllib.parse, time
PORT=8766; START=time.time()
def up():
    s=time.time()-START;h,r=divmod(int(s),3600);m,sec=divmod(r,60);return f"{h}h{m}m{sec}s"
def preview(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        resp=urllib.request.urlopen(req,timeout=10)
        data=resp.read().decode("utf-8",errors="ignore");lo=data.lower();title=url;desc="";img=""
        if"<title>"in lo:
            try:t=lo.split("<title>")[1].split("</title>")[0].strip().replace("\n"," ")[:200];title=t if t else url
            except:pass
        if'name="description"'in lo:
            try:desc=lo.split('name="description"')[1].split('content="')[1].split('"')[0][:300]
            except:pass
        if"og:image"in lo:
            try:img=lo.split('og:image"')[1].split('content="')[1].split('"')[0][:500]
            except:pass
        site=url.split("/")[2]if"://"in url else""
        return{"url":url,"title":title,"description":desc,"image":img,"site_name":site}
    except Exception as e:return{"url":url,"error":str(e)}
H="""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}a{color:#00ffaa;text-decoration:none}
.h{text-align:center;padding:60px 20px;background:radial-gradient(ellipse at top,rgba(0,255,170,0.08),transparent 60%)}h1{font-size:2.5rem;font-weight:800;margin-bottom:12px}h1 span{color:#00ffaa}.s{color:#666;max-width:500px;margin:0 auto 24px}
.b{display:inline-block;padding:12px 28px;border-radius:10px;font-weight:700;margin:8px;border:none;font-size:.95rem;cursor:pointer}.bp{background:#00ffaa;color:#0a0a1a}.bs{background:transparent;color:#e0e0e2;border:1px solid rgba(255,255,255,0.15)}
.stats{display:flex;justify-content:center;gap:40px;padding:24px;border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05);flex-wrap:wrap}.st{text-align:center}.st .n{font-size:1.5rem;font-weight:700;color:#00ffaa}.st .l{color:#555;font-size:.7rem}
.sec{padding:50px 20px;max-width:900px;margin:0 auto}h2{text-align:center;font-size:1.4rem;margin-bottom:24px}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}.card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px}.card:hover{border-color:#00ffaa}.card h3{font-size:.95rem;margin-bottom:8px}.card p{color:#666;font-size:.8rem}
.pw{max-width:560px;margin:0 auto 30px}.pw input{width:100%;padding:14px 18px;border-radius:10px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.03);color:#e0e0e2;font-size:1rem;margin-bottom:12px;box-sizing:border-box}.pw input:focus{outline:none;border-color:#00ffaa}.pw button{width:100%;padding:14px;background:#00ffaa;color:#0a0a1a;border:none;border-radius:10px;font-weight:700;font-size:1rem;cursor:pointer}
#r{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px;display:none;margin-top:16px}#r.show{display:block}#r img{max-width:100%;border-radius:8px;margin-bottom:12px}#r h3{color:#00ffaa;margin-bottom:6px}#r p{color:#888;font-size:.9rem}#r .e{color:#ff6b6b}
footer{text-align:center;padding:40px;color:#444;font-size:.75rem}</style></head><body>
<div class="h"><h1>Poke <span>Labs</span></h1><p class="s">Open-source microservices and AI tools built by Alexander and the Poke Labs community.</p><button class="b bp"onclick="document.getElementById('try').scrollIntoView({behavior:'smooth'})">Try Link Preview</button>&nbsp;<a href="https://github.com/pokelabshq"class="b bs">GitHub</a></div>
<div class="stats"><div class="st"><div class="n">55+</div><div class="l">Services</div></div><div class="st"><div class="n">12</div><div class="l">Skills</div></div><div class="st"><div class="n">MIT</div><div class="l">License</div></div><div class="st"><div class="n">1.0</div><div class="l">Gateway</div></div></div>
<div class="sec"id="try"><h2>Try Link Preview — Free</h2><div class="pw"><input type="text"id="url"placeholder="Paste a URL..."value="https://github.com"><button onclick="go()">Preview</button><div id="r"></div></div></div>
<div class="sec"><h2>All Services</h2><div class="cards"><div class="card"><h3>Link Preview API</h3><p>Extract title, description, and image from any URL. Free tier + x402 pay-per-use.</p></div><div class="card"><h3>Poke Hub</h3><p>All-in-one GitHub bot: auto-reply, stale closer, auto-labeler, dashboard.</p></div><div class="card"><h3>AI Council</h3><p>Automated multi-repo management: stale issues, PR reviews, dependency updates.</p></div><div class="card"><h3>Prometheus Metrics</h3><p>Monitor all services with a standard Prometheus /metrics endpoint.</p></div><div class="card"><h3>x402 Payments</h3><p>Accept USDC micropayments via the x402 protocol.</p></div><div class="card"><h3>Skills Marketplace</h3><p>Discover and install agent skills. 12 skills available.</p></div></div></div>
<footer>2026 Poke Labs — Built by Alexander Wondwossen, Toronto. MIT Licensed.</footer>
<script>async function go(){const u=document.getElementById("url").value.trim();if(!u)return;const r=document.getElementById("r");r.className="show";r.innerHTML="<p style='color:#888'>Loading...</p>";try{const d=await(await fetch("/api/preview",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url:u})})).json();if(d.error)r.innerHTML="<p class='e'>"+d.error+"</p>";else{let i=d.image?"<img src='"+d.image+"' alt=''>":"";r.innerHTML=i+"<h3>"+(d.title||u)+"</h3><p>"+(d.description||"")+"</p>";}}catch(e){r.innerHTML="<p class='e'>Failed: "+e.message+"</p>";}}document.getElementById("url").addEventListener("keydown",e=>{if(e.key==="Enter")go()});</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/":self.s(200,H,"h")
        elif p.path=="/api/health":self.s(200,{"ok":True,"v":1,"uptime":up(),"port":PORT})
        elif p.path=="/dashboard":self.s(200,f"<!DOCTYPE html><html><head><meta charset=UTF-8><title>Dashboard</title><style>body{{font-family:system-ui;background:#0a0a1a;color:#e0e0e2;padding:40px}}h1{{color:#00ffaa}}</style></head><body><h1>Poke Gateway v1</h1><p>Uptime: {up()} | Port: {PORT}</p><p>55+ services on disk. <a href='/' style='color:#00ffaa'>Home</a></p></body></html>","h")
        else:self.s(404,{"error":"not found"})
    def do_POST(self):
        p=urllib.parse.urlparse(self.path)
        if p.path=="/api/preview":
            try:
                body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
                url=body.get("url","").strip()
                if not url:self.s(400,{"error":"missing url"});return
                if not url.startswith("http"):url="https://"+url
                self.s(200,preview(url))
            except Exception as e:self.s(500,{"error":str(e)})
        else:self.s(404,{"error":"not found"})
    def s(self,c,d,t="j"):
        body=(json.dumps(d,default=str)if t=="j"else d).encode()
        self.send_response(c);self.send_header("Content-Type","application/json"if t=="j"else"text/html; charset=utf-8")
        if t=="j":self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a):pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Poke Gateway v1 on :{PORT}");s.serve_forever()
