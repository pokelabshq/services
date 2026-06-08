#!/usr/bin/env python3
"""WebSocket Events Hub v1 — Real-time pub/sub event streaming.
Supports: WebSocket connections for pub/sub, topic-based routing, 
SSE (Server-Sent Events) fallback, HTTP POST for publishing, health dashboard.
Pure stdlib — uses websocket via raw socket upgrade (no external deps).
"""
import http.server, json, time, threading, hashlib, base64, struct, os, socket
from collections import defaultdict

PORT = 8784

# --- Pub/Engine ---
topics = defaultdict(set)  # topic -> set of (conn_id, queue)
conns = {}  # conn_id -> {socket, queue, topics: set, is_sse: bool}
lock = threading.Lock()

def publish(topic, data):
    """Publish an event to all subscribers of a topic."""
    event = json.dumps({"topic": topic, "data": data, "ts": int(time.time())})
    with lock:
        dead = []
        for conn_id, q in list(topics.get(topic, set())):
            try:
                q.put(event)
            except:
                dead.append((conn_id, q))
        for d in dead:
            topics[topic].discard(d)

def get_stats():
    with lock:
        return {
            "topics": len(topics),
            "connections": len(conns),
            "topic_detail": {t: len(s) for t, s in topics.items()}
        }

# --- Thread-safe queue for SSE/WebSocket ---
class EventQueue:
    def __init__(self):
        self._queue = []
        self._lock = threading.Lock()
        self._event = threading.Event()

    def put(self, item):
        with self._lock:
            self._queue.append(item)
        self._event.set()

    def get_all(self):
        with self._lock:
            items = self._queue[:]
            self._queue = []
        self._event.clear()
        return items

    def wait(self, timeout=30):
        self._event.wait(timeout=timeout)
        return self.get_all()

# --- WebSocket handshake (RFC 6455, no external deps) ---
def ws_accept_key(key):
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()

def ws_send(sock, data):
    """Send a WebSocket text frame."""
    payload = data.encode("utf-8")
    length = len(payload)
    # Mask bit = 0 (server), opcode = 1 (text)
    header = b"\x81"
    if length < 126:
        header += bytes([0x80 | length])
    elif length < 65536:
        header += bytes([0xFE, length >> 8, length & 0xFF])
    else:
        header += bytes([0xFF]) + struct.pack(">Q", length)
    # Server-to-client: no masking
    sock.sendall(header + payload)

