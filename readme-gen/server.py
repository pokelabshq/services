#!/usr/bin/env python3
"""GitHub README Generator v1.0 — Auto-generate beautiful README.md for any repo."""
import http.server, json, urllib.request, os, sys

PORT = int(os.environ.get("PORT", 8780))

TEMPLATE = """# {name}

{description}

## Features

{features}

## Quick Start

```bash
{install}
```

## Installation

```bash
pip install {name_lower}
```

## Tech Stack

{tech_stack}

## License

MIT License.

---

Built by [{org}](https://github.com/{org})
"""

def generate_readme(data):
    name = data.get("name", "my-project")
    desc = data.get("description", "A cool project.")
    features = data.get("features", ["Fast", "Simple", "Open source"])
    install = data.get("install", "pip install " + name.lower())
    org = data.get("org", "pokelabshq")
    tech = data.get("tech_stack", ["Python 3.10+", "Zero dependencies"])
    features_md = "\\n".join(f"- {f}" for f in features)
    tech_md = "\\n".join(f"- {t}" for t in tech)
    return TEMPLATE.format(name=name, description=desc, features=features_md, install=install, name_lower=name.lower(), org=org, tech_stack=tech_md)

def fetch_repo_info(owner, repo):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        return {"name": data.get("name", repo), "description": data.get("description", ""), "org": owner, "language": data.get("language", "Python")}
    except:
        return {"name": repo, "description": "A project.", "org": owner}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html("<h1>README Generator v1.0</h1><p>POST to /api/generate with JSON body</p><p>GET /api/health for status</p>")
        elif self.path == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            owner = body.get("owner", "")
            repo = body.get("repo", "")
            if owner and repo:
                info = fetch_repo_info(owner, repo)
                info.update(body)
            else:
                info = body
            readme = generate_readme(info)
            self.send_json({"readme": readme, "chars": len(readme)})
        else:
            self.send_json({"error": "not found"}, 404)

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"README Generator v1.0 on port {PORT}")
    with http.server.HTTPServer(("", PORT), Handler) as s:
        s.serve_forever()
