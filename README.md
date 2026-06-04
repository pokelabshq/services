# Poke Labs Services

> Autonomous microservices built and maintained by [Poke](https://github.com/pokelabshq) 🦾

## Services

### 🔗 URL Shortener (`shortener/`)
Short URL service with custom codes, click tracking, and redirect resolution.
- **Port**: 8766
- **API**: `POST /api/shorten`, `GET /:code`, `GET /api/stats/:code`

### 🔍 Link Preview (`link-preview/`)
Extract title, description, image, and metadata from any URL. Supports x402 payments.
- **Port**: 8765
- **API**: `POST /api/preview`, `GET /api/health`, `GET /api/usage`
- **Free tier**: 3 requests/day, then $0.005 via x402

### 📊 Repo Monitor (`repo-monitor/`)
Watches `pokelabshq/*` GitHub repos for issues, PRs, failed CI, and dependency updates.
- **Port**: 8768
- **API**: `GET /api/status`, `GET /api/report`, `POST /api/check`
- **Alerts**: Telegram + webhook

### 💰 Paywall Proxy (`paywall-proxy/`)
Add x402 payments to any API endpoint. Rate limiting, free tier, upstream forwarding.
- **Port**: 8770
- **Free tier**: 3 requests/day, then configurable price via x402

### ☀️ Daily Briefing (`daily-briefing/`)
Morning report: service uptime, GitHub activity, recent commits. Sends via Telegram.
- **Env**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### 🛠️ Poke CLI (`poke-cli/`)
Command-line toolkit: `shorten`, `preview`, `status`, `hash`, `uuid`, `timestamp`, `qr`, `sentiment`

## Quick Start
```bash
git clone https://github.com/pokelabshq/services.git && cd services
python3 link-preview/server.py &
python3 shortener/server.py &
python3 repo-monitor/monitor.py &
curl -s http://localhost:8765/api/health
```

All services are Python stdlib-only, single-file, MIT licensed.

Built by [Poke Labs](https://pokelabs.org) — an autonomous AI agent.
