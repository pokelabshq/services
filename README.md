# 🏗️ Poke Labs Services
*69 zero-dependency Python microservices — ready to run.*

## Quick Start

```bash
# Start all services
bash deploy-all.sh start

# Start a specific service
cd link-preview && nohup python3 server.py > /tmp/link-preview.log 2>&1 &
```

## Service Categories

### 🔗 URL & Link Tools
| Service | Port | Description |
|---------|------|-------------|
| link-preview | 8765 | Extract title, description, image from URLs (x402) |
| url-shortener | - | URL shortener with analytics |
| qr-api | - | QR code generator |
| qr-scanner | - | QR code scanner |

### 📊 Analytics & Monitoring
| Service | Port | Description |
|---------|------|-------------|
| health-aggregator | 8799 | Fleet-wide health dashboard |
| uptime-monitor | - | Uptime checker with alerts |
| metrics-exporter | - | Prometheus-compatible metrics |
| analytics | - | Event analytics pipeline |

### 🤖 GitHub Automation
| Service | Port | Description |
|---------|------|-------------|
| poke-hub | 8775 | All-in-one GitHub bot (reply + stale + labels) |
| github-stats-api | 8779 | GitHub stats |
| milestone-tracker | - | Milestone/release tracking |
| changelog-gen | - | Auto-generate changelogs from commits |
| repo-monitor | - | Cross-repo monitoring dashboard |
| auto-merge | - | Dependabot auto-merge workflow |

### 🛠️ Developer Utilities
| Service | Port | Description |
|---------|------|-------------|
| json2ts | - | JSON to TypeScript types |
| hash-gen | - | Hash generator |
| timestamp-conv | - | Unix ↔ ISO timestamp converter |
| uuid-gen | - | UUID generator |
| keyword-api | - | Keyword extraction |
| color-api | - | Color palette generator |
| summarize | - | Text summary generator |
| template-gen | - | Template generator |

### 💰 Payments & Skills
| Service | Port | Description |
|---------|------|-------------|
| skills-marketplace-v2 | 8781 | Skill registry with search + install |
| skills-index | 8782 | Skills index JSON |
| x402-gateway | 8795 | USDC payment gateway |
| pricing-api | 8790 | Service pricing |
| paywall-proxy | - | x402 paywall proxy |
| residual-income | - | Revenue tracking dashboard |

### 🌐 Web & Portal
| Service | Port | Description |
|---------|------|-------------|
| pokelabs-site | 8766 | Main landing page + link preview combined |
| api-gateway | 8767 | Service gateway/router |
| dashboard | - | Admin dashboard |
| landing | - | Static landing page |
| portal | - | Service portal |
| status-page | - | Public status page |
| statuspage | - | StatusPage.io-compatible API |

### 📢 Notifications
| Service | Port | Description |
|---------|------|-------------|
| notify-hub | - | Multi-channel notification hub |
| telegram-bot | 8777 | Telegram bot |
| daily-briefing | - | Automated daily briefing |
| sentiment | - | Sentiment analysis for mentions |

### 🔌 API & Infra
| Service | Port | Description |
|---------|------|-------------|
| gateway | 8768 | API gateway |
| graphql-gateway | 8769 | GraphQL federation |
| ws-events-hub | 8771 | WebSocket real-time events |
| webhook-relay | 8772 | Webhook forwarding |
| webhook-dashboard | 8773 | Webhook management UI |
| a2a-marketplace | 8774 | Agent-to-agent marketplace |
| poke-gateway | 8776 | Poke-specific gateway |
| registry | 8785 | Service registry |
| meta-registry | 8786 | Registry of registries |
| deploy-manager | 8787 | Fleet deployment manager |
| health-dashboard | 8788 | Health dashboard |
| dns-checker | 8789 | DNS record checker |
| release-tracker | 8791 | Release tracker |
| uptime-checker | 8792 | Uptime checker |
| github-webhook | 8793 | GitHub webhook handler |
| poke-tweets | 8794 | Twitter/X integration |
| pocket | 8796 | Read-later service |
| poke-cli | 8797 | CLI tool |
| poke-feed | 8798 | Activity feed |
| cli | 8799 | CLI utilities |
| shortener | - | URL shortener |

## Architecture

```
Client → API Gateway (8767) → Service Mesh
                ↓
     Health Aggregator (8799)
                │
     ┌──────────┼──────────┐
     ↓          ↓          ↓
  Link       Poke      Skills
  Preview    Hub        Marketplace
  (8765)    (8775)     (8781)
```

## Revenue Model

1. **Link Preview API** — 3 free/day, then x402 USDC per request
2. **Skills Marketplace** — Premium paid skills
3. **Poke Hub** — Managed GitHub bot service
4. **API Gateway** — Rate-limited API access

## Tech Stack

- **Language:** Python 3 (stdlib only — zero dependencies)
- **Protocol:** HTTP/REST + WebSocket
- **Payments:** x402 USDC on Base chain
- **Hosting:** Conway Cloud sandboxes
- **Registry:** github.com/pokelabshq/services

## Wallet

`0xca3d86e4EDE205E6d72496BC2919c88b994B6beF` (Base chain)

## License

MIT — Poke Labs, 2026
