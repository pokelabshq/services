#!/usr/bin/env python3
"""Timestamp Converter — Unix to human-readable, multiple formats. Port: 8781"""
import http.server, json, urllib.parse, os, time
from datetime import datetime, timezone

PORT = int(os.environ.get("PORT", 8781))
FREE_LIMIT = 5
ip_usage = {}

def convert_timestamp(ts=None):
    now = time.time()
    if ts is None:
        ts = now
    else:
        ts = float(ts)
        if ts > 1e12:
            ts = ts / 1000
    dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
    return {
        "unix": int(ts),
        "unix_ms": int(ts * 1000),
        "utc": dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "iso8601": dt_utc.isoformat(),
        "rfc2822": dt_utc.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "relative": _relative_time(ts, now),
    }

def _relative_time(ts, now):
    diff = now - ts
    if abs(diff) < 60: return "just now" if diff >= 0 else "in a few seconds"
    if abs(diff) < 3600: m = int(diff / 60); return f"{m} min ago" if diff >= 0 else f"in {abs(m)} min"
    if abs(diff) < 86400: h = int(diff / 3600); return f"{h} hr ago" if diff >= 0 else f"in {abs(h)} hr"
    d = int(diff / 86400); return f"{d} days ago" if diff >= 0 else f"in {abs(d)} days"

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): pass
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self._respond(200, {"ok": True, "service": "timestamp-conv", "v": 1})
        elif p.path == "/api/usage":
            self._respond(200, {"used": ip_usage.get(self.client_address[0], 0), "limit": FREE_LIMIT})
        elif p.path == "/api/now":
            ip = self.client_address[0]
            if ip_usage.get(ip, 0) >= FREE_LIMIT:
                self._respond(402, {"error": "free limit exceeded", "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF", "chain": "base"}); return
            ip_usage[ip] = ip_usage.get(ip, 0) + 1
            self._respond(200, convert_timestamp())
        elif p.path == "/api/convert":
            params = urllib.parse.parse_qs(p.query)
            ts = params.get("ts", [None])[0]
            ip = self.client_address[0]
            if ip_usage.get(ip, 0) >= FREE_LIMIT:
                self._respond(402, {"error": "free limit exceeded", "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF", "chain": "base"}); return
            ip_usage[ip] = ip_usage.get(ip, 0) + 1
            try:
                result = convert_timestamp(float(ts) if ts else None)
                self._respond(200, result)
            except (ValueError, OSError) as e:
                self._respond(400, {"error": f"invalid timestamp: {e}"})
        else:
            self._respond(404, {"error": "not found"})
    def _respond(self, s, b):
        self.send_response(s); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
        self.wfile.write(json.dumps(b).encode())

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Timestamp Converter on port {PORT}")
    s.serve_forever()
