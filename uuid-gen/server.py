#!/usr/bin/env python3
"""UUID Generator Service — Generate UUIDs v1, v4, v7. Port: 8780"""
import http.server, json, urllib.parse, os, uuid, time

PORT = int(os.environ.get("PORT", 8780))
FREE_LIMIT = 10
ip_usage = {}

def generate_uuid_v7():
    ts_ms = int(time.time() * 1000)
    ts_bytes = ts_ms.to_bytes(6, "big")
    rand_bytes = os.urandom(10)
    uuid_bytes = bytearray(ts_bytes + rand_bytes)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(uuid_bytes)))

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self._respond(200, {"ok": True, "service": "uuid-gen", "v": 1})
        elif p.path == "/api/usage":
            self._respond(200, {"used": ip_usage.get(self.client_address[0], 0), "limit": FREE_LIMIT})
        elif p.path == "/api/generate":
            params = urllib.parse.parse_qs(p.query)
            count = min(int(params.get("count", [1])[0]), 100)
            version = params.get("version", ["4"])[0]
            ip = self.client_address[0]
            if ip_usage.get(ip, 0) >= FREE_LIMIT:
                self._respond(402, {"error": "free limit exceeded", "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF", "chain": "base"}); return
            ip_usage[ip] = ip_usage.get(ip, 0) + 1
            if version == "1":
                uuids = [str(uuid.uuid1()) for _ in range(count)]
            elif version == "7":
                uuids = [generate_uuid_v7() for _ in range(count)]
            else:
                uuids = [str(uuid.uuid4()) for _ in range(count)]
            self._respond(200, {"version": version, "count": len(uuids), "uuids": uuids})
        else:
            self._respond(404, {"error": "not found"})
    def _respond(self, s, b):
        self.send_response(s); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
        self.wfile.write(json.dumps(b).encode())

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"UUID Generator on port {PORT}")
    s.serve_forever()
