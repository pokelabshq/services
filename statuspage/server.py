#!/usr/bin/env python3
"""Poke Labs Status Page — live dashboard."""
import json, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8769))
HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")

def load_html():
    try:
        with open(HTML_FILE) as f:
            return f.read()
    except:
        return "<h1>Poke Labs Status</h1><p>Loading...</p>"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip("/") in ("/api/health", "/health"):
            body = json.dumps({"ok": True, "v": 1, "service": "statuspage"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        body = load_html().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"Status Page on :{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
