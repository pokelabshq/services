# Contributing to Poke Labs

Thanks for wanting to help! Here's how to add a new service.

## Service Requirements

1. **Zero dependencies** — Pure Python stdlib only (no pip install)
2. **Health endpoint** — `GET /api/health` returning `{"ok": true, "v": N, "port": NNNN}`
3. **Port constant** — `PORT = 87XX` at the top of your server file
4. **Single file** — `server.py` preferred, or `bot.py`/`app.py`
5. **Silent logging** — `def log_message(self, *a): pass` on your handler

## Adding a Service

```bash
mkdir myservice
cat > myservice/server.py << 'PYEOF'
#!/usr/bin/env python3
"""My Service — Description here."""
import http.server, json, socketserver, urllib.parse

PORT = 87XX  # Pick an unused port (see SERVICES.md)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/api/health":
            self.send_json({"ok": True, "v": 1, "port": PORT})
        else:
            self.send_json({"error": "not found"}, 404)

    def send_json(self, d, c=200):
        b = json.dumps(d).encode()
        self.send_response(c)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a): pass

class R(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"My Service on port {PORT}")
    R(("", PORT), Handler).serve_forever()
PYEOF
```

## Claiming a Port

Check existing ports:
```bash
grep -r 'PORT\s*=' */server.py */bot.py */app.py | sort -t= -k2 -n
```

Pick the next available port in the 8740-8799 range.

## Submitting

```bash
cd services
git add myservice/
git commit -m "feat: My Service — description"
git push
```

## License

All contributions are MIT licensed.
