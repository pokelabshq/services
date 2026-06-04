#!/usr/bin/env python3
"""Hash Generator Service — SHA256, SHA1, MD5, SHA512. Port: 8779"""
import http.server, json, urllib.parse, os, hashlib

PORT = int(os.environ.get("PORT", 8779))
FREE_LIMIT = 5
ip_usage = {}

ALGORITHMS = {
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
    "sha384": hashlib.sha384,
    "blake2b": hashlib.blake2b,
}

def hash_text(text, algo="sha256"):
    h = ALGORITHMS.get(algo, hashlib.sha256)(text.encode("utf-8"))
    return h.hexdigest()

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self._respond(200, {"ok": True, "service": "hash-gen", "v": 1, "algorithms": list(ALGORITHMS.keys())})
        elif p.path == "/api/usage":
            self._respond(200, {"used": ip_usage.get(self.client_address[0], 0), "limit": FREE_LIMIT})
        elif p.path == "/api/hash":
            params = urllib.parse.parse_qs(p.query)
            text = params.get("text", [""])[0]
            algo = params.get("algo", ["sha256"])[0]
            if not text:
                self._respond(400, {"error": "missing 'text' query param"}); return
            if algo not in ALGORITHMS:
                self._respond(400, {"error": f"unsupported algorithm. Use: {list(ALGORITHMS.keys())}"}); return
            ip = self.client_address[0]
            if ip_usage.get(ip, 0) >= FREE_LIMIT:
                self._respond(402, {"error": "free limit exceeded", "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF", "chain": "base"}); return
            ip_usage[ip] = ip_usage.get(ip, 0) + 1
            self._respond(200, {"algorithm": algo, "hash": hash_text(text, algo), "input_length": len(text)})
        else:
            self._respond(404, {"error": "not found"})
    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        if p.path != "/api/hash":
            self._respond(404, {"error": "not found"}); return
        ip = self.client_address[0]
        if ip_usage.get(ip, 0) >= FREE_LIMIT:
            self._respond(402, {"error": "free limit exceeded", "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF", "chain": "base"}); return
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        text = data.get("text", "")
        algo = data.get("algo", "sha256")
        if not text:
            self._respond(400, {"error": "missing 'text' field"}); return
        if algo not in ALGORITHMS:
            self._respond(400, {"error": f"unsupported algorithm. Use: {list(ALGORITHMS.keys())}"}); return
        ip_usage[ip] = ip_usage.get(ip, 0) + 1
        if data.get("all", False):
            result = {a: hash_text(text, a) for a in ALGORITHMS}
            self._respond(200, {"algorithm": "all", "hashes": result, "input_length": len(text)})
        else:
            self._respond(200, {"algorithm": algo, "hash": hash_text(text, algo), "input_length": len(text)})
    def _respond(self, s, b):
        self.send_response(s); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
        self.wfile.write(json.dumps(b).encode())

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Hash Generator on port {PORT}")
    s.serve_forever()
