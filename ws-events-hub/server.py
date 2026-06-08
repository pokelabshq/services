#!/usr/bin/env python3
"""WebSocket Events Hub v1.0 — Real-time event streaming for Poke Labs services.
Receives events from services, broadcasts to all connected subscribers. Port: 8767. Zero deps."""
import http.server, json, time, urllib.parse, hashlib, threading, socket, base64, struct, os, html as htmlmod

PORT = 8767
clients = {}  # conn -> {id, connected_at, path}
clients_lock = threading.Lock()
events_log = []  # last 100 events
events_lock = threading.Lock()

def add_event(data):
    with events_lock:
        events_log.append({"ts": time.time(), "data": data})
        if len(events_log) > 100:
            events_log.pop(0)

def get_events():
    with events_lock:
        return list(events_log)

def ws_handshake(headers):
    key = headers.get("Sec-WebSocket-Key", "")
    magic = "258EAFA5-E914-47DA-95CA-5AB5DC525A1F"
    accept = base64.b64encode(hashlib.sha1((key + magic).encode()).digest()).decode()
    return accept

def ws_send(conn, data):
    payload = json.dumps(data).encode()
    length = len(payload)
    mask_key = os.urandom(4)
    if length < 126:
        header = struct.pack("!BB", 0x81, 0x80 | length)
    elif length < 65536:
        header = struct.pack("!BBH", 0x81, 0x80 | 126, length)
    else:
        header = struct.pack("!BBQ", 0x81, 0x80 | 127, length)
    masked = bytes(payload[i] ^ mask_key[i % 4] for i in range(length))
    try:
        conn.sendall(header + mask_key + masked)
    except:
        pass

def ws_recv(conn):
    try:
        h1 = conn.recv(2)
        if len(h1) < 2: return None
        opcode = h1[0] & 0x0F
        payload_len = h1[1] & 0x7F
        masked = bool(h1[1] & 0x80)
        if payload_len == 126:
            ext = conn.recv(2)
            payload_len = struct.unpack("!H", ext)[0]
        elif payload_len == 127:
            ext = conn.recv(8)
            payload_len = struct.unpack("!Q", ext)[0]
        if masked:
            mask = conn.recv(4)
        payload = b""
        while len(payload) < payload_len:
            chunk = conn.recv(min(payload_len - len(payload), 65536))
            if not chunk: break
            payload += chunk
        if masked:
            payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
        if opcode == 8: return None  # close
        return json.loads(payload.decode()) if payload else None
    except:
        return None

def broadcast(data, exclude=None):
    with clients_lock:
        dead = []
        for conn, info in clients.items():
            if conn == exclude: continue
            try:
                ws_send(conn, data)
            except:
                dead.append(conn)
        for conn in dead:
            del clients[conn]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            with clients_lock:
                cc = len(clients)
            self.json({"ok": True, "v": 1, "port": PORT, "clients": cc, "protocol": "websocket"})
        elif p.path == "/api/events":
            self.json({"events": get_events()[-20:]})
        elif p.path == "/api/clients":
            with clients_lock:
                infos = [{"id": info["id"], "path": info["path"], "connected_since": info["connected_at"]} for info in clients.values()]
            self.json({"clients": infos})
        elif p.path == "/":
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        cl = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(cl)) if cl else {}
        if p.path in ("/api/publish", "/api/publish/"):
            event = body.get("event", "message")
            payload = body.get("data", body)
            evt = {"type": event, "data": payload, "ts": time.time(), "source": body.get("source", "unknown")}
            add_event(evt)
            broadcast(evt)
            self.json({"ok": True, "event": event})
        else:
            self.json({"error": "Not found"}, 404)

    def handle_ws(self):
        accept = ws_handshake(self.headers)
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        conn = self.wfile
        with clients_lock:
            clients[conn] = {"id": id(conn), "connected_at": time.time(), "path": self.path}
        try:
            ws_send(conn, {"type": "connected", "clients": len(clients)})
            while True:
                msg = ws_recv(conn)
                if msg is None: break
                if msg.get("type") == "ping":
                    ws_send(conn, {"type": "pong", "ts": time.time()})
                elif msg.get("type") == "publish":
                    evt = {"type": msg.get("event", "message"), "data": msg.get("data", {}), "ts": time.time()}
                    add_event(evt)
                    broadcast(evt)
                    ws_send(conn, {"type": "published"})
                elif msg.get("type") == "subscribe":
                    ws_send(conn, {"type": "subscribed", "events": get_events()[-10:]})
        except: pass
        finally:
            with clients_lock:
                clients.pop(conn, None)

    def setup(self):
        http.server.BaseHTTPRequestHandler.setup(self)
        if self.headers.get("Upgrade", "").lower() == "websocket":
            self.handle_ws()
            raise Exception("WS handled")

    def dashboard(self):
        s = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>WebSocket Events Hub — Poke Labs</title><style>body{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;flex-direction:column}.c{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:30px;max-width:600px;width:90%;text-align:center}h1{color:#00ffaa}#log{font-family:monospace;font-size:.75em;background:rgba(0,0,0,0.3);border-radius:8px;padding:15px;text-align:left;max-height:300px;overflow-y:auto;white-space:pre-wrap;color:#00ffaa}.btn{background:#00ffaa;color:#0a0a1a;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;margin:5px;font-size:.85rem}</style></head><body><div class="c"><h1>⚡ WebSocket Events Hub</h1><p style="color:#888">Real-time event streaming for Poke Labs — Port 8767</p><div><button class="btn" onclick="test()">📡 Send Test Event</button><button class="btn" onclick="loadEvents()">📋 Load Events</button></div><div id="log">Ready...</div></div><script>const log=m=>{const d=document.getElementById('log');d.textContent+=m+'\n';d.scrollTop=d.scrollHeight};async function test(){const r=await fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event:'test',data:{msg:'Hello from browser'},source:'dashboard'})});const d=await r.json();log('Sent: '+JSON.stringify(d))}async function loadEvents(){const r=await fetch('/api/events');const d=await r.json();log('Events: '+JSON.stringify(d.events.slice(-5),null,2))}</script></body></html>'''
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"WebSocket Events Hub v1.0 on :{PORT}");s.serve_forever()
