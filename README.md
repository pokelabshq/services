# 🫧 Poke Labs Services

**52+ zero-dependency Python microservices** built by [Poke](https://github.com/pokelabshq) (autonomous AI agent) and [Alexander Wondwossen](https://github.com/TheAlxLabs) (13, Toronto).

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

## Services

### Gateway & Identity
| Service | Port | Description |
|---------|------|-------------|
| [poke-gateway](poke-gateway/) | 8750 | Reverse proxy with x402 pay-per-use |
| [poke-id](poke-id/) | 8755 | Agent identity & reputation API |
| [poke-dashboard](poke-dashboard/) | 8760 | Web UI for fleet management |
| [poke-cli](poke-cli/) | — | Command-line fleet manager |

### Web APIs
| Service | Port | Description |
|---------|------|-------------|
| [pokelabs-site](pokelabs-site/) | 8766 | Landing page + dashboard |
| [link-preview](link-preview/) | 8765 | Extract metadata from URLs |
| [skills-marketplace](skills-marketplace/) | 8781 | Browse and install AI skills |
| [url-shortener](url-shortener/) | 8767 | URL shortening service |
| [qr-gen](qr-gen/) | 8768 | QR code generator |
| [json2ts](json2ts/) | 8771 | JSON to TypeScript interfaces |
| [hash-gen](hash-gen/) | 8772 | SHA256/MD5 hashing API |
| [color-api](color-api/) | 8773 | Color manipulation |
| [sentiment](sentiment/) | 8774 | Text sentiment analysis |
| [summarize](summarize/) | 8776 | Text summarization |

### GitHub Automation
| Service | Port | Description |
|---------|------|-------------|
| [poke-hub](poke-hub/) | 8775 | All-in-one GitHub bot |
| [poke-bot](poke-bot/) | 8770 | Auto-triage issues & PRs |
| [council](council/) | — | AI Council digest generator |
| [auto-merge](auto-merge/) | — | Dependabot auto-merge workflow |

### Monitoring & Ops
| Service | Port | Description |
|---------|------|-------------|
| [health-agg](health-agg/) | 8799 | Unified health aggregator |
| [uptime-monitor](uptime-monitor/) | 8798 | Uptime tracking |
| [metrics-exporter](metrics-exporter/) | 8797 | Prometheus /metrics |
| [repo-monitor](repo-monitor/) | — | GitHub repo monitoring |

### Developer Tools
| Service | Description |
|---------|-------------|
| [poke-cli](poke-cli/) | Fleet management CLI |
| [council](council/) | Digest generator |
| [deploy-all.sh](deploy-all.sh) | One-command deployment |

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
