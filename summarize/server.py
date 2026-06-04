#!/usr/bin/env python3
import http.server, json, os, re
from collections import Counter

PORT = 8767
FREE_LIMIT = 3
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage.json")

try:
    usage = json.load(open(USAGE_FILE))
except:
    usage = {}

def save():
    json.dump(usage, open(USAGE_FILE, "w"))

STOP_WORDS = {"a","an","the","and","or","but","in","on","at","to","for","of","with","by","from","is","it","this","that","are","was","were","be","been","being","have","has","had","do","does","did","will","would","could","should","may","might","shall","can","not","no","nor","as","if","then","than","too","very","just","he","she","me","my","we","us","yo","your","they","them","his","her","its","our","their","i","you","who","what","when","where","how","all","any","each","every","both","few","more","most","other","some","such","only","own","same","about","above","after","again","also","am","because","before","between","further","got","get","here","him","into","let","myself","now","off","once","over","so","these","those","through","under","up","which","while","whom"}

def tokenize(text):
    return re.findall(r"[a-z][a-z']{1,}", text.lower())

def split_sentences(text):
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if len(s.strip()) > 10]

def summarize(text, n=3):
    sents = split_sentences(text)
    if len(sents) <= n: return text
    words = tokenize(text)
    freq = Counter(w for w in words if w not in STOP_WORDS)
    mx = max(freq.values()) if freq else 1
    def score(s):
        w = tokenize(s)
        if not w: return 0
        return sum(freq.get(x,0)/mx for x in w if x not in STOP_WORDS)/len(w)
    scored = sorted([(s, score(s)) for s in sents], key=lambda x: x[1], reverse=True)
    idx = sorted([sents.index(s[0]) for s in scored[:n]])
    return " ".join(sents[i] for i in idx)

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/summarize": return self._h()
        self.js(404, {"error": "not found"})
    def _lim(self):
        ip = self.client_address[0]
        if usage.get(ip,0) >= FREE_LIMIT:
            self.js(402,{"error":"limit exceeded","wallet":"0xca3d86e4EDE205E6d72496BC2919c88b994B6beF","used":usage.get(ip,0),"limit":FREE_LIMIT})
            return True
        return False
    def _body(self):
        try: return json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        except: return None
    def _h(self):
        if self._lim(): return
        b = self._body()
        if not b: return self.js(400,{"error":"bad json"})
        text = b.get("text","").strip()
        if not text: return self.js(400,{"error":"need text"})
        n = min(int(b.get("sentences",3)),10)
        ip = self.client_address[0]
        usage[ip] = usage.get(ip,0)+1; save()
        s = summarize(text, n)
        self.js(200,{"ok":True,"summary":s,"original_length":len(text),"summary_length":len(s),"compression":round(len(s)/max(len(text),1)*100,1)})
    def do_GET(self):
        if self.path == "/api/health": return self.js(200,{"ok":True,"v":1,"free_limit":FREE_LIMIT})
        if self.path == "/api/usage": return self.js(200,{"used":usage.get(self.client_address[0],0),"limit":FREE_LIMIT})
        if self.path in ("/","index.html"):
            try:
                with open(os.path.join(PUBLIC_DIR,"index.html"),"rb") as f: h = f.read()
                self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(h)
            except: self.js(500,{"error":"no landing page"})
            return
        self.js(404,{"error":"not found"})
    def js(self, code, data):
        b = json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

if __name__ == "__main__":
    srv = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Summarize API on {PORT}"); srv.serve_forever()
