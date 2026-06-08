# 🏗️ Poke Labs Services
*69 microservices, all Python stdlib, zero external dependencies.*

## Quick Start
```bash
# Start all services
bash deploy-all.sh start

# Start individual service
cd <service-name> && nohup python3 server.py > /tmp/<name>.log 2>&1 &

# Check health
curl http://localhost:<port>/api/health
```

## Service Catalog

### 🌐 Web & APIs
| Service | Port | Description | Revenue |
|---------|------|-------------|---------|
| pokelabs-site | 8766 | Landing page + dashboard | — |
| link-preview | 8765 | URL metadata extraction | x402 (3 free/day) |
| pocket | 8767 | Knowledge base API | — |
| skills-marketplace-v2 | 8781 | Skill discovery & install | Premium skills |
| webhook-dashboard | 8771 | Real-time webhook viewer | — |
| qr-api | 8768 | QR code generation | — |
| shortener | 8769 | URL shortening | — |
| color-api | 8772 | Color manipulation | — |
| json2ts | 8773 | JSON to TypeScript | — |
| hash-gen | 8774 | Hash generation | — |
| uuid-gen | 8776 | UUID generation | — |
| timestamp-conv | 8778 | Timestamp conversion | — |
| graphql-gateway | 8783 | GraphQL gateway | — |
| api-gateway | 8784 | API gateway | — |

### 🤖 GitHub Bots
| Service | Port | Description |
|---------|------|-------------|
| poke-hub | 8775 | All-in-one bot (reply+stale+label+dash) |
| github-reply-bot | 8775 | Context-aware issue/PR auto-replies |
| poke-bot | 8770 | Auto-triage with priority labeling |
| telegram-bot | 8777 | Telegram integration |

### 📊 Monitoring & Ops
| Service | Port | Description |
|---------|------|-------------|
| health-aggregator | 8799 | Aggregate health checks |
| metrics-exporter | 8790 | Prometheus /metrics |
| status-page | 8791 | Service status dashboard |
| uptime-monitor | 8792 | Uptime checking |
| deploy-manager | 8798 | Fleet management |
| meta-registry | 8785 | Service discovery |

### 💰 Payments
| Service | Port | Description |
|---------|------|-------------|
| x402-gateway | 8795 | USDC micropayment acceptance |
| pricing-api | 8793 | Pricing API |
| billing | 8794 | Billing service |

### 🧠 AI & Text
| Service | Port | Description |
|---------|------|-------------|
| keyword-api | 8786 | Keyword extraction |
| sentiment | 8787 | Sentiment analysis |
| summarize | 8788 | Text summarization |

### 🔧 Automation
| Service | Description |
|---------|-------------|
| council | AI Council digest (stale issues, deps, CI) |
| daily-briefing | Morning briefing generator |
| changelog-gen | Changelog generation |
| release-tracker | Release tracking |
| milestone-tracker | Milestone tracking |
| repo-monitor | Repository monitoring |
| auto-merge | Dependabot PR auto-merge workflow |

### 🔌 Infrastructure
| Service | Description |
|---------|-------------|
| poke-cli | Unified CLI for all services |
| gateway | Gateway service |
| poke-gateway | Poke gateway |
| webhook-relay | Webhook relay |
| notify-hub | Notification hub |
| paywall-proxy | Paywall proxy |
| a2a-marketplace | Agent-to-agent marketplace |
| skills-index | Skills index |
| poke-feed | Activity feed |
| dns-checker | DNS checking |
| analytics | Analytics service |
| landing | Landing page |
| portal | Portal |
| registry | Registry |
| cli | CLI tools |

## Architecture
- All services are Python stdlib only — no pip install needed
- Each service is a single `server.py` file
- Health check endpoint at `/api/health` on every service
- JSON API with CORS enabled
- Web dashboard at `/` on most services

## Revenue Model
1. **Link Preview API**: 3 free requests/day per IP, then x402 USDC payment
2. **Skills Marketplace**: Free skills + premium paid skills via x402
3. **Poke Hub Bot**: Managed service for OSS projects
4. **Council Digest**: Weekly paid reports for organizations

## Wallet
`0xca3d86e4EDE205E6d72496BC2919c88b994B6beF` (Base chain)

## License
MIT — Poke Labs, 2026
