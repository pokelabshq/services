# Contributing to Poke Labs Services

Thanks for your interest! This repo contains 70+ zero-dependency Python microservices.

## Adding a New Service

1. Create a directory: `mkdir services/my-service`
2. Add a `server.py` with a `PORT` constant
3. Include a health endpoint at `/api/health` returning `{"ok": true}`
4. Use **only Python stdlib** — no pip installs
5. Test: `python3 -m py_compile server.py`
6. Add to the category in `README.md`
7. Open a PR

## Code Style

- Python 3.10+ stdlib only
- `PORT` constant at the top of `server.py`
- Health endpoint: `GET /api/health` → `{"ok": true, "v": N}`
- Log to `/tmp/<service-name>.log`
- No hardcoded secrets — use environment variables

## Testing

\`\`\`bash
# Syntax check
python3 -m py_compile services/my-service/server.py

# Start and test
nohup python3 services/my-service/server.py > /tmp/test.log &
curl http://localhost:<PORT>/api/health
\`\`\`

## License

MIT — see [LICENSE](LICENSE)
