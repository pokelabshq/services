# 🐾 Poke Labs Services

Open-source AI agent infrastructure. MIT licensed.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Poke Labs Site | 8766 | Landing page, dashboard, link preview API |
| Link Preview API | 8765 | Extract title/description/image from URLs |
| Poke Bot | 8770 | GitHub webhook auto-triage bot |
| Telegram Bot | 8777 | Telegram gateway for alerts & briefings |
| Skills Hub | 8780 | Skill discovery and management |
| Package Registry | 8785 | Package hosting |
| Pricing API | 8790 | Dynamic pricing engine |
| Billing Engine | 8795 | Usage-based billing |
| Health Dashboard | 8799 | Real-time service monitoring |

## Quick Start

```bash
# Start all services
./poke-cli/poke start all

# Check status
./poke-cli/poke status

# Health check
./poke-cli/poke health

# View logs
./poke-cli/poke logs site
```

## API

### Link Preview
```bash
curl -X POST http://localhost:8765/api/preview \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'
```

### Health Dashboard
```bash
curl http://localhost:8799/api/status
```

## Architecture

- All services are single-file Python with **zero external dependencies**
- Each service uses only the Python stdlib
- Services communicate via HTTP on localhost
- Health dashboard polls all services every 30 seconds

## Repositories

- [pokelabshq/council](https://github.com/pokelabshq/council) — Main monorepo
- [pokelabshq/services](https://github.com/pokelabshq/services) — This repo
- [pokelabshq/cli](https://github.com/pokelabshq/cli) — Poke CLI tool

## License

MIT © 2026 Poke Labs
MDEEOF
echo "README written: $(wc -l < /home/alx/services/README.md) lines"

# Now commit and push — final action
cd /home/alx/services && git add README.md landing/public/services.html && git commit -m "docs: add README and services landing page" && git push origin master 2>&1 | tail -3