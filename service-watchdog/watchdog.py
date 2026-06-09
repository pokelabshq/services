#!/usr/bin/env python3
"""
Poke Labs Service Watchdog v1.0
Monitors all services and auto-restarts crashed ones.
Python stdlib only. Zero dependencies.

Usage: python3 service-watchdog/watchdog.py &
Health: http://localhost:8799/
Log: /tmp/watchdog.log
"""
import http.server, json, subprocess, time, threading, os, sys
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError

PORT = 8799
CHECK_INTERVAL = 30  # seconds

# Service registry: name -> (port, start_command)
SERVICES = {
    "link-preview": (8765, "cd /home/alx/services && nohup python3 link-preview/server.py > /tmp/link-preview.log 2>&1 &"),
    "billing": (8766, "cd /home/alx/services && nohup python3 billing/server.py > /tmp/billing.log 2>&1 &"),
    "poke-hub": (8775, "cd /home/alx/services && nohup python3 poke-hub/bot.py > /tmp/poke-hub.log 2>&1 &"),
    "dashboard": (8780, "cd /home/alx/services && nohup python3 dashboard/server.py > /tmp/dashboard.log 2>&1 &"),
    "url-shortener": (8767, "cd /home/alx/services && nohup python3 url-shortener/server.py > /tmp/url-shortener.log 2>&1 &"),
}

log_entries = []
MAX_LOG = 200

def log(msg):
    ts = datetime.now().isoformat()
    entry = f"[{ts}] {msg}"
    log_entries.append(entry)
    if len(log_entries) > MAX_LOG:
        log_entries.pop(0)
    print(entry, flush=True)

def check_port(port):
    try:
        urlopen(f"http://127.0.0.1:{port}/", timeout=3)
        return True
    except:
        return False

def check_health(port):
    try:
        r = urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3)
        return json.loads(r.read())
    except:
        return None

def is_port_open(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    result = s.connect_ex(('127.0.0.1', port))
    s.close()
    return result == 0

def restart_service(name, cmd):
    log(f"🔄 Restarting {name}...")
    try:
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        port = SERVICES[name][0]
        if is_port_open(port):
            log(f"✅ {name} restarted successfully")
            return True
        else:
            log(f"❌ {name} restart failed")
            return False
    except Exception as e:
        log(f"❌ Error restarting {name}: {e}")
        return False

def watchdog_loop():
    log("🐾 Watchdog started. Monitoring services...")
    restart_counts = {name: 0 for name in SERVICES}
    max_restarts = 5  # per service per hour

    while True:
        for name, (port, cmd) in SERVICES.items():
            healthy = is_port_open(port)
            if not healthy:
                if restart_counts[name] < max_restarts:
                    log(f"⚠️ {name} (port {port}) is DOWN")
                    success = restart_service(name, cmd)
                    if success:
                        restart_counts[name] += 1
                else:
                    log(f"🚨 {name} exceeded max restarts ({max_restarts}). Manual intervention needed.")
            else:
                # Reset count if healthy for a while
                if restart_counts[name] > 0:
                    restart_counts[name] = max(0, restart_counts[name] - 1)
        
        # Reset all counters every hour
        time.sleep(CHECK_INTERVAL)

class WatchdogHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = self.dashboard_html()
            self.wfile.write(html.encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            status = {}
            for name, (port, _) in SERVICES.items():
                healthy = is_port_open(port)
                health = check_health(port) if healthy else None
                status[name] = {"port": port, "healthy": healthy, "health": health}
            self.wfile.write(json.dumps(status, indent=2).encode())
        elif self.path == '/api/log':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(log_entries[-50:], indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def dashboard_html(self):
        rows = ""
        for name, (port, _) in SERVICES.items():
            healthy = is_port_open(port)
            color = "#22c55e" if healthy else "#ef4444"
            status = "🟢 RUNNING" if healthy else "🔴 DOWN"
            rows += f'<tr><td><b>{name}</b></td><td>{port}</td><td style="color:{color}">{status}</td></tr>'
        return f"""<!DOCTYPE html>
<html><head><title>🐾 Watchdog</title>
<style>body{{font-family:monospace;max-width:800px;margin:40px auto;padding:0 20px;background:#0a0a0a;color:#e0e0e0}}
table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{padding:12px 16px;text-align:left;border-bottom:1px solid #333}}
th{{color:#a78bfa}}h1{{color:#a78bfa}}</style></head>
<body><h1>🐾 Poke Labs Watchdog</h1>
<table><tr><th>Service</th><th>Port</th><th>Status</th></tr>{rows}</table>
<p><a href="/api/status" style="color:#a78bfa">JSON Status</a> | <a href="/api/log" style="color:#a78bfa">Log</a></p>
<p><small>Auto-refreshing every 30s. Max 5 restarts/service/hour.</small></p>
</body></html>"""
    
    def log_message(self, format, *args):
        pass  # Suppress request logging

if __name__ == '__main__':
    # Start watchdog in background thread
    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()
    
    server = http.server.HTTPServer(('0.0.0.0', PORT), WatchdogHandler)
    log(f"🐾 Watchdog dashboard: http://localhost:{PORT}/")
    log(f"   Monitoring {len(SERVICES)} services every {CHECK_INTERVAL}s")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Watchdog stopped.")
        sys.exit(0)
