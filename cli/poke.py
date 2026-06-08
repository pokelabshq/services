#!/usr/bin/env python3
"""Poke CLI v1.0 — Command-line tool to manage all Poke Labs services.
Usage: python3 poke.py <command> [args]
Commands:
  list              — List all services
  start <name|all>  — Start a service (or all)
  stop <name|all>   — Stop a service (or all)
  restart <name|all>— Restart a service
  status [name]     — Check status of one or all services
  logs <name>       — Tail logs for a service
  health            — Quick health summary
  dashboard         — Open health dashboard URL
"""
import sys, os, socket, json, subprocess, time

SERVICES_DIR = "/home/alx/services"
LOG_DIR = "/tmp/poke-labs"

SERVICES = {
    "link-preview":     {"port": 8765, "file": "server.py",  "desc": "URL metadata API"},
    "pokelabs-site":    {"port": 8766, "file": "server.py",  "desc": "Landing page + dashboard"},
    "poke-bot":         {"port": 8770, "file": "bot.py",     "desc": "GitHub auto-triage"},
    "poke-hub":         {"port": 8775, "file": "bot.py",     "desc": "All-in-one GitHub bot"},
    "telegram-bot":     {"port": 8777, "file": "bot.py",     "desc": "Telegram integration"},
    "skills-hub":       {"port": 8780, "file": "server.py",  "desc": "Skills directory"},
    "skills-marketplace":{"port": 8781, "file": "server.py",  "desc": "Skills marketplace v2"},
    "registry":         {"port": 8785, "file": "server.py",  "desc": "Agent registry"},
    "billing":          {"port": 8795, "file": "server.py",  "desc": "Billing service"},
    "health-aggregator":{"port": 8799, "file": "agg.py",     "desc": "Health monitoring"},
}

def port_open(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def svc_path(name):
    return os.path.join(SERVICES_DIR, name, SERVICES[name]["file"])

def svc_running(name):
    return port_open(SERVICES[name]["port"])

def cmd_list():
    print(f"\n🐾 Poke Labs Services ({len(SERVICES)} total)")
    print(f"{'Service':<25} {'Port':>6} {'Status':<10} {'Description'}")
    print("─" * 75)
    for name, info in sorted(SERVICES.items()):
        running = svc_running(name)
        status = "✅ running" if running else "⬛ stopped"
        exists = os.path.exists(svc_path(name))
        if not exists:
            status = "⬜ missing"
        print(f"{name:<25} {info['port']:>6} {status:<10} {info['desc']}")
    print()

def cmd_start(target):
    if target == "all":
        targets = [n for n in SERVICES if os.path.exists(svc_path(n))]
    elif target in SERVICES:
        targets = [target]
    else:
        print(f"Unknown service: {target}")
        print(f"Available: {', '.join(sorted(SERVICES.keys()))}")
        return

    os.makedirs(LOG_DIR, exist_ok=True)
    started = 0
    for name in targets:
        info = SERVICES[name]
        port = info["port"]
        fpath = svc_path(name)
        if not os.path.exists(fpath):
            print(f"  ⬜ {name}: file not found, skipping")
            continue
        # Kill existing
        os.system(f"fuser -k {port}/tcp 2>/dev/null")
        time.sleep(0.3)
        log = os.path.join(LOG_DIR, f"{name}.log")
        subprocess.Popen(
            ["python3", fpath],
            stdout=open(log, "w"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        time.sleep(0.5)
        if port_open(port):
            print(f"  ✅ {name} → :{port}")
            started += 1
        else:
            print(f"  ⚠ {name} → :{port} (may not have started)")
    if len(targets) > 1:
        print(f"\nStarted {started}/{len(targets)} services")

def cmd_stop(target):
    if target == "all":
        targets = list(SERVICES.keys())
    elif target in SERVICES:
        targets = [target]
    else:
        print(f"Unknown service: {target}")
        return
    for name in targets:
        port = SERVICES[name]["port"]
        os.system(f"fuser -k {port}/tcp 2>/dev/null")
        print(f"  ⬇ {name} (:{port})")

def cmd_restart(target):
    cmd_stop(target)
    time.sleep(1)
    cmd_start(target)

def cmd_status(target=None):
    if target:
        if target not in SERVICES:
            print(f"Unknown: {target}")
            return
        names = [target]
    else:
        names = sorted(SERVICES.keys())

    print(f"\n📊 Status {'(' + target + ')' if target else '(all)'}")
    for name in names:
        info = SERVICES[name]
        running = svc_running(name)
        status = "✅ running" if running else "⬛ stopped"
        exists = os.path.exists(svc_path(name))
        if not exists:
            status = "⬜ missing"
        print(f"  {name:<25} :{info['port']:>5}  {status}")
    print()

def cmd_logs(name):
    if name not in SERVICES:
        print(f"Unknown: {name}")
        return
    log = os.path.join(LOG_DIR, f"{name}.log")
    if not os.path.exists(log):
        print(f"No log file for {name} ({log})")
        return
    print(f"📄 Logs for {name} ({log}):")
    print("─" * 50)
    try:
        result = subprocess.run(["tail", "-30", log], capture_output=True, text=True)
        print(result.stdout)
    except:
        with open(log) as f:
            lines = f.readlines()
            print("".join(lines[-30:]))

def cmd_health():
    up = 0
    down = 0
    for name, info in SERVICES.items():
        if port_open(info["port"]):
            up += 1
        else:
            down += 1
    total = up + down
    pct = round(up/total*100, 1) if total else 0
    bar_len = 20
    filled = int(bar_len * up / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\n🏥 Poke Labs Health: [{bar}] {up}/{total} ({pct}%)")
    if down > 0:
        print("Down services:")
        for name, info in sorted(SERVICES.items()):
            if not port_open(info["port"]) and os.path.exists(svc_path(name)):
                print(f"  ✗ {name} (:{info['port']})")
    print()

def cmd_dashboard():
    port = SERVICES.get("health-aggregator", {}).get("port", 8799)
    url = f"http://localhost:{port}/"
    if port_open(port):
        print(f"🏥 Dashboard: {url}")
    else:
        print(f"Health Aggregator is not running. Start it:")
        print(f"  python3 {svc_path('health-aggregator')}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    arg = sys.argv[2] if len(sys.argv) > 2 else None

    cmds = {
        "list": cmd_list, "ls": cmd_list,
        "start": lambda: cmd_start(arg or "all"),
        "stop": lambda: cmd_stop(arg or "all"),
        "restart": lambda: cmd_restart(arg or "all"),
        "status": lambda: cmd_status(arg),
        "st": lambda: cmd_status(arg),
        "logs": lambda: cmd_logs(arg) if arg else print("Usage: poke logs <name>"),
        "health": cmd_health, "he": cmd_health,
        "dashboard": cmd_dashboard, "dash": cmd_dashboard,
    }

    if cmd in cmds:
        cmds[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(sorted(set(cmds.keys())))}")

if __name__ == "__main__":
    main()
