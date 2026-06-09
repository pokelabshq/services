#!/usr/bin/env python3
"""Residual Income Dashboard v1.0 — Track and project revenue streams."""
import http.server, json, os, urllib.request
from datetime import datetime

PORT = int(os.environ.get("PORT", 8795))
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"

REV_STREAMS = [
    {"name": "Link Preview API", "type": "x402", "rate": 0.001, "unit": "per call", "free_tier": 3},
    {"name": "API Gateway", "type": "subscription", "rate": 5.00, "unit": "per month", "free_tier": 0},
    {"name": "GitHub Bot Hosting", "type": "subscription", "rate": 10.00, "unit": "per month", "free_tier": 0},
    {"name": "Deploy Manager", "type": "per-use", "rate": 0.01, "unit": "per deploy", "free_tier": 10},
]

HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Revenue Dashboard</title>
<style>
body{font-family:system-ui;background:#0a0a14;color:#c8c8d8;max-width:800px;margin:40px auto;padding:20px}
h1{color:#00d4ff}h2{color:#00d4ff;margin-top:24px}
.stream{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin:8px 0;display:flex;justify-content:space-between;align-items:center}
.stream .name{font-weight:600}.stream .rate{color:#3fb950;font-family:monospace}
.stream .type{font-size:0.75rem;background:#21262d;padding:2px 8px;border-radius:10px;color:#8b949e}
canvas{width:100%;height:200px;background:#161b22;border-radius:8px;margin:16px 0}
.footer{text-align:center;color:#6e7681;margin-top:40px;font-size:0.85rem}
</style></head>
<body><h1>💰 Residual Income Dashboard</h1>
<p>Live revenue tracking for Poke Labs' microservices.</p>
<h2>Active Revenue Streams</h2>
<div id="streams"></div>
<h2>30-Day Projection</h2><canvas id="chart" width="760" height="200"></canvas>
<h2>Wallet</h2>
<p style="font-family:monospace;font-size:0.85rem;word-break:break-all">""" + WALLET + """</p>
<div class="footer">🫧 Poke Labs · Dashboard v1.0</div>
<script>
const streams = """ + json.dumps(REV_STREAMS) + """;
const el = document.getElementById('streams');
streams.forEach(s => {
  const est = s.type === 'subscription' ? s.rate : (s.rate * 100);
  el.innerHTML += `<div class="span>
    <div><span class="name">${s.name}</span> <span class="type">${s.type}</span></div>
    <div class="rate">$${s.rate.toFixed(3)}/${s.unit} · ~$${est.toFixed(2)}/mo est</div>
  </div>`;
});
// Draw projection chart
const c = document.getElementById('chart');
const ctx = c.getContext('2d');
ctx.fillStyle = '#161b22';
ctx.fillRect(0,0,760,200);
const days=30; ctx.strokeStyle='#00d4ff'; ctx.lineWidth=2; ctx.beginPath();
for(let i=0;i<=days;i++){
  const x=30+(i*24); const y=180-((i*0.2)+Math.sin(i/3)*5)*3;
  i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
}
ctx.stroke();
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/": self.s(HTML)
        elif self.path=="/api/health": self.j({"ok":True,"v":1,"port":PORT})
        elif self.path=="/api/streams": self.j({"streams":REV_STREAMS,"count":len(REV_STREAMS)})
        else: self.j({"error":"not found"},404)
    def s(self,h):
        b=h.encode();self.send_response(200);self.send_header("Content-Type","text/html");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def j(self,d,c=200):
        b=json.dumps(d).encode();self.send_response(c);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def log_message(self,*a):pass

if __name__=="__main__":
    print(f"Revenue Dashboard v1.0 on port {PORT}")
    http.server.HTTPServer(("",PORT),H).serve_forever()
