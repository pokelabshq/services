#!/usr/bin/env python3
"""Daily Briefing Generator for Poke Labs.
Generates a morning status report: GitHub health, service status, credit usage.
Outputs formatted text ready for Telegram or console.
Zero dependencies. stdlib only."""
import json, urllib.request, urllib.parse, os, time

GH_USER = "pokelabshq"
SERVICES = [
    ("Link Preview", "http://localhost:8765/api/health"),
    ("Poke Labs Site", "http://localhost:8766/api/health"),
    ("Poke Bot", "http://localhost:8770/"),
    ("Telegram Bot", "http://localhost:8777/api/health"),
    ("Skills Hub", "http://localhost:8780/api/health"),
    ("Skills Marketplace", "http://localhost:8781/api/health"),
    ("Package Registry", "http://localhost:8785/api/health"),
    ("Pricing API", "http://localhost:8790/api/health"),
    ("Billing Engine", "http://localhost:8795/api/health"),
]

def gh_api(path):
    url = f"https://api.github.com/{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def check_service(name, url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            ver = data.get("v", "?")
            return f"✅ {name} (v{ver})"
    except:
        return f"❌ {name} (down)"

def get_repos():
    data = gh_api(f"users/{GH_USER}/repos?sort=updated&per_page=10")
    if not data:
        return "GitHub API unreachable"
    lines = []
    for r in data[:5]:
        lang = r.get("language", "?")
        updated = r.get("updated_at", "?")[:10]
        lines.append(f"  📦 {r['name']} ({lang}) — updated {updated}")
    return "\n".join(lines)

def get_issues():
    data = gh_api(f"repos/{GH_USER}/council/issues?state=open&per_page=5")
    if not data:
        return "  No open issues"
    lines = []
    for i in data:
        labels = ", ".join(l["name"] for l in i.get("labels", []))
        lines.append(f"  #{i['number']} {i['title']} [{labels}]")
    return "\n".join(lines) if lines else "  No open issues"

def generate():
    now = time.strftime("%A, %B %d, %Y — %I:%M %p UTC", time.gmtime())
    lines = [
        f"🐾 **Poke Labs Daily Briefing**",
        f"📅 {now}",
        "",
        "**📊 GitHub Repos:**",
        get_repos(),
        "",
        "**🔴 Open Issues (council):**",
        get_issues(),
        "",
        "**🖥️ Service Status:**",
    ]
    for name, url in SERVICES:
        lines.append(f"  {check_service(name, url)}")
    lines.extend([
        "",
        "**💰 Credits:** Conway credits need funding. USDC wallet empty.",
        "",
        "🐾 Poke Labs — Built by Alexander (13, Toronto)",
    ])
    return "\n".join(lines)

if __name__ == "__main__":
    print(generate())
