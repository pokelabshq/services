"""
Poke Labs SDK for Python — Zero dependencies.
Pure stdlib. Works on any Python 3.10+.

Usage:
    from poke_labs import Client
    c = Client("http://localhost:8750")
    print(c.preview("https://github.com"))
"""
import json, urllib.request, urllib.error, urllib.parse

class Client:
    def __init__(self, base_url="http://localhost:8750", api_key=None):
        self.base = base_url.rstrip("/")
        self.key = api_key

    def _req(self, method, path, data=None):
        url = f"{self.base}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        if self.key: req.add_header("Authorization", f"Bearer {self.key}")
        try:
            with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())
        except urllib.error.HTTPError as e:
            try: return {"error": json.loads(e.read()), "status": e.code}
            except: return {"error": str(e), "status": e.code}

    def health(self): return self._req("GET", "/api/health")
    def usage(self): return self._req("GET", "/api/usage")
    def preview(self, url): return self._req("POST", "/preview/api/preview", {"url": url})
    def identity(self): return self._req("GET", "/id/api/identity")
    def agents(self): return self._req("GET", "/id/api/agents")
    def agent(self, name): return self._req("GET", f"/id/api/agents/{name}")
    def reputation(self, name): return self._req("GET", f"/id/api/reputation/{name}")
    def feed(self, **kw):
        q = urllib.parse.urlencode({k:v for k,v in kw.items() if v})
        return self._req("GET", f"/id/api/feed?q={q}" if q else "/id/api/feed")
    def event(self, service, type, message, meta=None):
        return self._req("POST", "/id/api/events", {"service":service,"type":type,"message":message,"meta":meta})
