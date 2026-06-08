#!/usr/bin/env python3
"""
Poke Gateway v1.0 — Smart reverse proxy with x402 payment enforcement.
Routes requests to backend services, enforces pay-per-use via USDC.

Port: 8750
Routes:
  /preview/*    → link-preview service (8765)
  /skills/*     → skills-marketplace (8781)
  /health/*     → health-aggregator (8799)
  /id/*         → poke-id (8755)
  /dashboard/*  → poke-dashboard (8760)

Free tier: 3 requests/day per IP per route
Paid: x402 USDC micropayment (0.01 USDC per request)
"""
import http.server, http.client, json, os, socketserver, urllib.parse, datetime, re, hashlib

PORT = 8750
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
FREE_LIMIT = 3
PRICE_USDC = 0.01

ROUTES = {
    "preview": {"host": "localhost", "port": 8765, "prefix": "/api/preview"},
    "skills":  {"host": "localhost", "port": 8781, "prefix": "/api"},
    "health":  {"host": "localhost", "port": 8799, "prefix": "/api"},
    "id":      {"host": "localhost", "port": 8755, "prefix": "/api"},
    "dash":    {"host": "localhost", "port": 8760, "prefix": "/api"},
}

USAGE_FILE = os.path.join(os.path.dirname(__file__), "usage.json")

def load_usage():
    if os.path.isfile(USAGE_FILE):
        try:
            with open(USAGE_FILE) as f: return json.load(f)
        except: pass
    return {}

def save_usage(data):
    with open(USAGE_FILE, "w") as f: json.dump(data, f, indent=2)

def get_ip(self):
    return self.client_address[0]

def check_free_today(ip, route):
    usage = load_usage()
    today = datetime.date.today().isoformat()
    key = f"{ip}:{route}:{today}"
    return usage.get(key, 0) < FREE_LIMIT

def record_usage(ip, route):
    usage = load_usage()
    today = datetime.date.today().isoformat()
    key = f"{ip}:{route}:{today}"
    usage[key] = usage.get(key, 0) + 1
    # Cleanup old entries
    cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    usage = {k: v for k, v in usage.items() if k.split(":", 2)[2] >= cutoff}
    save_usage(usage)

def proxy_request(method, host, port, path, headers, body=None):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=10)
        conn.request(method, path, body=body, headers={k: v for k, v in headers.items() if k.lower() not in ("host", "connection")})
        resp = conn.getresponse()
        resp_body = resp.read()
        resp_headers = dict(resp.getheaders())
        conn.close()
        return resp.status, resp_headers, resp_body
    except Exception as e:
        return 502, {"Content-Type": "application/json"}, json.dumps({"error": f"Backend unavailable: {e}"}).encode()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Payment")
        self.end_headers()

    def _handle(self, method):
        path = urllib.parse.urlparse(self.path).path
        ip = get_ip(self)

        # Health & info endpoints (free)
        if path == "/api/health" or path == "/":
            self._send_json({"ok": True, "v": 1, "port": PORT, "routes": list(ROUTES.keys()), "wallet": WALLET, "free_limit": FREE_LIMIT, "price": PRICE_USDC})
            return

        if path == "/api/usage":
            usage = load_usage()
            today = datetime.date.today().isoformat()
            ip_usage = {k.split(":", 1)[1]: v for k, v in usage.items() if k.startswith(ip + ":") and today in k}
            self._send_json({"ip": ip, "usage": ip_usage, "free_limit": FREE_LIMIT})
            return

        # Match route
        route_name = path.strip("/").split("/")[0] if path.strip("/") else ""
        route = ROUTES.get(route_name)
        if not route:
            self._send_json({"error": f"Unknown route: {route_name}", "available": list(ROUTES.keys())}, 404)
            return

        # Check free tier
        if not check_free_today(ip, route_name):
            # Return 402 Payment Required
            self._send_json({
                "error": "Free limit exceeded",
                "message": f"FREE_LIMIT requests per day exceeded for /{route_name}/",
                "payment": {
                    "protocol": "x402",
                    "chain": "base",
                    "token": "USDC",
                    "amount": PRICE_USDC,
                    "wallet": WALLET,
                    "description": f"Poke Gateway: /{route_name}/ request"
                },
                "free_limit": FREE_LIMIT,
                "upgrade": f"Send {PRICE_USDC} USDC to {WALLET} on Base chain"
            }, 402)
            return

        # Build backend path
        backend_path = route["prefix"] + path[len("/" + route_name):]
        qs = urllib.parse.urlparse(self.path).query
        if qs:
            backend_path += "?" + qs

        # Read body for POST
        body = None
        if method == "POST":
            body_len = int(self.headers.get("Content-Length", 0))
            if body_len > 0:
                body = self.rfile.read(body_len)

        # Proxy
        status, resp_headers, resp_body = proxy_request(
            method, route["host"], route["port"],
            backend_path, self.headers, body
        )

        # Record usage on success
        if status < 400:
            record_usage(ip, route_name)

        # Send response
        self.send_response(status)
        for k, v in resp_headers.items():
            if k.lower() not in ("transfer-encoding", "connection"):
                self.send_header(k, v)
        self.send_header("X-Poke-Gateway", "v1.0")
        self.send_header("X-Route", route_name)
        self.send_header("Content-Length", str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

    def _send_json(self, data, code=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

class Reusable(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"🌐 Poke Gateway v1.0 on port {PORT}")
    print(f"   Routes: {', '.join(ROUTES.keys())}")
    print(f"   Wallet: {WALLET}")
    print(f"   Free: {FREE_LIMIT}/day per IP | Paid: {PRICE_USDC} USDC")
    Reusable(("", PORT), Handler).serve_forever()
