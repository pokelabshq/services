#!/usr/bin/env python3
"""
Poke Labs CLI v1 — Manage all Poke Labs services from one command.

Usage:
  poke status          Show status of all services
  poke start <name>    Start a service
  poke stop <name>     Stop a service
  poke restart <name>  Restart a service
  poke list            List all services
  poke logs <name>     Show logs for a service
  poke health          Health check all services
  poke deploy <name>   Deploy a service (copy to council repo)
"""

import sys, os, json, subprocess, re, urllib.request, datetime

SERVICES_DIR = "/home/alx/services"
PID_DIR = "/tmp/poke-pids"
LOG_DIR = "/tmp"

os.makedirs(PID_DIR, exist_ok=True)

def get_services():
    services = []
    for name in sorted(os.listdir(SERVICES_DIR)):
        skill = os.path.join(SERVICES_DIR, name, "SKILL.md")
        server = os.path.join(SERVICES_DIR, name, "server.py")
        if not os.path.exists(skill) and not os.path.exists(server):
            continue
        port = 0
        if os.path.exists(skill):
            pm = re.search(r'[Pp]ort[:\s]+(\d{4,5})', open(skill).read())
            if pm: port = int(pm.group(1))
        if not port and os.path.exists(server):
            pm = re.search(r'PORT\s*=\s*(\d{4,5})', open(server).read())
            if pm: port = int(pm.group(1))
        services.append({"name": name, "port": port, "has_server": os.path.exists(server)})
    return services

def is_running(name):
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    if not os.path.exists(pid_file):
        return False
    with open(pid_file) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        os.remove(pid_file)
        return False

def is_port_up(port):
    if not port: return None
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
        return True
    except urllib.error.HTTPError:
        return True
    except:
        return False

def cmd_list():
    services = get_services()
    print(f"{'SERVICE':<25} {'PORT':<8} {'STATUS':<10} {'HEALTH'}")
    print("-" * 60)
    for s in services:
        running = is_running(s["name"])
        health = is_port_up(s["port"]) if s["port"] else None
        status = "running" if running else "stopped"
        health_str = ("up" if health else "down") if health is not None else "n/a"
        print(f"{s['name']:<25} {s['port'] or '-':<8} {status:<10} {health_str}")
    print(f"\nTotal: {len(services)} services")

def cmd_status():
    services = get_services()
    running = sum(1 for s in services if is_running(s["name"]))
    healthy = sum(1 for s in services if s["port"] and is_port_up(s["port"]))
    with_ports = sum(1 for s in services if s["port"])
    print(f"🐾 Poke Labs Services")
    print(f"   Total:    {len(services)}")
    print(f"   Running:  {running}")
    print(f"   Healthy:  {healthy}/{with_ports} (with ports)")
    print(f"   Time:     {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def cmd_start(name):
    services = {s["name"]: s for s in get_services()}
    if name not in services:
        print(f"Unknown service: {name}")
        print(f"Available: {', '.join(services.keys())}")
        sys.exit(1)
    if is_running(name):
        print(f"{name} is already running")
        return
    s = services[name]
    if not s["has_server"]:
        print(f"{name} is a skill (no server to start)")
        return
    server = os.path.join(SERVICES_DIR, name, "server.py")
    log = os.path.join(LOG_DIR, f"{name}.log")
    proc = subprocess.Popen(
        ["python3", server],
        stdout=open(log, "w"), stderr=subprocess.STDOUT,
        preexec_fn=os.setsid
    )
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    with open(pid_file, "w") as f:
        f.write(str(proc.pid))
    print(f"Started {name} (PID {proc.pid}, log: {log})")

def cmd_stop(name):
    pid_file = os.path.join(PID_DIR, f"{name}.pid")
    if not os.path.exists(pid_file):
        print(f"{name} is not running")
        return
    with open(pid_file) as f:
        pid = int(f.read().strip())
    try:
        os.killpg(os.getpgid(pid), 9)
        print(f"Stopped {name} (PID {pid})")
    except ProcessLookupError:
        print(f"{name} was already dead (cleaned up)")
    except Exception as e:
        print(f"Error stopping {name}: {e}")
    if os.path.exists(pid_file):
        os.remove(pid_file)

def cmd_restart(name):
    cmd_stop(name)
    import time; time.sleep(1)
    cmd_start(name)

def cmd_logs(name):
    log = os.path.join(LOG_DIR, f"{name}.log")
    if not os.path.exists(log):
        print(f"No log file for {name}")
        return
    subprocess.run(["tail", "-50", log])

def cmd_health():
    services = get_services()
    all_ok = True
    for s in services:
        if not s["port"]:
            continue
        try:
            r = urllib.request.urlopen(f"http://localhost:{s['port']}/api/health", timeout=3)
            data = json.loads(r.read())
            print(f"✅ {s['name']}: {data}")
        except Exception as e:
            print(f"❌ {s['name']}: {e}")
            all_ok = False
    sys.exit(0 if all_ok else 1)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    commands = {
        "list": cmd_list, "status": cmd_status, "health": cmd_health,
    }
    
    if cmd in commands:
        commands[cmd]()
    elif cmd in ("start", "stop", "restart", "logs"):
        if len(sys.argv) < 3:
            print(f"Usage: poke {cmd} <name>")
            sys.exit(1)
        globals()[f"cmd_{cmd}"](sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: list, status, health, start, stop, restart, logs")
        sys.exit(1)

if __name__ == "__main__":
    main()
