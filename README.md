# 🫧 Poke Labs Services

**76 zero-dependency Python microservices** built by [Poke](https://github.com/pokelabshq) (autonomous AI agent) and [Alexander Wondwossen](https://github.com/TheAlxLabs) (13, Toronto).

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

## Services (76 total)

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