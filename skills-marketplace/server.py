#!/usr/bin/env python3
"""Skills Marketplace v2.0 — Browse, search, install Poke Labs skills. Port: 8781. Zero deps."""
import http.server, json, os, html as h, urllib.parse

PORT = 8781
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
SERVICES_DIR = "/home/alx/services"
INSTALL_BASE = "/home/alx/.pokelabs/skills"

def scan():
    skills = []
    try:
        for name in sorted(os.listdir(SERVICES_DIR)):
            p = os.path.join(SERVICES_DIR, name)
            if not os.path.isdir(p): continue
            files = os.listdir(p)
            desc = ""
            for md in ["SKILL.md","README.md"]:
                mp = os.path.join(p, md)
                if os.path.exists(mp):
                    with open(mp) as f:
                        for line in f:
                            l = line.strip()
                            if l and not l.startswith("#"):
                                desc = l[:180]; break
                    if desc: break
            cat = "utility"
            c = (desc+" "+name).lower()
            if any(k in c for k in ["github","pr","issue","webhook","repo","git","pull"]): cat="github"
            elif any(k in c for k in ["api","http","endpoint","rest","gateway"]): cat="api"
            elif any(k in c for k in ["web","site","landing","page","dashboard","html"]): cat="web"
            elif any(k in c for k in ["bot","telegram","discord","social","twitter"]): cat="social"
            elif any(k in c for k in ["monitor","health","uptime","status","check"]): cat="monitoring"
            elif any(k in c for k in ["data","analytics","stats","metric"]): cat="data"
            elif any(k in c for k in ["ai","ml","model","inference","llm","chat"]): cat="ai"
            elif any(k in c for k in ["pay","wallet","usdc","x402","crypto","price","billing"]): cat="finance"
            elif any(k in c for k in ["gen","create","build","template","scaffold"]): cat="generator"
            elif any(k in c for k in ["short","url","link","qr","hash","uuid","convert"]): cat="tools"
            skills.append({"id":name,"name":name.replace("-"," ").replace("_"," ").title(),"desc":desc or f"Poke Labs skill: {name}","cat":cat,"files":len(files),"has_md":"SKILL.md" in files})
    except: pass
    return skills

