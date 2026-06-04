#!/usr/bin/env python3
"""Poke Labs Landing Page — pokelabs.org"""
import os, json, http.server, urllib.request
PORT = int(os.environ.get("PORT", 8760))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = self.path.split("?")[0].rstrip("/")
        if p == "/api/health":
            d = json.dumps({"ok":True,"v":1,"service":"pokelabs-landing"}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(d); return
        if p in ("","/"): p = "/index.html"
        fp = os.path.join(PUBLIC_DIR, p.lstrip("/"))
        if os.path.isfile(fp):
            ct = "text/html"
            if fp.endswith(".css"): ct="text/css"
            elif fp.endswith(".js"): ct="application/javascript"
            elif fp.endswith(".png"): ct="image/png"
            elif fp.endswith(".svg"): ct="image/svg+xml"
            with open(fp,"rb") as f: data=f.read()
            self.send_response(200); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
        else:
            self.send_response(404); self.end_headers()
    def log_message(self,*a): pass

if __name__ == "__main__":
    print(f"Poke Labs Landing on :{PORT}", flush=True)
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
