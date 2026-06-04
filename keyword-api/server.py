#!/usr/bin/env python3
"""Keyword Extraction API — extracts keywords/phrases from text.
Free tier (3/IP/day) + x402 USDC payments on Base."""
import http.server, json, os, re, math
from collections import Counter

PORT = 8766
FREE_LIMIT = 3
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage.json")

try:
    usage = json.load(open(USAGE_FILE))
except:
    usage = {}

def save():
    json.dump(usage, open(USAGE_FILE, "w"))

STOP_WORDS = {
    'a','an','the','and','or','but','in','on','at','to','for','of','with',
    'by','from','is','it','this','that','are','was','were','be','been',
    'being','have','has','had','do','does','did','will','would','could',
    'should','may','might','shall','can','need','dare','ought','used',
    'not','no','nor','as','if','then','than','too','very','just','about',
    'above','after','again','all','also','am','any','because','before',
    'between','both','each','few','further','get','got','he','her','here',
    'him','his','how','i','into','its','let','me','more','most','my',
    'myself','now','only','other','our','out','over','own','same','she',
    'so','some','such','their','them','there','these','they','those',
    'through','under','up','us','we','what','when','where','which','while',
    'who','whom','why','you','your','yours','yourself','itself','himself',
    'herself','themselves','ourselves','yourself','myself',
}

def tokenize(text):
    words = re.findall(r'[a-z][a-z\']{1,}', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def extract_keywords(text, top_n=10):
    words = tokenize(text)
    if not words:
        return []
    unigram_counts = Counter(words)
    total = len(words)
    unigram_scores = {w: c/total for w, c in unigram_counts.items()}
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    bigram_counts = Counter(bigrams)
    bigram_total = len(bigrams) if bigrams else 1
    bigram_scores = {b: c/bigram_total * 1.5 for b, c in bigram_counts.items() if c >= 2}
    all_scores = {}
    for w, s in unigram_scores.items():
        all_scores[w] = s
    for b, s in bigram_scores.items():
        all_scores[b] = s
    sorted_kw = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
    return [{"keyword": k, "score": round(s, 4)} for k, s in sorted_kw[:top_n]]

def extract_entities(text):
    entities = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
    counts = Counter(entities)
    return [{"entity": e, "count": c} for e, c in counts.most_common(10)]

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/keywords":
            return self._handle_keywords()
        if self.path == "/api/entities":
            return self._handle_entities()
        if self.path == "/api/analyze":
            return self._handle_analyze()
        return self.js(404, {"error": "not found"})

    def _check_limit(self):
        ip = self.client_address[0]
        if usage.get(ip, 0) >= FREE_LIMIT:
            self.js(402, {
                "error": "limit exceeded",
                "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF",
                "used": usage.get(ip, 0),
                "limit": FREE_LIMIT
            })
            return True
        return False

    def _get_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length))
        except:
            return None

    def _handle_keywords(self):
        if self._check_limit(): return
        body = self._get_body()
        if not body: return self.js(400, {"error": "bad json"})
        text = body.get("text", "").strip()
        if not text: return self.js(400, {"error": "need text"})
        top_n = min(int(body.get("top_n", 10)), 50)
        ip = self.client_address[0]
        usage[ip] = usage.get(ip, 0) + 1; save()
        keywords = extract_keywords(text, top_n)
        self.js(200, {"ok": True, "keywords": keywords, "total_words": len(text.split())})

    def _handle_entities(self):
        if self._check_limit(): return
        body = self._get_body()
        if not body: return self.js(400, {"error": "bad json"})
        text = body.get("text", "").strip()
        if not text: return self.js(400, {"error": "need text"})
        ip = self.client_address[0]
        usage[ip] = usage.get(ip, 0) + 1; save()
        entities = extract_entities(text)
        self.js(200, {"ok": True, "entities": entities})

    def _handle_analyze(self):
        if self._check_limit(): return
        body = self._get_body()
        if not body: return self.js(400, {"error": "bad json"})
        text = body.get("text", "").strip()
        if not text: return self.js(400, {"error": "need text"})
        top_n = min(int(body.get("top_n", 10)), 50)
        ip = self.client_address[0]
        usage[ip] = usage.get(ip, 0) + 1; save()
        keywords = extract_keywords(text, top_n)
        entities = extract_entities(text)
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        self.js(200, {
            "ok": True,
            "keywords": keywords,
            "entities": entities,
            "stats": {
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "char_count": len(text),
                "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 1),
            }
        })

    def do_GET(self):
        if self.path == "/api/health":
            return self.js(200, {"ok": True, "v": 1, "free_limit": FREE_LIMIT})
        if self.path == "/api/usage":
            return self.js(200, {"used": usage.get(self.client_address[0], 0), "limit": FREE_LIMIT})
        if self.path == "/" or self.path == "/index.html":
            try:
                with open(os.path.join(PUBLIC_DIR, "index.html"), "rb") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html)
            except:
                self.js(500, {"error": "landing page missing"})
            return
        self.js(404, {"error": "not found"})

    def js(self, code, data):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"Keyword API running on port {PORT}")
    server.serve_forever()
