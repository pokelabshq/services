#!/usr/bin/env python3
"""Poke Labs Package Registry v1 — Minimal package publishing & discovery"""
import http.server, json, time, os, urllib.parse, re

PORT = 8785
DATA_DIR = "/tmp/poke-registry"
REGISTRY_FILE = f"{DATA_DIR}/registry.json"

os.makedirs(DATA_DIR, exist_ok=True)

def load_registry():
    try:
        with open(REGISTRY_FILE) as f: return json.load(f)
    except: return {"packages": {}, "stats": {"total_publishes": 0, "total_downloads": 0}}

def save_registry(reg):
    with open(REGISTRY_FILE, "w") as f: json.dump(reg, f, indent=2)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        reg = load_registry()
        if p.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "packages": len(reg["packages"]), "stats": reg["stats"]})
        elif p.path == "/api/search":
            q = urllib.parse.parse_qs(p.query).get("q", [""])[0].lower()
            results = [{"name": k, "description": v.get("description", ""), "latest": v.get("latest", "?"), "downloads": v.get("downloads", 0)}
                       for k, v in reg["packages"].items() if q in k or q in v.get("description", "").lower()]
            self.send_json({"results": results, "total": len(results)})
        elif p.path.startswith("/api/packages/"):
            name = p.path.split("/")[-1]
            if name in reg["packages"]:
                pkg = reg["packages"][name]
                self.send_json({"name": name, "description": pkg.get("description", ""), "latest": pkg.get("latest", "0.0.0"),
                                "versions": pkg.get("versions", []), "downloads": pkg.get("downloads", 0)})
            else:
                self.send_json({"error": "not found", "available": list(reg["packages"].keys())}, 404)
        elif p.path == "/":
            self.send_html(self.landing(reg))
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        reg = load_registry()

        if self.path == "/api/publish":
            name = body.get("name", "").strip().lower()
            version = body.get("version", "").strip()
            description = body.get("description", "")
            author = body.get("author", "anonymous")

            if not re.match(r'^[a-z0-9_-]+$', name):
                self.send_json({"error": "Invalid name"}, 400); return
            if not re.match(r'^\d+\.\d+\.\d+', version):
                self.send_json({"error": "Use semver (1.0.0)"}, 400); return

            if name not in reg["packages"]:
                reg["packages"][name] = {"description": "", "latest": "0.0.0", "versions": [], "downloads": 0}

            pkg = reg["packages"][name]
            existing = [v["version"] for v in pkg.get("versions", [])]
            if version not in existing:
                pkg.setdefault("versions", []).append({"version": version, "published": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "author": author})
            pkg["latest"] = version
            if description: pkg["description"] = description

            reg["stats"]["total_publishes"] = reg["stats"].get("total_publishes", 0) + 1
            save_registry(reg)
            self.send_json({"ok": True, "published": f"{name}@{version}"})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        for h, v in [("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Methods", "GET,POST,OPTIONS"), ("Access-Control-Allow-Headers", "Content-Type")]:
            self.send_header(h, v)
        self.end_headers()

    def send_json(self, d, code=200):
        self.send_response(code)
        for h, v in [("Content-Type", "application/json"), ("Access-Control-Allow-Origin", "*")]:
            self.send_header(h, v)
        self.end_headers()
        self.wfile.write(json.dumps(d, indent=2).encode())

    def landing(self, reg):
        pkgs = "".join(f"<li><code>{p}</code> — {v.get('latest','?')}</li>" for p, v in list(reg["packages"].items())[:10])
        return f"""<!DOCTYPE html><html><head><title>Poke Labs Registry</title>
<style>body{{font-family:system-ui;max-width:650px;margin:3rem auto;padding:1rem;color:#ddd;background:#0a0a1a}}
h1{{color:#a78bfa}}code{{background:#222;padding:.15rem .4rem;border-radius:4px}}
pre{{background:#111;padding:1rem;border-radius:8px;overflow:auto}}</style></head><body>
<h1>📦 Poke Labs Package Registry</h1>
<p>Publish, discover, and version packages for the Poke Labs ecosystem.</p>
<h2>Publish</h2>
<pre>curl -X POST http://localhost:{PORT}/api/publish \\
  -H "Content-Type: application/json" \\
  -d '{{"name":"poke-cli","version":"1.0.0","description":"Poke Labs CLI","author":"Poke"}}'</pre>
<h2>Search</h2>
<pre>curl http://localhost:{PORT}/api/search?q=poke</pre>
<h2>Packages ({len(reg["packages"])})</h2>
<ul>{pkgs or '<li><em>No packages yet. Be first!</em></li>'}</ul>
</body></html>"""

    def log_message(self, *a): pass

if __name__ == "__main__":
    import subprocess, time as t
    subprocess.run(["fuser", "-k", f"{PORT}/tcp"], capture_output=True)
    t.sleep(1)
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Poke Labs Registry v1 on :{PORT}")
    s.serve_forever()
