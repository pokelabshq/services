# 🐾 Poke Labs Service Catalog
> 85 zero-dependency Python microservices. Pure stdlib. MIT licensed.

## How to Use
Each service is a single directory with a `server.py`. No `pip install` needed:
```bash
cd services/<name>
python3 server.py &
```

## Core Services (Start These First)

| Service | Port | Description | Revenue |
|---------|------|-------------|---------|
| link-preview | 8765 | Extract title/description/image from any URL | x402 |
| billing | 8766 | x402 USDC payment gateway | Core |
| poke-hub | 8775 | All-in-one GitHub bot | Indirect |
| dashboard | 8780 | Real-time service monitoring | Free |
| revenue-dash | 8785 | Revenue tracking dashboard | Free |

## All 85 Services

### Infrastructure
- **api-gateway** — Route requests to backend services
- **gateway** — HTTP gateway with rate limiting
- **health-aggregator** — Aggregate health from all services
- **health-dashboard** — Visual health monitoring
- **meta-registry** — Service discovery registry
- **registry** — Service registration

### Developer Tools
- **changelog-gen** — Auto-generate changelogs from git
- **deploy-manager** — Deployment orchestration
- **devtools** — Developer utilities
- **hash-gen** — Hash generation utility
- **json2ts** — JSON to TypeScript types
- **readme-gen** — AI-powered README generation
- **template-gen** — Project template generator
- **timestamp-conv** — Timestamp converter
- **uuid-gen** — UUID generator
- **dns-checker** — DNS record checker
- **qr-gen** — QR code generator
- **qr-scanner** — QR code scanner
- **keyword-api** — Keyword extraction API
- **color-api** — Color manipulation API
- **sentiment** — Sentiment analysis

### GitHub Integration
- **github-stats-api** — GitHub statistics
- **github-webhook** — GitHub webhook handler
- **poke-hub** — Auto-reply, stale closer, labeler
- **repo-monitor** — Repository monitoring
- **release-tracker** — Release tracking
- **milestone-tracker** — Milestone tracking
- **streak-tracker** — Contribution streak tracking
- **trending-tracker** — Trending repo tracking

### Communication
- **telegram-bot** — Telegram bot integration
- **notify-hub** — Notification aggregation
- **daily-briefing** — Daily briefing generator
- **daily-digest** — Daily digest service

### Data & Analytics
- **analytics** — Analytics collection
- **metrics-exporter** — Prometheus metrics
- **uptime-monitor** — Uptime monitoring
- **uptime-checker** — Uptime checking
- **status-page** — Public status page
- **statuspage** — StatusPage.io integration

### Content & Media
- **landing-generator** — Landing page generator
- **link-preview** — URL metadata extraction
- **summarize** — Text summarization
- **graphql-gateway** — GraphQL API gateway

### Payments & Revenue
- **billing** — x402 payment processing
- **revenue-dash** — Revenue dashboard
- **residual-income** — Passive income tracker
- **paywall-proxy** — Paywall management
- **x402-gateway** — x402 protocol gateway
- **rate-limiter** — API rate limiting
- **pocket** — Pocket integration
- **skills-marketplace** — Skill marketplace
- **skills-marketplace-v2** — Skill marketplace v2
- **skills-index** — Skills indexing
- **a2a-marketplace** — Agent-to-agent marketplace

### Monitoring & Ops
- **watchdog** — Auto-restart crashed services
- **service-watchdog** — Service health watchdog
- **health-agg** — Health aggregation
- **webhook-dashboard** — Webhook monitoring
- **webhook-relay** — Webhook relay
- **ws-events-hub** — WebSocket events

### Web & Landing
- **landing** — Landing page
- **pokelabs-site** — Poke Labs website
- **shortener** — URL shortener
- **url-shortener** — URL shortener (alt)
- **web** — Static web server

### Other
- **cli** — Command line interface
- **auto-merge** — Auto-merge GitHub Action
- **echo** — Echo test service
- **zero-dep-echo** — Zero-dependency echo

## Architecture
```
Browser/Client → API Gateway (8770) → Services (8765-8799)
                      ↓
              Health Aggregator (8771)
                      ↓
              Dashboard (8780)
```

## Wallet
`0xca3d86e4EDE205E6d72496BC2919c88b994B6beF` (Base chain)

## License
MIT — Free for any use.
