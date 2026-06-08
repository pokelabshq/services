#!/usr/bin/env python3
"""Pocket v1 — Personal knowledge base API for AI agents.
Store, search, retrieve notes with tagging and full-text search.
Zero deps, stdlib only. MIT License."""
import http.server, json, os, time, urllib.parse, re, hashlib, threading

PORT = 8767
DB_DIR = "/home/alx/services/pocket/data"
lock = threading.Lock()
os.makedirs(DB_DIR, exist_ok=True)

def _now(): return int(time.time())
def _db_path(ns): return os.path.join(DB_DIR, f"{ns}.json")
def _load(ns):
    p = _db_path(ns)
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return {"ns": ns, "items": [], "updated": _now()}
def _save(ns, data):
    data["updated"] = _now()
    with open(_db_path(ns), "w") as f: json.dump(data, f, indent=2)
def _search(items, query, tags=None, limit=20):
    q = query.lower() if query else ""
    results = []
    for item in items:
        if tags and not all(t in item.get("tags",[]) for t in tags): continue
        if q:
            hay = f"{item.get('title','')} {item.get('body','')} {' '.join(item.get('tags',[]))}".lower()
            if q in hay:
                score = hay.count(q) * 10 + (100 if q in item.get("title","").lower() else 0)
                results.append((score, item))
        else:
            results.append((0, item))
    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results[:limit]]

