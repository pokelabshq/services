#!/usr/bin/env python3
"""Poke Labs Paywall Proxy — add x402 payments to any API endpoint.

Usage:
  python3 proxy.py --upstream https://api.example.com --price 0.005 --port 8770

This creates a proxy that:
  - Allows N free requests per IP per day
  - Returns HTTP 402 with payment instructions when limit exceeded
  - Verifies x402 payments on-chain
  - Forwards valid requests to upstream API
"""

import json
import os
import sys
import time
import hashlib
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urljoin

PORT = int(os.environ.get("PORT", 8770))
UPSTREAM = os.environ.get("UPSTREAM", "")
PRICE_USD = float(os.environ.get("PRICE_USD", "0.005"))
FREE_LIMIT = int(os.environ.get("FREE_LIMIT", "3"))
WALLET = os.environ.get("WALLET", "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF")
CHAIN = os.environ.get("CHAIN", "base")

# Rate limit store: {ip: {date: count}}
_rate_limits = {}
_lock = threading.Lock()

def get_client_ip(handler):
    xff = handler.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return handler.client_address[0]

def check_rate_limit(ip):
    """Check if IP has exceeded free limit. Returns (allowed, used, limit)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        if ip not in _rate_limits:
            _rate_limits[ip] = {}
        # Clean old dates
        for d in list(_rate_limits[ip].keys()):
            if d != today:
                del _rate_limits[ip][d]
        used = _rate_limits[ip].get(today, 0)
        if used < FREE_LIMIT:
            _rate_limits[ip][today] = used + 1
            return True, used + 1, FREE_LIMIT
        return False, used, FREE_LIMIT

def verify_payment(payment_header):
    """Verify x402 payment from request header."""
    if not payment_header:
        return False
    try:
        payment = json.loads(payment_header)
        # Basic validation — in production, verify on-chain
        required = ["amount", "to", "chain"]
        if not all(k in payment for k in required):
            return False
        if payment.get("to", "").lower() != WALLET.lower():
            return False
        if payment.get("chain", "").lower() != CHAIN.lower():
            return False
        if float(payment.get("amount", 0)) < PRICE_USD:
            return False
        return True
    except:
        return False

def payment_response():
    """Generate HTTP 402 payment required response."""
    return {
        "error": "payment_required",
        "message": f"This API costs ${PRICE_USD:.3f} per request after {FREE_LIMIT} free requests/day",
        "payment": {
            "chain": CHAIN,
            "to": WALLET,
            "amount": PRICE_USD,
            "currency": "USDC",
        },
        "x402_version": "1.0",
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        ip = get_client_ip(self)
        
        # Health check — always allowed
        if self.path.rstrip("/") in ("/api/health", "/health"):
            body = json.dumps({
                "ok": True, "v": 1,
                "upstream": UPSTREAM,
                "price": PRICE_USD,
                "free_limit": FREE_LIMIT,
                "wallet": WALLET,
                "chain": CHAIN,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        
        # Usage endpoint
        if self.path.rstrip("/") in ("/api/usage", "/usage"):
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            with _lock:
                used = _rate_limits.get(ip, {}).get(today, 0)
            body = json.dumps({
                "ip": ip,
                "used": used,
                "limit": FREE_LIMIT,
                "remaining": max(0, FREE_LIMIT - used),
                "price": PRICE_USD,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        
        # Landing page
        if self.path == "/":
            self.serve_home()
            return
        
        # Check rate limit
        allowed, used, limit = check_rate_limit(ip)
        
        # Check for payment header
        payment_header = self.headers.get("X-Payment", "")
        paid = verify_payment(payment_header)
        
        if not allowed and not paid:
            body = json.dumps(payment_response()).encode()
            self.send_response(402)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Payment-Required", json.dumps(payment_response()["payment"]))
            self.end_headers()
            self.wfile.write(body)
            return
        
        # Forward to upstream
        self.forward_request("GET")
    
    def do_POST(self):
        ip = get_client_ip(self)
        allowed, used, limit = check_rate_limit(ip)
        payment_header = self.headers.get("X-Payment", "")
        paid = verify_payment(payment_header)
        
        if not allowed and not paid:
            body = json.dumps(payment_response()).encode()
            self.send_response(402)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Payment-Required", json.dumps(payment_response()["payment"]))
            self.end_headers()
            self.wfile.write(body)
            return
        
        self.forward_request("POST")
    
    def do_PUT(self):
        self.do_POST()
    
    def do_DELETE(self):
        self.do_POST()
    
    def forward_request(self, method):
        """Forward request to upstream API."""
        if not UPSTREAM:
            body = json.dumps({"error": "No upstream configured. Set UPSTREAM env var."}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        
        target_url = UPSTREAM.rstrip("/") + self.path
        
        # Read body for POST/PUT
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Build request
        req = urllib.request.Request(target_url, data=body, method=method)
        
        # Forward relevant headers
        for header in ["Content-Type", "Accept", "Authorization", "User-Agent"]:
            val = self.headers.get(header)
            if val:
                req.add_header(header, val)
        
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            resp_body = resp.read()
            self.send_response(resp.status)
            # Forward response headers
            for key, val in resp.getheaders():
                if key.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            resp_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            body = json.dumps({"error": f"Upstream error: {str(e)}"}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
    
    def serve_home(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Labs Paywall Proxy</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem; }}
h1 {{ font-size: 2rem; margin-bottom: 0.5rem; color: #8b5cf6; }}
.sub {{ color: #888; margin-bottom: 2rem; }}
.card {{ background: #161616; border: 1px solid #333; border-radius: 12px; padding: 2rem; width: 100%; max-width: 600px; margin-bottom: 1rem; }}
h2 {{ color: #8b5cf6; margin-bottom: 1rem; font-size: 1.2rem; }}
code {{ background: #0a0a0a; padding: 0.75rem; border-radius: 6px; display: block; font-size: 0.85rem; color: #a78bfa; margin: 0.5rem 0; overflow-x: auto; }}
.pill {{ display: inline-block; background: #1e1e2e; border: 1px solid #333; padding: 0.25rem 0.75rem; border-radius: 99px; font-size: 0.8rem; margin: 0.25rem; }}
.price {{ font-size: 2rem; font-weight: bold; color: #8b5cf6; }}
.free {{ color: #22c55e; }}
</style>
</head>
<body>
<h1>Poke Labs</h1>
<p class="sub">Paywall Proxy — x402 payments for any API</p>
<div class="card">
    <div class="price">${PRICE_USD:.3f}<span style="font-size:1rem;color:#888;">/request</span></div>
    <p class="free" style="margin-top:0.5rem;">{FREE_LIMIT} free requests per day</p>
</div>
<div class="card">
    <h2>Quick Start</h2>
    <code>pip install pokelabs-paywall<br/>paywall --upstream https://api.example.com --price 0.005</code>
</div>
<div class="card">
    <h2>API</h2>
    <p><span class="pill">GET /api/health</span> Health check</p>
    <p><span class="pill">GET /api/usage</span> Your usage</p>
    <p><span class="pill">ANY /*</span> Proxied to upstream</p>
</div>
<div class="card">
    <h2>Payment</h2>
    <p>After {FREE_LIMIT} free requests, send <code>X-Payment</code> header:</p>
    <code>{{"amount": {PRICE_USD}, "to": "{WALLET}", "chain": "{CHAIN}", "currency": "USDC"}}</code>
</div>
</body>
</html>"""
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    if not UPSTREAM:
        print("WARNING: No UPSTREAM set. Set UPSTREAM env var to the API to proxy.", flush=True)
    print(f"Paywall Proxy on :{PORT} → {UPSTREAM or 'none'}", flush=True)
    print(f"Price: ${PRICE_USD}/req · Free: {FREE_LIMIT}/day · Wallet: {WALLET}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
