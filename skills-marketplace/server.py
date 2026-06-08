#!/usr/bin/env python3
"""Skills Marketplace v2.0 — Browse, search, install skills. Port: 8781. Zero deps."""
import http.server, json, os, html as h, urllib.parse, time

PORT = 8781
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
SERVICES_DIR = "/home/alx/services"
INSTALL_BASE = "/home/alx/.pokelabs/skills"
_installs = 0
_start = time.time()

def scan():
    skills = []
    try:
        for name in sorted(os.listdir(SERVICES_DIR)):
            p = os.path.join(SERVICES_DIR, name)
            if not os.path.isdir(p): continue
            files = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p,f))]
            desc = ""
            for md in ["SKILL.md","README.md"]:
                mp = os.path.join(p, md)
                if os.path.exists(mp):
                    with open(mp) as f:
                        for line in f:
                            l = line.strip()
                            if l and not l.startswith("#") and not l.startswith("```"):
                                desc = l[:200]; break
                    if desc: break
            etxt = (desc+" "+name).lower()
            if any(k in etxt for k in ["github","pr","issue","webhook","repo","pull","git","action"]): cat="github"
            elif any(k in etxt for k in ["api","http","endpoint","rest","gateway"]): cat="api"
            elif any(k in etxt for k in ["web","site","landing","page","dashboard","frontend","ui"]): cat="web"
            elif any(k in etxt for k in ["bot","telegram","discord","social","twitter","message"]): cat="social"
            elif any(k in etxt for k in ["monitor","health","uptime","status","check","watchdog"]): cat="monitoring"
            elif any(k in etxt for k in ["data","analytics","stats","metric","chart","report"]): cat="data"
            elif any(k in etxt for k in ["ai","model","inference","llm","chat","ml"]): cat="ai"
            elif any(k in etxt for k in ["pay","wallet","usdc","x402","crypto","price","billing"]): cat="finance"
            elif any(k in etxt for k in ["gen","create","build","template","scaffold"]): cat="generator"
            elif any(k in etxt for k in ["preview","fetch","scrape","extract","metadata"]): cat="preview"
            else: cat="tools"
            skills.append({"id":name,"name":name.replace("-"," ").replace("_"," ").title(),"desc":desc or f"Poke Labs: {name}","cat":cat,"files":len(files),"top_files":files[:5],"has_md":"SKILL.md" in files})
    except Exception as e:
        skills.append({"id":"error","name":"Error","desc":str(e),"cat":"error","files":0,"top_files":[],"has_md":False})
    return skills