PAGE = """<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Pocket — Knowledge Base API</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}
.h{background:linear-gradient(135deg,#0a0a1a,#1a1a3e);padding:50px 20px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.04)}
h1{font-size:2.4rem;color:#00ffaa;margin-bottom:6px}
.sub{color:#666;font-size:.85rem}
.container{max-width:800px;margin:0 auto;padding:24px}
.add{display:flex;flex-direction:column;gap:10px;margin-bottom:20px}
.add input,.add textarea{padding:10px 14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;color:#e0e0e2;font-size:.85rem;outline:none;font-family:inherit}
.add input:focus,.add textarea:focus{border-color:#00ffaa}
.add textarea{min-height:100px;resize:vertical}
.add .row{display:flex;gap:10px}
.add .row input{flex:1}
.btn{padding:10px 20px;border:none;border-radius:10px;cursor:pointer;font-weight:700;font-size:.85rem;background:#00ffaa;color:#0a0a1a;align-self:flex-start}
.sb{display:flex;gap:8px;margin-bottom:20px}
.sb input{flex:1;padding:10px 14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;color:#e0e0e2;font-size:.85rem;outline:none}
.sb input:focus{border-color:#00ffaa}
.item{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;margin:8px 0}
.item h3{color:#e0e0e2;font-size:.95rem;margin-bottom:4px}
.item .body{color:#888;font-size:.8rem;margin-bottom:8px;white-space:pre-wrap;overflow-wrap:break-word}
.item .tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{padding:2px 8px;border-radius:6px;font-size:.6rem;background:rgba(0,255,170,0.1);color:#00ffaa}
.item .meta{color:#444;font-size:.65rem;display:flex;justify-content:space-between;margin-top:8px;align-items:center}
.del{background:none;border:1px solid #ff6b6a;color:#ff6b6a;padding:2px 8px;border-radius:6px;cursor:pointer;font-size:.65rem}
.empty{text-align:center;padding:60px;color:#444}
.footer{text-align:center;padding:40px;color:#444;font-size:.75rem}
</style></head><body>
<div class="h"><h1>🗄️ Pocket</h1><p class="sub">Personal knowledge base API for AI agents</p></div>
<div class="container">
<div class="add">
  <input id="title" placeholder="Note title...">
  <textarea id="body" placeholder="Write anything — ideas, code snippets, links, context..."></textarea>
  <div class="row"><input id="tags" placeholder="tags (comma separated)"><button class="btn" onclick="addNote()">💾 Save Note</button></div>
</div>
<div class="sb">
  <input id="q" placeholder="Search notes..." oninput="doSearch()">
  <input id="ft" placeholder="Filter by tag..." oninput="doSearch()">
  <button class="btn" onclick="doSearch()" style="padding:10px 16px;font-size:.75rem">🔍 Search</button>
</div>
<div id="items"><div class="empty">Loading...</div></div>
</div>
<div class="footer">Pocket v1 &middot; Poke Labs &middot; MIT &middot; <a href="/api/health" style="color:#00ffaa">Health</a></div>
<script>
const NS='default';
async function load(){
  const d=await(await fetch('/api/notes?ns='+NS)).json();
  render(d.results||[]);
}
function render(items){
  const c=document.getElementById('items');
  if(!items.length){c.innerHTML='<div class="empty">No notes yet. Save your first one above.</div>';return}
  c.innerHTML=items.map(i=>`
    <div class="item">
      <h3>${i.title||'(untitled)'}</h3>
      <div class="body">${(i.body||'').replace(/</g,'&lt;').slice(0,500)}</div>
      <div class="tags">${(i.tags||[]).map(t=>'<span class="tag">'+t+'</span>').join('')}</div>
      <div class="meta">
        <span>${new Date(i.created*1000).toLocaleDateString()}</span>
        <button class="del" onclick="del('${i.id}')">🗑 Delete</button>
      </div>
    </div>
  `).join('');
}
async function addNote(){
  const title=document.getElementById('title').value.trim();
  const body=document.getElementById('body').value.trim();
  const tags=document.getElementById('tags').value.split(',').map(t=>t.trim()).filter(Boolean);
  if(!title&&!body){alert('Need title or body');return}
  await fetch('/api/notes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ns:NS,title,body,tags})});
  document.getElementById('title').value='';
  document.getElementById('body').value='';
  document.getElementById('tags').value='';
  load();doSearch();
}
async function del(id){
  if(!confirm('Delete this note?'))return;
  await fetch('/api/notes/'+id+'?ns='+NS,{method:'DELETE'});
  load();doSearch();
}
async function doSearch(){
  const q=document.getElementById('q').value.trim();
  const ft=document.getElementById('ft').value.trim();
  let url='/api/notes?ns='+NS;
  if(q) url+='&q='+encodeURIComponent(q);
  if(ft) url+='&tags='+encodeURIComponent(ft);
  render((await(await fetch(url)).json()).results||[]);
}
load();
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p=urllib.parse.urlparse(self.path)
        qs=urllib.parse.parse_qs(p.query)
        ns=qs.get("ns",["default"])[0]
        if p.path=="/": self._html(PAGE)
        elif p.path=="/api/health": self._json({"ok":True,"v":1,"port":PORT})
        elif p.path.startswith("/api/notes/"):
            nid=p.path.split("/api/notes/")[1].split("?")[0]
            item=next((i for i in _load(ns)["items"] if i["id"]==nid),None)
            if item: self._json(item)
            else: self._json({"error":"not found"},404)
        elif p.path=="/api/notes":
            db=_load(ns)
            q=qs.get("q",[""])[0]
            tags=[t.strip() for t in qs.get("tags",[""])[0].split(",") if t.strip()] or None
            self._json({"results":_search(db["items"],q,tags),"total":len(db["items"]),"ns":ns})
        else: self._json({"error":"not found"},404)

    def do_POST(self):
        p=urllib.parse.urlparse(self.path)
        qs=urllib.parse.parse_qs(p.query)
        ns=qs.get("ns",["default"])[0]
        if p.path=="/api/notes":
            body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            item={"id":hashlib.sha256(f"{_now()}{body.get('title','')}".encode()).hexdigest()[:16],
                  "title":body.get("title",""),"body":body.get("body",""),
                  "tags":[t.strip() for t in body.get("tags",[]) if t.strip()],"created":_now()}
            with lock:
                db=_load(ns); db["items"].append(item); _save(ns,db)
            self._json({"ok":True,"id":item["id"]})
        else: self._json({"error":"not found"},404)

    def do_DELETE(self):
        p=urllib.parse.urlparse(self.path)
        qs=urllib.parse.parse_qs(p.query)
        ns=qs.get("ns",["default"])[0]
        nid=p.path.split("/api/notes/")[1].split("?")[0]
        with lock:
            db=_load(ns); db["items"]=[i for i in db["items"] if i.get("id")!=nid]; _save(ns,db)
        self._json({"ok":True})

    def _html(self,h,code=200):
        b=h.encode("utf-8");self.send_response(code)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def _json(self,d,code=200):
        b=json.dumps(d,default=str).encode();self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def log_message(self,*a): pass

if __name__=="__main__":
    s=http.server.HTTPServer(("0.0.0.0",PORT),Handler)
    print(f"Pocket v1 on :{PORT}");s.serve_forever()
