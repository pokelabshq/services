#!/usr/bin/env python3
"""Generate a health scorecard for a GitHub repository.
Usage: python3 repo-scorecard.py owner/repo"""
import json, sys
from urllib.request import urlopen, Request

def score(repo):
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "PokeScore/1.0"}
    
    # Get repo info
    r = urlopen(Request(f"https://api.github.com/repos/{repo}", headers=h), timeout=10)
    data = json.loads(r.read())
    
    # Get open issues and PRs
    r = urlopen(Request(f"https://api.github.com/repos/{repo}/issues?state=open&per_page=1", headers=h), timeout=10)
    link = r.headers.get('Link', '')
    open_issues = int(link.split('page=')[-1].split('>')[0]) if 'last' in link else 1
    
    # Get recent commits (last 30 days)
    r = urlopen(Request(f"https://api.github.com/repos/{repo}/stats/commit_activity", headers=h), timeout=10)
    commits = json.loads(r.read())
    recent_commits = sum(c['total'] for c in commits[-4:]) if commits else 0
    
    # Calculate score
    score = 100
    score -= min(open_issues * 2, 30)  # -2 per issue, max -30
    score -= 10 if not data.get('has_wiki') else 0
    score -= 10 if data.get('open_issues_count', 0) > 20 else 0
    score += min(recent_commits, 20)  # +1 per recent commit, max +20
    score = max(0, min(100, score))
    
    # Grade
    grade = 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F'
    
    print(f"📊 Repository Health Scorecard: {repo}")
    print(f"{'='*50}")
    print(f"  Grade: {grade} ({score}/100)")
    print(f"  Stars: ⭐ {data.get('stargazers_count', 0)}")
    print(f"  Forks: 🍴 {data.get('forks_count', 0)}")
    print(f"  Open Issues: 🐛 {data.get('open_issues_count', 0)}")
    print(f"  Recent Commits (30d): 📝 {recent_commits}")
    print(f"  Default Branch: {data.get('default_branch', 'main')}")
    print(f"  Language: {data.get('language', 'Unknown')}")
    print(f"  Updated: {data.get('updated_at', 'Unknown')}")
    print(f"{'='*50}")
    
    # Recommendations
    if open_issues > 10:
        print(f"  ⚠️  High issue count — consider triaging")
    if recent_commits == 0:
        print(f"  ⚠️  No recent commits — repo may be inactive")
    if data.get('open_issues_count', 0) > 20:
        print(f"  ⚠️  Backlog growing — prioritize bug fixes")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        score(sys.argv[1])
    else:
        score("pokelabshq/council")