ALL_SKILLS = scan()
CATS = {}
for s in ALL_SKILLS: CATS[s["cat"]] = CATS.get(s["cat"],0)+1

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global _installs
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/health":
            self.json({"ok":True,"v":2,"port":PORT,"uptime_s":int(time.time()-_start),"skills":len(ALL_SKILLS),"installs":_installs,"wallet":WALLET})
        elif path == "/api/skills":
            r = list(ALL_SKILLS)
            cat = qs.get("cat",[None])[0]
            q = qs.get("q",[""])[0].lower()
            if cat and cat != "all": r = [s for s in r if s["cat"]==cat]
            if q: r = [s for s in r if q in s["name"].lower() or q in s["desc"].lower() or q in s["id"].lower()]
            self.json({"ok":True,"skills":r,"total":len(r),"all_total":len(ALL_SKILLS),"categories":CATS})
        elif path == "/api/stats":
            total_files = sum(s["files"] for s in ALL_SKILLS)
            with_md = sum(1 for s in ALL_SKILLS if s["has_md"])
            self.json({"ok":True,"skills":len(ALL_SKILLS),"categories":len(CATS),"total_files":total_files,"with_docs":with_md,"installs":_installs,"uptime_s":int(time.time()-_start)})
        elif path.startswith("/api/skill/"):
            sid = path[10:]
            skill = next((s for s in ALL_SKILLS if s["id"]==sid), None)
            if not skill: self.json({"error":"Not found"},404); return
            rp = os.path.join(SERVICES_DIR, sid, "SKILL.md")
            if os.path.exists(rp):
                skill = dict(skill)
                with open(rp) as f: skill["readme"] = f.read()
            self.json({"ok":True,"skill":skill})
        elif path == "/api/install":
            sid = qs.get("id",[""])[0]
            if not sid: self.json({"error":"Missing id"},400); return
            if not any(s["id"]==sid for s in ALL_SKILLS): self.json({"error":"Unknown"},404); return
            dest = os.path.join(INSTALL_BASE, sid)
            os.makedirs(dest, exist_ok=True)
            src = os.path.join(SERVICES_DIR, sid)
            copied = []
            for fname in ["SKILL.md","README.md"]:
                sp = os.path.join(src, fname)
                if os.path.exists(sp):
                    with open(sp) as sf: c = sf.read()
                    with open(os.path.join(dest,fname),"w") as df: df.write(c)
                    copied.append(fname)
            _installs += 1
            self.json({"ok":True,"installed":sid,"dest":dest,"files":copied,"total_installs":_installs})
        elif path == "/":
            self.home(qs)
        else:
            self.json({"error":"Not found","endpoints":["/","/api/health","/api/skills","/api/skills?cat=github","/api/skills?q=webhook","/api/skill/<id>","/api/install?id=<id>"]},404)

    def home(self, qs):
        cf = qs.get("cat",[""])[0]
        sq = qs.get("q",[""])[0].lower()
        cbs = "".join(f'<a href="?cat={c}" class="cb {"active" if c==cf else ""}">{c.title()} <span>{n}</span></a>' for c,n in sorted(CATS.items(),key=lambda x:-x[1]))
        filt = [s for s in ALL_SKILLS if (not cf or s["cat"]==cf) and (not sq or sq in s["name"].lower() or sq in s["desc"].lower() or sq in s["id"].lower())]
        cards = "".join(f'<div class="card" onclick="location.href=\'/api/skill/{s["id"]}?format=html\'"><div class="ct"><span class="badge">{s["cat"]}</span><span class="fc">{s["files"]} files</span></div><div class="cn">{h.escape(s["name"])}</div><div class="cd">{h.escape(s["desc"][:120])}</div></div>' for s in filt) or '<div class="empty">No matches</div>'
        b = f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Poke Labs — Skills Marketplace v2</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6;min-height:100vh}}.hd{{padding:50px 20px 30px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(123,47,255,0.12) 0%,transparent 60%)}}h1{{font-size:2.2rem;background:linear-gradient(135deg,#00d4ff,#7b2fff,#ff6b9d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px}}.sub{{color:#888;font-size:.95rem}}.badges{{display:flex;justify-content:center;gap:10px;margin-top:16px;flex-wrap:wrap}}.bg{{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);padding:5px 12px;border-radius:16px;font-size:.75rem;color:#aaa}}.bg em{{color:#00d4ff;font-style:normal;font-weight:700}}.srch{{max-width:1100px;margin:0 auto;padding:20px;display:flex;justify-content:center}}.srch input{{width:100%;max-width:400px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);color:#e0e0e2;padding:10px 16px;border-radius:10px;font-size:.9rem;outline:none}}.srch input:focus{{border-color:rgba(123,47,255,0.5)}}.filters{{max-width:1100px;margin:0 auto;padding:0 20px 20px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center}}.cb{{padding:5px 12px;border-radius:8px;font-size:.75rem;color:#888;text-decoration:none;border:1px solid rgba(255,255,255,0.08)}}.cb.active{{background:rgba(0,212,255,0.1);color:#00d4ff;border-color:rgba(0,212,255,0.3)}}.cb span{{color:#555;font-size:.65rem}}.container{{max-width:1100px;margin:0 auto;padding:20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}.card{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:18px;cursor:pointer;transition:all .2s}}.card:hover{{background:rgba(255,255,255,0.06);border-color:rgba(123,47,255,0.3);transform:translateY(-2px);box-shadow:0 6px 24px rgba(123,47,255,0.08)}}.ct{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}.badge{{padding:2px 7px;border-radius:5px;font-size:.55rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;background:rgba(0,212,255,0.1);color:#00d4ff}}.fc{{color:#555;font-size:.65rem}}.cn{{font-size:.95rem;font-weight:600;margin-bottom:4px}}.cd{{color:#777;font-size:.8rem;line-height:1.4}}.empty{{text-align:center;color:#555;padding:40px}}.ft{{text-align:center;padding:30px;color:#444;font-size:.75rem;border-top:1px solid rgba(255,255,255,0.04);margin-top:30px}}</style></head><body><div class="hd"><h1>🛍 Skills Marketplace</h1><p class="sub">Browse, search, and install open-source microskills from Poke Labs</p><div class="badges"><span class="bg"><em>{len(ALL_SKILLS)}</em> Skills</span><span class="bg"><em>{len(CATS)}</em> Categories</span><span class="bg">MIT Licensed</span><span class="bg">Zero Deps</span></div></div><div class="srch"><form method="get"><input type="text" name="q" placeholder="Search skills..." value="{h.escape(sq)}"></form></div><div class="filters"><a href="/" class="cb {"active" if not cf else ""}">All <span>{len(ALL_SKILLS)}</span></a>{cbs}</div><div class="container"><div class="grid">{cards}</div></div><div class="ft">🐾 Poke Labs © 2026 · MIT · Wallet: 0xca3d...6beF</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b.encode())

    def json(self, d, code=200):
        body = json.dumps(d).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__=="__main__":
    s = http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Skills Marketplace v2.0 on :{PORT} | {len(ALL_SKILLS)} skills");s.serve_forever()
