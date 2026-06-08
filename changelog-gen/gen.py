#!/usr/bin/env python3
"""Poke Labs Changelog Generator — Reads git history and generates CHANGELOG.md"""
import subprocess, re, os, sys, datetime

def run(cmd):
    return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()

def get_tags():
    try:
        return run("git tag --sort=-version:refname").split("\n")
    except:
        return []

def get_commits(since_tag=None):
    fmt = "%H|%s|%b|%aI|%an"
    cmd = f"git log --pretty=format:'{fmt}'"
    if since_tag:
        cmd += f" {since_tag}..HEAD"
    try:
        output = run(cmd)
        commits = []
        for line in output.split("\n"):
            if "|" not in line:
                continue
            parts = line.split("|", 4)
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0][:8],
                    "subject": parts[1],
                    "body": parts[2] if len(parts) > 2 else "",
                    "date": parts[3][:10] if len(parts) > 3 else "",
                    "author": parts[4] if len(parts) > 4 else "unknown"
                })
        return commits
    except:
        return []

def categorize(subject):
    s = subject.lower()
    if s.startswith("feat") or s.startswith("feature") or s.startswith("add"):
        return "added"
    elif s.startswith("fix") or s.startswith("bugfix") or s.startswith("hotfix"):
        return "fixed"
    elif s.startswith("break") or s.startswith("breaking"):
        return "breaking"
    elif s.startswith("deprecat"):
        return "deprecated"
    elif s.startswith("remov") or s.startswith("delet"):
        return "removed"
    elif s.startswith("secur") or s.startswith("vuln"):
        return "security"
    elif s.startswith("perf") or s.startswith("optim"):
        return "performance"
    elif s.startswith("refactor") or s.startswith("restruct"):
        return "changed"
    elif s.startswith("doc"):
        return "docs"
    elif s.startswith("test"):
        return "tests"
    elif s.startswith("chore") or s.startswith("ci") or s.startswith("build"):
        return "chore"
    return "changed"

def clean_subject(subject):
    prefixes = ["feat:", "feat(", "fix:", "fix(", "docs:", "test:", "chore:", "ci:",
                "build:", "refactor:", "perf:", "style:", "breaking:", "deprecate:",
                "remove:", "security:", "add:", "update:", "remove:", "delete:"]
    s = subject.strip()
    for p in prefixes:
        if s.lower().startswith(p):
            s = s[len(p):].strip()
    # Remove scope like (service-name)
    s = re.sub(r'\([^)]+\)\s*', '', s)
    return s[0].upper() + s[1:] if s else subject

def generate_changelog():
    tags = get_tags()
    commits = get_commits()
    
    if not commits:
        return "# Changelog\n\nNo commits found.\n"
    
    # Group by category
    categories = {}
    for c in commits:
        cat = categorize(c["subject"])
        cleaned = clean_subject(c["subject"])
        entry = f"- {cleaned} ({c['hash']})"
        if c["author"] != "unknown":
            entry += f" — {c['author']}"
        categories.setdefault(cat, []).append(entry)
    
    # Build output
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Changelog\n", f"## [{today}] — Unreleased\n"]
    
    order = ["breaking", "added", "changed", "deprecated", "removed", "fixed", "security", "performance", "docs", "tests", "chore"]
    labels = {
        "breaking": "⚠️ Breaking Changes",
        "added": "✨ Added",
        "changed": "🔄 Changed",
        "deprecated": "🚫 Deprecated",
        "removed": "🗑️ Removed",
        "fixed": "🐛 Fixed",
        "security": "🔒 Security",
        "performance": "⚡ Performance",
        "docs": "📝 Documentation",
        "tests": "✅ Tests",
        "chore": "🔧 Chores"
    }
    
    for cat in order:
        if cat in categories:
            lines.append(f"### {labels.get(cat, cat)}\n")
            for entry in categories[cat]:
                lines.append(entry)
            lines.append("")
    
    # Add previous versions if tags exist
    if tags:
        lines.append("---\n")
        lines.append("## Previous Versions\n")
        for tag in tags[:5]:
            tag_commits = get_commits(tag)
            if tag_commits:
                lines.append(f"### {tag}\n")
                for c in tag_commits[:10]:
                    lines.append(f"- {clean_subject(c['subject'])} ({c['hash']})")
                lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(repo)
    changelog = generate_changelog()
    out = os.path.join(repo, "CHANGELOG.md")
    with open(out, "w") as f:
        f.write(changelog)
    print(f"Generated {out} with {changelog.count('- ')} entries")
