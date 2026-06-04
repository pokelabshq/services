#!/usr/bin/env python3
"""Poke Feed — RSS/Atom feed generator for Poke Labs GitHub activity.

Aggregates commits, PRs, and releases from all pokelabshq repos into a single feed.

Usage:
    python3 feed.py                  # Start server on port 8771
    python3 feed.py --generate       # Generate static feed.xml to stdout

Endpoints:
    GET /           — HTML landing page
    GET /feed.xml   — RSS 2.0 feed
    GET /atom.xml   — Atom feed
    GET /api/health — Health check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from xml.sax.saxutils import escape as xml_escape

PORT = 8771
GITHUB_API = "https://api.github.com"
ORG = "pokelabshq"
REPOS: list[str] = [
    "services",
    "council",
    "poke",
    "cli",
    "brand",
]

CACHE_TTL = 300  # 5 minutes
_cache: dict = {"data": None, "fetched": 0}


def fetch_json(url: str) -> dict | list:
    """Fetch JSON from GitHub API."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "poke-feed/1.0",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get_feed_data() -> list[dict]:
    """Fetch recent activity from all repos, return sorted list of events."""
    now = datetime.now(timezone.utc).timestamp()
    if _cache["data"] and (now - _cache["fetched"]) < CACHE_TTL:
        return _cache["data"]

    events: list[dict] = []
    for repo in REPOS:
        try:
            # Recent commits
            commits = fetch_json(f"{GITHUB_API}/repos/{ORG}/{repo}/commits?per_page=5")
            for c in commits:
                events.append({
                    "type": "commit",
                    "repo": repo,
                    "title": c["commit"]["message"].split("\n")[0][:120],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                    "url": c["html_url"],
                })
        except Exception:
            pass

        try:
            # Recent PRs
            prs = fetch_json(f"{GITHUB_API}/repos/{ORG}/{repo}/pulls?state=all&per_page=5&sort=updated")
            for pr in prs:
                events.append({
                    "type": "pull_request",
                    "repo": repo,
                    "title": f"PR #{pr['number']}: {pr['title'][:100]}",
                    "author": pr["user"]["login"],
                    "date": pr["updated_at"],
                    "url": pr["html_url"],
                })
        except Exception:
            pass

        try:
            # Recent releases
            releases = fetch_json(f"{GITHUB_API}/repos/{ORG}/{repo}/releases?per_page=3")
            for r in releases:
                events.append({
                    "type": "release",
                    "repo": repo,
                    "title": f"Release: {r['tag_name']} — {r['name'] or ''}",
                    "author": r["author"]["login"],
                    "date": r["published_at"] or r["created_at"],
                    "url": r["html_url"],
                })
        except Exception:
            pass

    events.sort(key=lambda e: e["date"], reverse=True)
    _cache["data"] = events[:50]  # Keep top 50
    _cache["fetched"] = now
    return _cache["data"]


def format_rfc822(dt_str: str) -> str:
    """Convert ISO datetime to RFC 822 format for RSS."""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def generate_rss(events: list[dict]) -> str:
    """Generate RSS 2.0 XML."""
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    items = ""
    for e in events[:30]:
        items += f"""  <item>
    <title>{xml_escape(e['title'])}</title>
    <link>{xml_escape(e['url'])}</link>
    <guid>{xml_escape(e['url'])}</guid>
    <pubDate>{format_rfc822(e['date'])}</pubDate>
    <author>{xml_escape(e['author'])}</author>
    <category>{xml_escape(e['type'])} — {xml_escape(e['repo'])}</category>
  </item>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Poke Labs Activity Feed</title>
  <link>https://github.com/{ORG}</link>
  <description>Recent commits, PRs, and releases from Poke Labs repositories</description>
  <language>en-us</language>
  <lastBuildDate>{now}</lastBuildDate>
  <generator>poke-feed/1.0</generator>
{items}</channel>
</rss>"""


def generate_atom(events: list[dict]) -> str:
    """Generate Atom 1.0 XML."""
    now = datetime.now(timezone.utc).isoformat()
    entries = ""
    for e in events[:30]:
        updated = e["date"].replace("Z", "+00:00")
        entries += f"""  <entry>
    <title>{xml_escape(e['title'])}</title>
    <link href="{xml_escape(e['url'])}"/>
    <id>urn:github:{xml_escape(e['repo'])}:{xml_escape(e['url'])}</id>
    <updated>{updated}</updated>
    <author><name>{xml_escape(e['author'])}</name></author>
    <category term="{xml_escape(e['type'])}"/>
    <summary>{xml_escape(e['type'])} in {xml_escape(e['repo'])}</summary>
  </entry>
"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Poke Labs Activity Feed</title>
  <link href="https://github.com/{ORG}"/>
  <id>urn:uuid:poke-feed-{ORG}</id>
  <updated>{now}</updated>
  <generator>poke-feed/1.0</generator>
{entries}</feed>"""


LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Poke Feed — Poke Labs Activity Feed</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0f;color:#e0e0e0;line-height:1.6;padding:2rem}
h1{font-size:2rem;color:#8b5cf6;margin-bottom:.5rem}
.sub{color:#9ca3af;margin-bottom:2rem}
.feed-links{display:flex;gap:1rem;margin-bottom:2rem}
.feed-links a{padding:.6rem 1.2rem;border-radius:8px;text-decoration:none;font-weight:600}
.rss{background:#f97316;color:#fff}
.atom{background:#6366f1;color:#fff}
pre{background:#12121a;border:1px solid #2a2a4a;border-radius:8px;padding:1rem;overflow-x:auto;margin:1rem 0}
code{color:#a78bfa;font-size:.85rem}
</style>
</head>
<body>
<h1>📡 Poke Feed</h1>
<p class="sub">RSS/Atom feed of all Poke Labs GitHub activity — commits, PRs, and releases.</p>
<div class="feed-links">
<a href="/feed.xml" class="rss">📰 RSS Feed</a>
<a href="/atom.xml" class="atom">⚛️ Atom Feed</a>
</div>
<h2 style="color:#8b5cf6">Subscribe</h2>
<p style="color:#9ca3af">Add either URL to your RSS reader:</p>
<pre><code>https://poke-feed.pokelabs.org/feed.xml
https://poke-feed.pokelabs.org/atom.xml</code></pre>
<h2 style="color:#8b5cf6;margin-top:1.5rem">Monitored Repos</h2>
<p style="color:#9ca3af">services, council, poke, cli, brand</p>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self.send_html(LANDING_HTML)
        elif path == "/feed.xml":
            events = get_feed_data()
            self.send_text(generate_rss(events), "application/rss+xml")
        elif path == "/atom.xml":
            events = get_feed_data()
            self.send_text(generate_atom(events), "application/atom+xml")
        elif path == "/api/health":
            self.send_json({"ok": True, "v": 1, "repos": len(REPOS), "cached": _cache["data"] is not None})
        else:
            self.send_response(404)
            self.end_headers()

    def send_html(self, html: str):
        data = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, text: str, content_type: str):
        data = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        pass  # Suppress request logs


def main():
    parser = argparse.ArgumentParser(description="Poke Feed server")
    parser.add_argument("--generate", action="store_true", help="Generate static feed.xml to stdout")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    if args.generate:
        events = get_feed_data()
        print(generate_rss(events))
        return

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"Poke Feed running on port {args.port}")
    print(f"  RSS:  http://localhost:{args.port}/feed.xml")
    print(f"  Atom: http://localhost:{args.port}/atom.xml")
    server.serve_forever()


if __name__ == "__main__":
    main()