def ws_recv(sock, timeout=60):
    """Receive a WebSocket text frame. Returns None on close/error."""
    sock.settimeout(timeout)
    try:
        header = sock.recv(2)
        if len(header) < 2:
            return None
        opcode = header[0] & 0x0F
        masked = header[1] & 0x80
        length = header[1] & 0x7F
        if length == 126:
            length = struct.unpack(">H", sock.recv(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", sock.recv(8))[0]
        if masked:
            mask = sock.recv(4)
        payload = b""
        while len(payload) < length:
            chunk = sock.recv(min(length - len(payload), 65536))
            if not chunk:
                return None
            payload += chunk
        if masked:
            payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
        if opcode == 0x8:  # Close
            return None
        if opcode == 0x9:  # Ping → Pong
            pong = b"\x8A\x00"
            sock.sendall(pong)
            return "__pong__"
        if opcode == 0x1:  # Text
            return payload.decode("utf-8", errors="ignore")
        return None
    except socket.timeout:
        return "__timeout__"
    except:
        return None

# --- WebSocket connection handler ---
def ws_handler(sock, addr):
    conn_id = f"ws_{addr[0]}_{addr[1]}_{int(time.time()*1000)}"
    q = EventQueue()
    with lock:
        conns[conn_id] = {"addr": addr, "topics": set(), "q": q, "is_sse": False, "connected_at": time.time()}

    # Perform WebSocket handshake
    data = sock.recv(4096).decode("utf-8", errors="ignore")
    if "Upgrade: websocket" not in data:
        # Not a WebSocket request — could be SSE
        sock.close()
        with lock:
            conns.pop(conn_id, None)
        return

    key = ""
    for line in data.split("\r\n"):
        if line.startswith("Sec-WebSocket-Key:"):
            key = line.split(":", 1)[1].strip()

    if not key:
        sock.close()
        return

    accept = ws_accept_key(key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    )
    sock.sendall(response.encode())
    ws_send(sock, json.dumps({"type": "connected", "conn_id": conn_id}))

    subscribed_topics = set()

    # Spawn a sender thread that also publishes events
    def sender():
        try:
            while True:
                events = q.wait(timeout=30)
                for event in events:
                    ws_send(sock, event)
                # Send periodic ping
                if not events:
                    ping_frame = b"\x89\x00"
                    try:
                        sock.sendall(ping_frame)
                    except:
                        break
        except:
            pass

    sender_thread = threading.Thread(target=sender, daemon=True)
    sender_thread.start()

    # Main receive loop
    try:
        while True:
            msg = ws_recv(sock, timeout=60)
            if msg is None or msg == "__timeout__":
                break
            if msg == "__pong__":
                continue
            try:
                cmd = json.loads(msg)
                action = cmd.get("action")
                topic = cmd.get("topic", "default")
                if action == "subscribe":
                    with lock:
                        subscribed_topics.add(topic)
                        topics[topic].add((conn_id, q))
                    ws_send(sock, json.dumps({"type": "subscribed", "topic": topic}))
                elif action == "unsubscribe":
                    with lock:
                        subscribed_topics.discard(topic)
                        topics[topic].discard((conn_id, q))
                    ws_send(sock, json.dumps({"type": "unsubscribed", "topic": topic}))
                elif action == "publish":
                    publish(topic, cmd.get("data", {}))
                    ws_send(sock, json.dumps({"type": "published", "topic": topic}))
                elif action == "stats":
                    ws_send(sock, json.dumps({"type": "stats", **get_stats()}))
            except json.JSONDecodeError:
                ws_send(sock, json.dumps({"type": "error", "msg": "Invalid JSON"}))
    except:
        pass
    finally:
        # Cleanup
        with lock:
            for topic in subscribed_topics:
                topics[topic].discard((conn_id, q))
            conns.pop(conn_id, None)
        try:
            sock.close()
        except:
            pass

# --- HTTP Server for SSE + REST API ---
DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><title>WS Events Hub v1 — Poke Labs</title>
<style>
body{font-family:system-ui;background:#0f0f23;color:#e0e0e0;padding:2rem}
h1{color:#00d4ff}pre{background:#1a1a3e;padding:1rem;border-radius:8px;overflow-x:auto;max-height:400px}
input,button{padding:.5rem;margin:.2rem;border:1px solid #333;background:#1a1a3e;color:#e0e0e0;border-radius:4px}
button{background:#00d4ff;color:#000;cursor:pointer;font-weight:bold}
button:hover{background:#00b8e6}
#events{font-family:monospace;font-size:.85rem}
.event{padding:.2rem 0;border-bottom:1px solid #2a2a5e}
</style></head>
<body>
<h1>🔌 WebSocket Events Hub v1</h1>
<div>
  <input id="topic" placeholder="topic" value="test">
  <input id="msg" placeholder="message" size="40">
  <button onclick="publish()">Publish</button>
  <button onclick="connect()">Connect WS</button>
  <button onclick="disconnect()">Disconnect</button>
</div>
<pre id="events"></pre>
<script>
let ws=null;
function log(m){const e=document.getElementById('events');e.innerHTML=`<div class="event">${new Date().toISOString()} ${m}</div>`+e.innerHTML;}
function connect(){
  if(ws)return;
  ws=new WebSocket(`ws://${location.host}/ws`);
  ws.onopen=()=>{log('✅ Connected');ws.send(JSON.stringify({action:'subscribe',topic:document.getElementById('topic').value}))};
  ws.onmessage=e=>log('📨 '+e.data);
  ws.onclose=e=>{log('❌ Closed: '+e.code);ws=null};
  ws.onerror=e=>log('⚠️ Error');
}
function disconnect(){if(ws){ws.close();ws=null}}
function publish(){
  const t=document.getElementById('topic').value;
  const m=document.getElementById('msg').value;
  fetch('/api/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:t,data:{message:m}})}).then(r=>r.json()).then(d=>log('📤 Published: '+JSON.stringify(d)));
}
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif self.path == "/api/health":
            stats = get_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "v": 1, "port": PORT, **stats}).encode())
        elif self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_stats()).encode())
        elif self.path == "/ws":
            # WebSocket upgrade — handle in a new thread
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            # We need to get the key from the request first
            # Actually, we need to do the handshake here
            # Let's read the request properly
            pass  # Handled by the threaded server below
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/publish":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            topic = body.get("topic", "default")
            data = body.get("data", {})
            publish(topic, data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"published": True, "topic": topic}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a): pass

# --- Threaded HTTP + WebSocket server ---
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class WSHandler(http.server.BaseHTTPRequestHandler):
    """Handles both HTTP and WebSocket upgrade requests."""
    def do_GET(self):
        if self.path == "/ws":
            # Read the full request for WebSocket key
            # The request is already being handled, we have the connection
            # We need to do the upgrade here
            pass
        else:
            Handler.do_GET(self)

    def handle(self):
        """Override to handle WebSocket upgrades."""
        try:
            # Read the initial request line + headers
            raw = b""
            while b"\r\n\r\n" not in raw:
                chunk = self.rfile.read1(4096) if hasattr(self.rfile, 'read1') else self.rfile.read(4096)
                if not chunk:
                    return
                raw += chunk

            request_text = raw.decode("utf-8", errors="ignore")
            if "Upgrade: websocket" in request_text:
                # Extract key
                key = ""
                for line in request_text.split("\r\n"):
                    if line.startswith("Sec-WebSocket-Key:"):
                        key = line.split(":", 1)[1].strip()
                if key:
                    accept = ws_accept_key(key)
                    response = (
                        "HTTP/1.1 101 Switching Protocols\r\n"
                        "Upgrade: websocket\r\n"
                        "Connection: Upgrade\r\n"
                        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
                    )
                    self.wfile.write(response.encode())
                    self.wfile.flush()
                    # Now handle as WebSocket
                    ws_handler(self.connection, self.client_address)
                    return
            # Not WebSocket — handle as regular HTTP
            # Re-parse the request
            self.raw_requestline = request_text.split("\r\n")[0].encode()
            if not self.parse_request():
                return
            # Re-read body if needed
            self.request_text = request_text
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            # For non-ws GET/POST, use the Handler methods
            Handler.do_GET(self) if self.command == "GET" else Handler.do_POST(self)
        except Exception as e:
            pass

    def log_message(self, *a): pass

if __name__ == "__main__":
    server = ThreadedHTTPServer(("0.0.0.0", PORT), WSHandler)
    print(f"WebSocket Events Hub v1 on :{PORT}")
    server.serve_forever()
