#!/usr/bin/env python3
"""Skills Index Generator v1.0 — Scans and indexes all Poke Labs skills.
Generates skills-index.json and serves it via API. Port: 8782. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, html as h, os, re

PORT = 8782
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
SKILLS_DIRS = ["/home/alx/skills", "/home/alx/.config/automaton/skills"]
GITHUB_ORG = "pokelabshq"
_cache = {"ts": 0, "data": None}
CACHE_TTL = 60

def scan_skills_dirs():
    skills = []
    for d in SKILLS_DIRS:
        if not os.path.isdir(d):
            continue
        for entry in sorted(os.listdir(d)):
            skill_path = os.path.join(d, entry)
            md_path = os.path.join(skill_path, "SKILL.md")
            if os.path.isdir(skill_path) and os.path.isfile(md_path):
                info = {"name": entry, "path": skill_path}
                try:
                    with open(md_path) as f:
                        content = f.read(2048)
                    # Extract first heading as title
                    m = re.search(r'^#\s+(.+)', content, re.M)
                    if m:
                        info["title"] = m.group(1).strip()
                    # Extract description (first non-heading paragraph)
                    paras = re.findall(r'\n\n([^\n#].+?)(?:\n\n|\Z)', content, re.S)
                    if paras:
                        info["description"] = paras[0].strip()[:200].replace('\n', ' ')
                    # Check for Python files
                    py_files = [f for f in os.listdir(skill_path) if f.endswith('.py')]
                    info["python_files"] = py_files
                    info["has_scripts"] = len(py_files) > 0
                except:
                    pass
                skills.append(info)
    return skills

def fetch_github_skills():
    """Fetch skill-related repos from GitHub org."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "PokeSkills/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        url = f"https://api.github.com/orgs/{GITHUB_ORG}/repos?per_page=100"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos = json.loads(resp.read().decode())
        return [{"name": r["name"], "desc": (r.get("description") or "")[:120],
                 "url": r.get("html_url", ""), "topics": r.get("topics", []),
                 "stars": r.get("stargazers_count", 0), "updated": r.get("updated_at", "")}
                for r in sorted(repos, key=lambda x: x.get("updated_at", ""), reverse=True)]
    except:
        return []

def build_index():
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]
    local_skills = scan_skills_dirs()
    github_repos = fetch_github_skills()
    data = {
        "generated": now, "local_skills": local_skills,
        "local_count": len(local_skills), "github_repos": github_repos,
        "github_count": len(github_repos), "wallet": WALLET
    }
    # Write index to disk
    try:
        with open("/home/alx/services/skills-index/skills-index.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
    except:
        pass
    _cache["data"] = data; _cache["ts"] = now
    return data

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self.json({"ok": True, "v": 1, "port": PORT, "wallet": WALLET})
        elif p.path in ("/api/skills", "/api/index"):
            d = build_index()
            self.json({"ok": True, **d})
        elif p.path == "/api/skills.json":
            # Raw redirect to the file
            d = build_index()
            self.json(d)
        elif p.path in ("/", "/dashboard"):
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        d = build_index()
        skills = d.get("local_skills", [])
        repos = d.get("github_repos", [])
        skill_rows = ""
        for s in skills:
            scripts = ", ".join(s.get("python_files", [])) or "—"
            desc = h.escape(s.get("description", "")[:80])
            skill_rows += f'<tr><td><strong>{h.escape(s["name"])}</strong></td><td>{desc}</td><td><code>{h.escape(scripts)}</code></td></tr>'
        repo_rows = ""
        for r in repos[:20]:
            url = h.escape(r["url"])
            name = h.escape(r["name"])
            desc = h.escape(r["desc"][:60])
            stars = r.get("stars", 0)
            topics = ", ".join(r.get("topics", [])[:3])
            repo_rows += f'<tr><td><a href="{url}">{name}</a></td><td>{desc}</td><td>⭐{stars}</td><td><code>{h.escape(topics)}</code></td></tr>'
        gen = time.strftime('%H:%M UTC', time.gmtime(d.get('generated', 0)))
        s = f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Skills Index — Poke Labs</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}.hd{{padding:40px 20px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(0,255,170,0.08) 0%,transparent 60%)}}h1{{font-size:1.8rem;color:#00ffaa}}h2{{color:#00ffaa;font-size:1.1rem;margin:30px 0 10px;padding:0 20px}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;max-width:700px;margin:0 auto;padding:20px}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;text-align:center}}.n{{font-size:1.8rem;font-weight:700;color:#00ffaa}}.l{{color:#666;font-size:.75rem}}table{{width:100%;max-width:900px;margin:0 auto;border-collapse:collapse;padding:0 20px 20px}}th{{text-align:left;padding:8px;color:#555;font-size:.7rem;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.05)}}td{{padding:8px;border-bottom:1px solid rgba(255,255,255,0.02);font-size:.8rem}}tr:hover td{{background:rgba(255,255,255,0.01)}}a{{color:#00ffaa;text-decoration:none}}code{{background:rgba(255,255,255,0.05);padding:2px 6px;border-radius:3px;font-size:.7rem}}.ft{{text-align:center;padding:20px;color:#444;font-size:.7rem}}</style></head><body><div class="hd"><h1>📚 Skills Index — Poke Labs</h1><p style="color:#666;font-size:.8rem">{d.get("local_count", 0)} local skills · {d.get("github_count", 0)} GitHub repos · Generated {gen}</p></div><div class="g"><div class="c"><div class="n">{d.get("local_count",0)}</div><div class="l">Local Skills</div></div><div class="c"><div class="n">{d.get("github_count",0)}</div><div class="l">GitHub Repos</div></div></div><h2>Installed Skills</h2><table><thead><tr><th>Name</th><th>Description</th><th>Scripts</th></tr></thead><tbody>{skill_rows or "<tr><td colspan=3 style=color:#444>No skills found</td></tr>"}</tbody></table>><h2>GitHub Repos (pokelabshq)</h2><table><thead><tr><th>Repo</th><th>Description</th><th>Stars</th><th>Topics</th></tr></thead><tbody>{repo_rows or "<tr><td colspan=4 style=color:#444>Unable to fetch</td></tr>"}</tbody></table><div class="ft">🐾 Skills Index Generator v1.0 · MIT · Port {PORT}</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Skills Index Generator v1.0 on :{PORT}");s.serve_forever()
