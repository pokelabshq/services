#!/usr/bin/env python3
"""
Skill Market CLI v1.0 — List, search, and install skills from Poke Labs.
Pure Python stdlib. Zero deps.

Usage:
  python3 skill-market-cli/cli.py list
  python3 skill-market-cli/cli.py search <query>
  python3 skill-market-cli/cli.py install <skill-name>
  python3 skill-market-cli/cli.py info <skill-name>
"""
import sys, json, os, shutil

SKILLS_DIR = os.path.expanduser("~/.automaton/skills")

SKILLS = {
    "auto-merge-pr": {"desc": "Auto-merge Dependabot PRs", "category": "github", "tags": ["github", "automation"]},
    "council": {"desc": "AI Council automation", "category": "automation", "tags": ["github", "automation"]},
    "daily-digest": {"desc": "Daily Digest Generator", "category": "automation", "tags": ["automation", "reporting"]},
    "github-reply-bot": {"desc": "GitHub Auto-Reply Bot", "category": "github", "tags": ["github", "webhook"]},
    "link-preview": {"desc": "Link Preview API", "category": "api", "tags": ["api", "metadata"]},
    "poke-hub": {"desc": "All-in-One GitHub Bot", "category": "github", "tags": ["github", "automation"]},
    "poke-bot": {"desc": "GitHub Auto-Triage Bot", "category": "github", "tags": ["github", "triage"]},
    "webhook-tester": {"desc": "Webhook Tester", "category": "devtools", "tags": ["devtools", "webhooks"]},
    "deploy-manager": {"desc": "Deploy Manager", "category": "ops", "tags": ["ops", "deployment"]},
    "billing": {"desc": "x402 Billing Middleware", "category": "api", "tags": ["api", "payments"]},
    "color-api": {"desc": "Color conversion API", "category": "api", "tags": ["api", "colors"]},
    "hash-gen": {"desc": "Hash Generator", "category": "api", "tags": ["api", "crypto"]},
    "uuid-gen": {"desc": "UUID Generator", "category": "api", "tags": ["api", "utils"]},
}

def cmd_list(args):
    print("
  Poke Labs Skill Marketplace")
    print("  " + "=" * 40)
    cats = {}
    for name, s in sorted(SKILLS.items()):
        cats.setdefault(s["category"], []).append((name, s))
    for cat, items in sorted(cats.items()):
        print(f"
  [{cat.upper()}]")
        for name, s in items:
            print(f"    {name} — {s['desc']}")
    print(f"
  Total: {len(SKILLS)} skills")

def cmd_search(args):
    if not args:
        print("Usage: search <query>"); return
    q = " ".join(args).lower()
    for name, s in SKILLS.items():
        if q in name.lower() or q in s["desc"].lower() or any(q in t for t in s.get("tags", [])):
            print(f"  {name} — {s['desc']}")

def cmd_install(args):
    if not args:
        print("Usage: install <skill-name>"); return
    name = args[0]
    if name not in SKILLS:
        print(f"Unknown: {name}"); return
    skill = SKILLS[name]
    dest = os.path.join(SKILLS_DIR, name)
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "SKILL.md"), "w") as f:
        f.write(f"# {name}

{skill['desc']}

Category: {skill['category']}
Tags: {', '.join(skill.get('tags', []))}
")
    print(f"  Installed: {name} -> {dest}")

def cmd_info(args):
    if not args:
        print("Usage: info <skill-name>"); return
    name = args[0]
    if name not in SKILLS:
        print(f"Unknown: {name}"); return
    s = SKILLS[name]
    print(f"
  {name}
  Description: {s['desc']}
  Category: {s['category']}
  Tags: {', '.join(s.get('tags', []))}")

CMDS = {"list": cmd_list, "search": cmd_search, "install": cmd_install, "info": cmd_info}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in CMDS:
        print("Skill Market CLI v1.0 — Poke Labs")
        print("Commands: list | search <query> | install <name> | info <name>")
        sys.exit(1)
    CMDS[args[0]](args[1:])