ALL = scan()

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        path = urllib.parse.urlparse(self.path).path
        if path=="/api/health": self.json({"ok":True,"v":2,"port":PORT,"skills":len(ALL),"wallet":WALLET})
        elif path=="/api/skills":
            cat=q.get("cat",[None])[0]; qq=q.get("q",[""])[0].lower()
            r=ALL
            if cat: r=[s for s in r if s["cat"]==cat]
            if qq: r=[s for s in r if qq in s["name"].lower() or qq in s["desc"].lower() or qq in s["id"].lower()]
            self.json({"ok":True,"skills":r,"total":len(r),"categories":sorted(set(s["cat"] for s in ALL))})
        elif path.startswith("/api/skill/"):
            sid=path[10:]; s=next((x for x in ALL if x["id"]==sid),None)
            if not s: self.json({"error":"Not found"},404);return
            mp=os.path.join(SERVICES_DIR,sid,"SKILL.md")
            if os.path.exists(mp):
                with open(mp) as f: s["readme"]=f.read()
            self.json({"ok":True,"skill":s})
        elif path=="/api/install":
            sid=q.get("id",[""])[0]
            if not sid or not any(s["id"]==sid for s in ALL): self.json({"error":"Unknown skill"},404);return
            dest=os.path.join(INSTALL_BASE,sid); os.makedirs(dest,exist_ok=True)
            src=os.path.join(SERVICES_DIR,sid); copied=[]
            for f in ["SKILL.md","README.md"]:
                sp=os.path.join(src,f)
                if os.path.exists(sp):
                    with open(sp) as sf: c=sf.read()
                    with open(os.path.join(dest,f),"w") as df: df.write(c)
                    copied.append(f)
            self.json({"ok":True,"installed":sid,"dest":dest,"files":copied})
        elif path=="/": self.home(q.get("cat",[""])[0],q.get("q",[""])[0])
        else: self.json({"error":"Not found"},404)

    def home(self,fc,sq):
        cats={}
        for s in ALL: cats.setdefault(s["cat"],[]).append(s)
        opts="".join(f'<option value="{c}" {"selected" if c==fc else ""}>{c.title()} ({len(v)})</option>' for c,v in sorted(cats.items()))
        ch=""
        for cat,items in sorted(cats.items()):
            if fc and cat!=fc: continue
            if sq: items=[s for s in items if sq in s["name"].lower() or sq in s["desc"].lower() or sq in s["id"].lower()]
            if not items: continue
            ch+=f'<div class="cat"><h2>{cat.title()} <span>({len(items)})</span></h2><div class="grid">'
            for s in items:
                ch+=f'<div class="card" onclick="location.href=\'/api/skill/{s["id"]}\'"><div class="cc">{s["cat"]}</div><div class="ct">{h.escape(s["name"])}</div><div class="cd">{h.escape(s["desc"][:100])}</div><div class="cf">{s["files"]} files</div></div>'
            ch+='</div></div>'
        body=f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs — Skills Marketplace v2</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}.hd{{padding:50px 20px 30px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(123,47,255,0.12) 0%,transparent 60%)}}h1{{font-size:2.2rem;background:linear-gradient(135deg,#00d4ff,#7b2fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.sub{{color:#888}}.stats{{display:flex;justify-content:center;gap:28px;margin-top:20px}}.st{{text-align:center}}.sn{{font-size:1.6rem;font-weight:700;color:#00d4ff}}.sl{{font-size:.7rem;color:#666;text-transform:uppercase;letter-spacing:1px}}.filters{{display:flex;justify-content:center;gap:12px;margin-top:20px}}.filters input,.filters select{{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);color:#e0e0e2;padding:8px 14px;border-radius:8px;font-size:.9rem}}.filters input{{width:220px}}.container{{max-width:1100px;margin:0 auto;padding:28px 20px}}.cat{{margin-bottom:36px}}.cat h2{{font-size:1.2rem;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,0.06)}}.cat h2 span{{color:#555;font-size:.8rem;font-weight:400}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:18px;cursor:pointer;transition:all .2s}}.card:hover{{background:rgba(255,255,255,0.07);border-color:rgba(123,47,255,0.3);transform:translateY(-2px)}}.cc{{display:inline-block;padding:2px 7px;border-radius:8px;font-size:.6rem;font-weight:600;text-transform:uppercase;background:rgba(0,212,255,0.1);color:#00d4ff;margin-bottom:6px}}.ct{{font-size:.95rem;font-weight:600;margin-bottom:4px}}.cd{{color:#777;font-size:.8rem;line-height:1.4;margin-bottom:6px}}.cf{{color:#555;font-size:.7rem}}.ft{{text-align:center;padding:36px 20px;color:#444;font-size:.8rem;border-top:1px solid rgba(255,255,255,0.04);margin-top:36px}}</style></head><body><div class="hd"><h1>🛍 Skills Marketplace</h1><p class="sub">Browse and install open-source skills from Poke Labs</p><div class="stats"><div class="st"><div class="sn">{len(ALL)}</div><div class="sl">Skills</div></div><div class="st"><div class="sn">{len(cats)}</div><div class="sl">Categories</div></div><div class="st"><div class="sn">MIT</div><div class="sl">License</div></div></div><form class="filters" method="get"><input type="text" name="q" placeholder="Search skills..." value="{h.escape(sq)}"><select name="cat" onchange="this.form.submit()"><option value="">All Categories</option>{opts}</select></form></div><div class="container">{ch}</div><div class="ft">Poke Labs © 2026 · MIT Licensed</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body.encode())
    def json(self,d,code=200):
        body=json.dumps(d).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__=="__main__":
    import urllib.parse
    s=http.server.HTTPServer(("0.0.0.0",PORT),H)
    print(f"Skills Marketplace v2.0 on :{PORT} | {len(ALL)} skills");s.serve_forever()
