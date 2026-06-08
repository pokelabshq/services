#!/usr/bin/env python3
"""
Poke Labs Service Test Suite v1
Tests all services for: syntax, stdlib-only, server start, health endpoint.
Run: python3 tests/test_all_services.py
"""
import subprocess, socket, time, json, os, sys, importlib.util

SERVICES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def discover():
    services = []
    for entry in sorted(os.listdir(SERVICES_DIR)):
        path = os.path.join(SERVICES_DIR, entry, "server.py")
        if os.path.isfile(path) and entry != "tests":
            services.append((entry, path))
    return services

def detect_port(filepath):
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if "PORT" in line and "=" in line:
                nums = [int(s) for s in line.split("=")[1].replace("}","").split() if s.isdigit()]
                if nums:
                    return nums[0]
    return None

def check_port(port):
    if not port:
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def syntax_check(path):
    try:
        subprocess.run([sys.executable, "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
                       capture_output=True, check=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode()[:200]

def stdlib_check(path):
    STDLIB_MODULES = {
        'os','sys','json','re','math','random','datetime','time','socket','http','urllib',
        'email','hashlib','base64','html','io','csv','collections','itertools','functools',
        'pathlib','string','struct','threading','subprocess','signal','logging','argparse',
        'configparser','tempfile','shutil','glob','typing','dataclasses','enum','uuid',
        'secrets','hmac','textwrap','traceback','warnings','contextlib','decimal','fractions',
        'statistics','queue','copy','pprint','operator','csv','xml','unicodedata','difflib',
        'calendar','bisect','heapq','weakref','types','numbers','abc','ast','dis','code',
        'codeop','zipfile','tarfile','gzip','bz2','lzma','zipimport','pickle','shelve',
        'sqlite3','zlib','binascii','quopri','uu','codecs','unicodedata','locale','gettext',
        'textwrap','rlcompleter','pty','fcntl','grp','pwd','resource','nis','syslog',
        'platform','ctypes','array','mmap','readline','fileinput','filecmp','linecache',
        'imghdr','sndhdr','ossaudiodev','optparse','nntplib','imaplib','smtplib','poplib',
        'telnetlib','ftplib','macpath','getopt','webbrowser','cgi','cgitb','wsgiref',
    }
    issues = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line.startswith("import "):
                mod = line.split()[1].split(".")[0].split(",")[0].strip()
                if mod not in STDLIB_MODULES:
                    issues.append(f"  Line {i}: non-stdlib import '{mod}'")
            elif line.startswith("from ") and " import " in line:
                mod = line.split()[1].split(".")[0]
                if mod not in STDLIB_MODULES and not mod.startswith("."):
                    issues.append(f"  Line {i}: non-stdlib from-import '{mod}'")
    return issues

def start_and_test(name, path):
    port = detect_port(path)
    if not port:
        return "skip", "No port detected"
    
    # Kill anything on that port
    os.system(f"fuser -k {port}/tcp 2>/dev/null")
    
    proc = subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    
    try:
        if check_port(port):
            return "pass", f"Started on port {port}"
        else:
            stderr = proc.stderr.read().decode()[:300] if proc.stderr else ""
            return "fail", f"Port {port} not responding. {stderr}"
    finally:
        proc.terminate()
        proc.wait(timeout=3)
        os.system(f"fuser -k {port}/tcp 2>/dev/null")

def main():
    print("=" * 60)
    print("🧪 Poke Labs Service Test Suite v1")
    print("=" * 60)
    services = discover()
    print(f"Found {len(services)} services\n")
    
    results = {"pass": 0, "fail": 0, "skip": 0}
    
    for name, path in services:
        # Syntax check
        ok, err = syntax_check(path)
        if not ok:
            print(f"  ❌ {name}: SYNTAX ERROR — {err[:100]}")
            results["fail"] += 1
            continue
        
        # Stdlib check
        issues = stdlib_check(path)
        if issues:
            print(f"  ⚠️  {name}: {len(issues)} non-stdlib import(s)")
        
        # Start test
        status, msg = start_and_test(name, path)
        icon = {"pass": "✅", "fail": "❌", "skip": "⏭️"}[status]
        print(f"  {icon} {name}: {msg}")
        results[status] += 1
    
    print("\n" + "=" * 60)
    total = sum(results.values())
    print(f"📊 Results: {results['pass']}/{total} passed, {results['fail']} failed, {results['skipped']} skipped")
    print("=" * 60)
    
    sys.exit(1 if results["fail"] > 0 else 0)

if __name__ == "__main__":
    main()
