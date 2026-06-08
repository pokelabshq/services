#!/usr/bin/env python3
"""poke — Poke Labs CLI v1.0
Usage: python3 poke.py <command> [args]

Commands:
  list              List all services
  start <name>      Start a service
  stop <name>       Stop a service
  restart <name>    Restart a service
  status            Show status of all services
  logs <name>       Show logs for a service
  health            Check health of all running services
  deploy            Deploy all services
  version           Show version info
"""
import sys, os, json, subprocess, time, socket, urllib.request

SERVICES_DIR = "/home/alx/services"
VERSION = "1.0.0"
COLORS = {
    "green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m",
    "blue": "\033[94m", "cyan": "\033[96m", "reset": "\033[0m", "bold": "\033[1m"
}
def c(color, text): return f"{COLORS.get(color,'')}{text}{COLORS['reset']}"

SERVER_FILES = ("server.py","app.py","bot.py","gateway.py","index.py","deploy.py","digest.py")

def discover():
    svcs = []
    for name in sorted(os.listdir(SERVICES_DIR)):
        path = os.path.join(SERVICES_DIR, name)
        if not os.path.isdir(path): continue
        servers, port = [], None
        for f in os.listdir(path):
            if f.lower() in SERVER_FILES:
                servers.append(f)
                if port is None:
                    try:
                        with open(os.path.join(path, f)) as fh:
                            import re
                            for line in fh:
                                m = re.search(r'PORT\s*=\s*(\d{4,5})', line)
                                if m: port = int(m.group(1)); break
                    except: pass
        pid, status = None, "stopped"
        if port:
            try:
                r = subprocess.run(["pgrep","-f",f".*{name}.*.py"],capture_output=True,text=True,timeout=2)
                if r.stdout.strip():
                    pid = int(r.stdout.strip().split("\n")[0])
                    s = socket.socket(); s.settimeout(1)
                    s.connect(("127.0.0.1", port)); s.close()
                    status = "running"
            except: pass
        svcs.append({"name":name,"servers":servers,"port":port,"pid":pid,"status":status,"path":path})
    return svcs

def cmd_list():
    svcs = discover()
    print(f"\n{c('bold','Poke Labs Services')} — {len(svcs)} total\n")
    print(f"{'Service':<30} {'Port':<8} {'Status':<10} {'Files'}")
    print("─" * 70)
    for s in svcs:
        color = "green" if s["status"]=="running" else "red"
        port = str(s["port"]) if s["port"] else "—"
        files = ", ".join(s["servers"][:2]) if s["servers"] else "—"
        print(f"{s['name']:<30} {port:<8} {c(color,s['status']):<10} {files}")
    print()

def cmd_status():
    svcs = discover()
    running = sum(1 for s in svcs if s["status"]=="running")
    print(f"\n{c('bold','Poke Labs Status')}")
    print(f"Services: {len(svcs)} total, {c('green',str(running))} running, {c('red',str(len(svcs)-running))} stopped")
    for s in svcs:
        icon = "🟢" if s["status"]=="running" else "🔴"
        port = f":{s['port']}" if s['port'] else ""
        print(f"  {icon} {s['name']}{port} ({s['status']})")
    print()

def cmd_start(name):
    path = os.path.join(SERVICES_DIR, name)
    if not os.path.isdir(path): print(c("red", f"Service '{name}' not found")); return
    for sn in SERVER_FILES:
        fp = os.path.join(path, sn)
        if os.path.exists(fp):
            p = subprocess.Popen(["python3", fp], stdout=open(f"/tmp/{name}.log","a"), stderr=subprocess.STDOUT, start_new_session=True)
            print(c("green", f"Started {name} (PID {p.pid}, {sn})"))
            return
    print(c("red", f"No server file found in {name}"))

def cmd_stop(name):
    os.system(f"pkill -f '{SERVICES_DIR}/{name}/' 2>/dev/null")
    print(c("yellow", f"Stopped {name}"))

def cmd_restart(name):
    cmd_stop(name); time.sleep(1); cmd_start(name)

def cmd_logs(name):
    log = f"/tmp/{name}.log"
    if os.path.exists(log):
        r = subprocess.run(["tail", "-50", log], capture_output=True, text=True)
        print(r.stdout if r.stdout else "(empty log)")
    else:
        print(c("yellow", f"No log file for {name}"))

def cmd_health():
    svcs = discover()
    running = [s for s in svcs if s["status"]=="running"]
    print(f"\n{c('bold','Health Check')} — {len(running)} running services\n")
    for s in running:
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{s['port']}/api/health", timeout=3)
            data = json.loads(r.read())
            ok = data.get("ok", False)
            ver = data.get("v", "?")
            status = c("green", "✓") if ok else c("red", "✗")
            print(f"  {status} {s['name']}:{s['port']} v{ver}")
        except:
            print(f"  {c('red','✗')} {s['name']}:{s['port']} (health endpoint unreachable)")
    print()

def cmd_deploy():
    svcs = discover()
    print(c("bold", f"\nDeploying {len(svcs)} services...\n"))
    for s in svcs:
        if s["status"] != "running":
            cmd_start(s["name"])
            time.sleep(0.5)
        else:
            print(f"  {c('green','✓')} {s['name']} already running")
    print(c("bold", "\nDone."))

def cmd_version():
    svcs = discover()
    print(f"\n{c('bold','Poke Labs CLI v{VERSION}')}")
    print(f"Services: {len(svcs)}")
    print(f"Directory: {SERVICES_DIR}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print()

COMMANDS = {
    "list": cmd_list, "status": cmd_status, "health": cmd_health,
    "deploy": cmd_deploy, "version": cmd_version,
}

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        cmd_list()
        return
    cmd = args[0]
    if cmd in ("start","stop","restart","logs"):
        if len(args) < 2: print(f"Usage: poke {cmd} <name>"); return
        {"start":cmd_start,"stop":cmd_stop,"restart":cmd_restart,"logs":cmd_logs}[cmd](args[1])
    elif cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print(c("red", f"Unknown command: {cmd}"))
        print("Commands: list, start, stop, restart, status, logs, health, deploy, version")

if __name__ == "__main__":
    main()
