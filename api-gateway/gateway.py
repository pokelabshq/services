#!/usr/bin/env python3
"""Poke Labs API Gateway v1 — Single entry point for all services."""
import http.server, json, urllib.request, urllib.error, os, socket

PORT = 8760
ROUTES = {
    "/preview":  ("localhost", 8765),
    "/bot":      ("localhost", 8770),
    "/site":     ("localhost", 8766),
    "/telegram": ("localhost", 8777),
    "/market":   ("localhost", 8780),
    "/dash":     ("localhost", 8799),
    "/relay":    ("localhost", 8775),
    "/uptime":   ("localhost", 8776),
    "/repo":     ("localhost", 8778),
    "/barcode":  ("localhost", 8782),
}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            rows = "".join(f"<tr><td>{k}</td><td>{k.strip('/').title()}</td><td>{v[1]}</td></tr>" for k,v in ROUTES.items())
            html = f"<!DOCTYPE html><html><head><title>Poke Labs API Gateway</title></head><body style='font-family:system-ui;background:#0a0a0f;color:#e0e0e0;padding:2rem'><h1 style='color:#00d4ff'>🐾 Poke Labs API Gateway</h1><p>Port {PORT} — Single entry point for all services.</p><table><tr><th>Path</th><th>Service</th><th>Port</th></tr>{rows}</table><p>Health: GET /health</p></body></html>"
            self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(html.encode()); return
        if path in ("/health","/api/health"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps({"ok":True,"v":1}).encode()); return
        for prefix,(host,port) in ROUTES.items():
            if path.startswith(prefix):
                url = f"http://{host}:{port}{path[len(prefix):]}"
                try:
                    req = urllib.request.Request(url, headers={"User-Agent":"poke-gateway/1"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        body = r.read(); self.send_response(r.status)
                        ct = r.headers.get("Content-Type")
                        if ct: self.send_header("Content-Type", ct)
                        self.end_headers(); self.wfile.write(body)
                except Exception as e:
                    self.send_response(502); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps({"error":str(e)}).encode())
                return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        path = self.path.split("?")[0]
        cl = int(self.headers.get("Content-Length",0))
        body = self.rfile.read(cl) if cl > 0 else b""
        for prefix,(host,port) in ROUTES.items():
            if path.startswith(prefix):
                url = f"http://{host}:{port}{path[len(prefix):]}"
                try:
                    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type":self.headers.get("Content-Type","application/json"),"User-Agent":"poke-gateway/1"})
                    with urllib.request.urlopen(req, timeout=30) as r:
                        rb = r.read(); self.send_response(r.status)
                        ct = r.headers.get("Content-Type")
                        if ct: self.send_header("Content-Type", ct)
                        self.end_headers(); self.wfile.write(rb)
                except Exception as e:
                    self.send_response(502); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps({"error":str(e)}).encode())
                return
        self.send_response(404); self.end_headers()
    def log_message(self, *a): pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"API Gateway v1 on port {PORT}")
    server.serve_forever()
