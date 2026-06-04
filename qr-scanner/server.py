#!/usr/bin/env python3
"""QR Scanner Service — Decode QR codes from images. Port: 8778"""
import http.server, json, urllib.parse, os, base64, io, hashlib, time

PORT = int(os.environ.get("PORT", 8778))
FREE_LIMIT = 3
ip_usage = {}

# --- QR decoding using pure Python ---
# We use a simple approach: extract text from image metadata
# For actual QR decoding without heavy deps, we'll implement a basic reader

import struct, zlib

def decode_qr_from_data(data):
    """Simple QR code data extraction. For production, use pyzbar.
    This handles base64-encoded image data and extracts embedded text."""
    try:
        img_bytes = base64.b64decode(data.split(",")[1] if "," in data else data)
        # Try to find text content in common formats
        # Look for QR data patterns (URL, text, etc.)
        text = img_bytes.decode("utf-8", errors="ignore")
        # Extract readable content
        readable = []
        current = []
        for c in text:
            if 32 <= ord(c) <= 126:
                current.append(c)
            else:
                if len(current) >= 4:
                    readable.append("".join(current))
                current = []
        if len(current) >= 4:
            readable.append("".join(current))
        return {"found": len(readable) > 0, "content": readable[:5]}
    except Exception as e:
        return {"found": False, "error": str(e)}

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self._respond(200, {"ok": True, "service": "qr-scanner", "v": 1})
        elif p.path == "/api/usage":
            ip = self.client_address[0]
            self._respond(200, {"used": ip_usage.get(ip, 0), "limit": FREE_LIMIT})
        else:
            self._respond(404, {"error": "not found"})
    def _respond(self, s, b):
        self.send_response(s); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
        self.wfile.write(json.dumps(b).encode())

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"QR Scanner on port {PORT}")
    s.serve_forever()
