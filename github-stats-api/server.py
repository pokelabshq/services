#!/usr/bin/env python3
"""GitHub Stats API v1.0 — Serves cached repository statistics for pokelabshq. Port: 8779. Zero deps."""
import http.server, json, time, urllib.request, urllib.parse, html as h, os

PORT = 8779
WALLET = "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
ORG = "pokelabshq"
CACHE_TTL = 300
_cache = {"ts": 0, "data": None}

def fetch_repos():
    if _cache["data"] and time.time() - _cache["ts"] < CACHE_TTL:
        return _cache["data"]
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "PokeStats/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100&sort=updated"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos = json.loads(resp.read().decode())
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        total_forks = sum(r.get("forks_count", 0) for r in repos)
        total_issues = sum(r.get("open_issues_count", 0) for r in repos)
        langs = {}
        for r in repos:
            lang = r.get("language") or "Unknown"
            langs[lang] = langs.get(lang, 0) + 1
        data = {
            "org": ORG, "total_repos": len(repos),
            "stars": total_stars, "forks": total_forks,
            "open_issues": total_issues,
            "languages": dict(sorted(langs.items(), key=lambda x: x[1], reverse=True)),
            "repos": [{"name": r["name"], "desc": (r.get("description") or "")[:80],
                       "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0),
                       "lang": r.get("language", "?"), "updated": r.get("updated_at", ""),
                       "url": r.get("html_url", "")} for r in repos],
            "cached_at": time.time()
        }
        _cache["data"] = data; _cache["ts"] = time.time()
        return data
    except Exception as e:
        return {"error": str(e), "cached": _cache["data"]}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/api/health":
            self.json({"ok": True, "v": 1, "port": PORT, "wallet": WALLET})
        elif p.path == "/api/stats":
            self.json({"ok": True, **fetch_repos()})
        elif p.path in ("/", "/dashboard"):
            self.dashboard()
        else:
            self.json({"error": "Not found"}, 404)

    def dashboard(self):
        d = fetch_repos()
        if "error" in d and not d.get("cached"):
            self.json({"error": d["error"]}, 500); return
        rows = ""
        for r in d.get("repos", []):
            url_esc = h.escape(r['url'])
            name_esc = h.escape(r['name'])
            lang_esc = h.escape(str(r['lang']))
            upd_esc = h.escape(r['updated'][:10])
            rows += f'<tr><td><a href="{url_esc}">{name_esc}</a></td><td>{r["stars"]}</td><td>{r["forks"]}</td><td>{lang_esc}</td><td style="color:#555;font-size:.7rem">{upd_esc}</td></tr>'
        _total = d.get('total_repos', 0)
        _stars = d.get('stars', 0)
        _forks = d.get('forks', 0)
        _issues = d.get('open_issues', 0)
        _cached = time.strftime('%H:%M UTC', time.gmtime(d.get('cached_at', 0)))
        s = f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>GitHub Stats — {ORG}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,sans-serif;background:#0a0a1a;color:#e0e0e2;line-height:1.6}}.hd{{padding:40px 20px;text-align:center;background:radial-gradient(ellipse at 50% 0%,rgba(0,255,170,0.08) 0%,transparent 60%)}}h1{{font-size:1.8rem;color:#00ffaa}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;max-width:700px;margin:0 auto;padding:20px}}.c{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:16px;text-align:center}}.n{{font-size:1.8rem;font-weight:700;color:#00ffaa}}.l{{color:#666;font-size:.75rem}}table{{width:100%;max-width:800px;margin:0 auto;border-collapse:collapse;padding:0 20px 40px}}th{{text-align:left;padding:8px;color:#555;font-size:.7rem;text-transform:uppercase;border-bottom:1px solid rgba(255,255,255,0.05)}}td{{padding:8px;border-bottom:1px solid rgba(255,255,255,0.02);font-size:.8rem}}tr:hover td{{background:rgba(255,255,255,0.01)}}a{{color:#00ffaa;text-decoration:none}}a:hover{{text-decoration:underline}}.ft{{text-align:center;padding:20px;color:#444;font-size:.7rem}}</style></head><body><div class="hd"><h1>📊 GitHub Stats — {ORG}</h1><p style="color:#666;font-size:.8rem;margin-top:4px">{_total} repos · Updated {_cached}</p></div><div class="g"><div class="c"><div class="n">{_total}</div><div class="l">Repos</div></div><div class="c"><div class="n">{_stars}</div><div class="l">⭐ Stars</div></div><div class="c"><div class="n">{_forks}</div><div class="l">🍴 Forks</div></div><div class="c"><div class="n">{_issues}</div><div class="l">🐛 Open Issues</div></div></div><table><thead><tr><th>Repo</th><th>Stars</th><th>Forks</th><th>Lang</th><th>Updated</th></tr></thead><tbody>{rows}</tbody></table><div class="ft">🐾 Poke Labs GitHub Stats API v1.0 · MIT · Port {PORT}</div></body></html>'
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(s.encode())

    def json(self, d, code=200):
        body = json.dumps(d, default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(body)))
        self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"GitHub Stats API v1.0 on :{PORT}");s.serve_forever()
