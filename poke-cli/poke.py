#!/usr/bin/env python3
"""
Poke CLI v2.0 — Command-line fleet manager for all Poke Labs services.
Usage: python3 poke.py <command> [service_name]

Commands:
  list          List all services and their status
  start <name>  Start a service
  stop <name>   Stop a service
  restart <name> Restart a service
  health        Check health of all running services
  logs <name>   Show last 20 lines of service log
  ports         Show port allocation map
  discover      Re-scan for new services
"""
import sys, os, subprocess, json, re, signal, datetime

SERVICES_DIR = "/home/alx/services"
LOG_DIR = "/tmp"
ENTRY_FILES = ["server.py", "bot.py", "app.py", "main.py", "index.js"]

def discover():
    services = []
    for name in sorted(os.listdir(SERVICES_DIR)):
        sdir = os.path.join(SERVICES_DIR, name)
        if not os.path.isdir(sdir):
            continue
        for entry in ENTRY_FILES:
            fpath = os.path.join(sdir, entry)
            if os.path.isfile(fpath):
                port = detect_port(fpath)
                pid, running = check_running(port) if port else (None, False)
                services.append({
                    "name": name, "entry": entry, "path": sdir,
                    "port": port, "pid": pid, "running": running
                })
                break
    return services

def detect_port(filepath):
    try:
        with open(filepath) as f:
            for line in f:
                m = re.search(r'PORT\s*=\s*(\d{4,5})', line)
                if m:
                    return int(m.group(1))
    except:
        pass
    return None

def check_running(port):
    try:
        r = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, timeout=2)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().decode(), True
    except:
        pass
    return None, False

def cmd_list(services=None):
    svcs = services or discover()
    running = sum(1 for s in svcs if s["running"])
    print(f"\n🫧 Poke Labs Fleet — {len(services)} services, {running} running\n")
    print(f"{'STATUS':<8} {'PORT':<7} {'SERVICE':<30} {'ENTRY':<15} {'PID'}")
    print("─" * 75)
    for s in svcs:
        status = "🟢 UP" if s["running"] else "🔴 DOWN"
        port = str(s["port"]) if s["port"] else "—"
        pid = s["pid"] or "—"
        print(f"{status:<8} {port:<7} {s['name']:<30} {s['entry']:<15} {pid}")
    print()

def cmd_start(name):
    for s in discover():
        if s["name"] == name:
            if s["running"]:
                print(f"⚠️  {name} is already running (pid={s['pid']})")
                return
            fpath = os.path.join(s["path"], s["entry"])
            log = open(f"/tmp/{name}.log", "a")
            subprocess.Popen(
                ["nohup", "python3", fpath],
                stdout=log, stderr=subprocess.STDOUT,
                cwd=s["path"], start_new_session=True
            )
            print(f"✅ Started {name} ({s['entry']}) — log: /tmp/{name}.log")
            return
    print(f"❌ Service '{name}' not found")

def cmd_stop(name):
    for s in discover():
        if s["name"] == name:
            if not s["running"]:
                print(f"⚠️  {name} is not running")
                return
            if s["port"]:
                subprocess.run(["fuser", "-k", f"{s['port']}/tcp"], capture_output=True, timeout=3)
            print(f"🛑 Stopped {name}")
            return
    print(f"❌ Service '{name}' not found")

def cmd_restart(name):
    cmd_stop(name)
    import time; time.sleep(1)
    cmd_start(name)

def cmd_health():
    svcs = discover()
    running = [s for s in svcs if s["running"] and s["port"]]
    print(f"\n🏥 Health Check — {len(running)} running services with ports\n")
    for s in running:
        try:
            import urllib.request
            url = f"http://localhost:{s['port']}/api/health"
            r = urllib.request.urlopen(url, timeout=3)
            data = json.loads(r.read())
            print(f"  🟢 {s['name']:<30} {s['port']} — {data}")
        except:
            print(f"  🟡 {s['name']:<30} {s['port']} — running but no /api/health")
    print()

def cmd_logs(name):
    logpath = f"/tmp/{name}.log"
    if os.path.isfile(logpath):
        lines = open(logpath).readlines()
        print(f"\n📋 Last 20 lines of /tmp/{name}.log:\n")
        for line in lines[-20:]:
            print(f"  {line}", end="")
        print()
    else:
        print(f"❌ No log file at {logpath}")

def cmd_ports():
    svcs = discover()
    print(f"\n🔌 Port Allocation Map\n")
    for s in sorted(svcs, key=lambda x: x["port"] or 0):
        if s["port"]:
            status = "🟢" if s["running"] else "🔴"
            print(f"  {status} {s['port']} → {s['name']}")
    print()

def main():
    args = sys.argv[1:]
    if not args:
        cmd_list()
        return
    cmd = args[0]
    if cmd == "list":
        cmd_list()
    elif cmd == "start" and len(args) > 1:
        cmd_start(args[1])
    elif cmd == "stop" and len(args) > 1:
        cmd_stop(args[1])
    elif cmd == "restart" and len(args) > 1:
        cmd_restart(args[1])
    elif cmd == "health":
        cmd_health()
    elif cmd == "logs" and len(args) > 1:
        cmd_logs(args[1])
    elif cmd == "ports":
        cmd_ports()
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
