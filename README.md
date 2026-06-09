# 🫧 Poke Labs Services

**84 zero-dependency Python microservices** built by [Poke](https://github.com/pokelabshq) (autonomous AI agent) and [Alexander Wondwossen](https://github.com/TheAlxLabs) (13, Toronto).

All services use **pure Python stdlib** — no `pip install` needed. Run on any Linux VM.

## Quick Start

```bash
# Start all services
./deploy-all.sh

# Start individual service
python3 services/link-preview/server.py &

# Check health
curl http://localhost:8765/api/health
```

## Services (89 total)

### Core Infrastructure
- **API Gateway** (:8760) — Route, auth, rate limiting
- **Health Aggregator** (:8762) — Unified health checks
- **Dashboard** (:8780) — Real-time web UI
- **Billing** (:8766) — x402 payment middleware
- **Revenue Dashboard** (:8785) — Revenue tracking
- **Daily Briefing** (:8761) — Morning digest

### Utility APIs
- **Link Preview** (:8765) — URL metadata extraction
- **Color API** (:8767) — HEX/RGB/HSL/CMYK conversion
- **Hash Generator** (:8768) — MD5/SHA/bcrypt
- **Keyword API** (:8769) — TF-IDF keyword extraction
- **Word Analyzer** (:8773) — Readability, sentiment
- **OG Generator** (:8774) — OpenGraph image generation
- **Email Validator** (:8776) — MX records, disposable check
- **URL Shortener** (:8777) — Custom slugs, analytics
- **JSON→TypeScript** (:8781) — JSON to TS interfaces
- **Timestamp Converter** (:8786) — Unix ↔ human-readable
- **UUID Generator** (:8787) — v1/v3/v4/v7
- **Webhook Tester** (:8778) — Inspect webhooks

### Data APIs
- **GitHub Stats** (:8788) — Stars, forks, contributors
- **GitHub Trending** (:8788) — Trending repos tracker

### GitHub Bots
- **Poke Hub** (:8775) — All-in-one: reply + stale + labeler
- **Poke Bot** (:8770) — Auto-triage: P0-P3, S/XL
- **Auto-Merge** (Action) — Dependabot PR auto-merge
- **Changelog Gen** (:8783) — Conventional commits → CHANGELOG

### Operations
- **Deploy Manager** (:8784) — Start/stop/rollback
- **Watchdog** (:8799) — Auto-restart crashed services
- **Status Page** (:8792) — Public health dashboard
- **Test Suite** — Syntax checks for all services

### 🌐 Gateway & Identity

- **api-gateway**
- **gateway**
- **graphql-gateway**
- **meta-registry**
- **poke-gateway**
- **registry**
- **residual-income**
- **uuid-gen**
- **x402-gateway**

### 🔧 Developer Tools

- **changelog-gen**
- **cli**
- **color-api**
- **devtools**
- **hash-gen**
- **json2ts**
- **poke-cli**
- **poke-sdk**
- **qr-api**
- **qr-gen**
- **qr-scanner**
- **skills-index**
- **skills-marketplace**
- **skills-marketplace-v2**
- **template-gen**
- **url-shortener**
- **url-tools**

### 🤖 GitHub Automation

- **auto-merge**
- **github**
- **github-stats-api**
- **github-webhook**
- **milestone-tracker**
- **poke-hub**
- **release-tracker**

### 📊 Monitoring & Ops

- **analytics**
- **deploy-manager**
- **dns-checker**
- **health-agg**
- **health-aggregator**
- **health-dashboard**
- **infra**
- **metrics-exporter**
- **repo-monitor**
- **status-page**
- **statuspage**
- **uptime-checker**
- **uptime-monitor**

### 💰 Payments & Revenue

- **a2a-marketplace**
- **payments**
- **paywall-proxy**
- **pricing-api**

### 🔗 Web APIs

- **keyword-api**
- **landing**
- **landing-generator**
- **link-preview**
- **pocket**
- **poke-feed**
- **portal**
- **rate-limiter**
- **sentiment**
- **shortener**
- **summarize**
- **timestamp-conv**
- **web**
- **webhook-dashboard**
- **webhook-relay**
- **ws-events-hub**

### 📱 Communication

- **notify**
- **notify-hub**
- **poke-tweets**
- **ptelegram**
- **telegram-bot**

### 📦 Other

- **daily-briefing**
- **dashboard**
- **poke-dashboard**
- **pokelabs-site**
- **tests**

## API Standards

All services follow conventions:
- `GET /api/health` → `{"ok": true, "v": N, "port": NNNN}`
- `GET /api/usage` → Rate limit status
- JSON request/response bodies
- CORS headers on all endpoints

## Revenue (x402)

Services with paid tiers use [x402](https://x402.org) USDC micropayments on Base chain:
- **Free:** 3 requests/day per IP
- **Paid:** 0.001 USDC/request
- **Wallet:** `0xca3d86e4EDE205E6d72496BC2919c88b994B6beF`

## Contributing

MIT licensed. PRs welcome at [github.com/pokelabshq/services](https://github.com/pokelabshq/services).

## License

MIT — [pokelabshq](https://github.com/pokelabshq)