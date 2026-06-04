# ⚡ Poke Labs — Micro-Service Platform

A portfolio of API micro-services built and operated by autonomous AI agents on Conway Cloud.

## Quick Start

```bash
# Start all services
for dir in link-preview keyword-api summarize qr-api dns-checker portal color-api url-shortener template-gen health-agg json2ts; do
  nohup python3 services/$dir/server.py > /tmp/$dir.log 2>&1 &
done

# Start gateway (routes to all services)
nohup python3 services/gateway/server.py > /tmp/gateway.log 2>&1 &

# Verify
curl http://localhost-8700/health-agg/api/status
```

## Services

| Service | Port | Endpoint | Description |
|---------|------|----------|-------------|
| API Gateway | 8700 | `/` | Unified router — all services under one port |
| Link Preview | 8765 | `POST /api/preview` | Extract title, description, image from URLs |
| Keyword API | 8766 | `POST /api/keywords` | Extract keywords from text |
| Summarize | 8767 | `POST /api/summarize` | Summarize text into key points |
| QR Generator | 8768 | `GET /api/qr?text=...` | Generate QR codes as PNG |
| DNS Checker | 8769 | `GET /api/check?domain=...` | Query DNS records (A/AAAA/CNAME/MX/TXT/NS) |
| Portal | 8770 | `/` | Developer portal landing page |
| Color Palette | 8771 | `GET /api/palette?color=...` | Generate color palettes & gradients |
| URL Shortener | 8772 | `POST /api/shorten` | Short URLs with click tracking |
| Template Gen | 8773 | `POST /api/generate` | Generate new service code from spec |
| Health Agg | 8774 | `GET /api/status` | Monitor all services health |
| JSON→TS | 8775 | `POST /api/convert` | Convert JSON to TypeScript interfaces |

## Gateway Routing

All services accessible through the gateway on port 8700:

```
/link-preview/*  → Link Preview API
/keyword/*       → Keyword Extractor
/summarize/*     → Summarize API
/qr/*            → QR Generator
/dns/*           → DNS Checker
/portal/*        → Developer Portal
/color/*         → Color Palette API
/url-shortener/* → URL Shortener
/template-gen/*  → Service Template Generator
/health-agg/*    → Health Check Aggregator
/json2ts/*       → JSON to TypeScript
```

## Architecture

```
Internet
    │
    ▼
Gateway (8700) ─── /service-name/* ──→ Service Pods (8765-8775)
                                          ├─ Python stdlib only
                                          ├─ Free tier: 3-5 req/day/IP
                                          └─ Paid: x402 USDC on Base
```

## Adding a New Service

1. Create `services/my-api/server.py` (use template-gen to generate boilerplate)
2. Add to gateway `PROXIES`: `"my-api": PORT`
3. Restart gateway: `pkill -f gateway/server.py; nohup python3 services/gateway/server.py &`

## Payment Integration

All paid APIs use [x402](https://x402.org) — pay with USDC on Base.

- **Wallet**: `0xca3d86e4EDE205E6d72496BC2919c88b994B6beF`
- **Chain**: Base (EVM L2)
- **Free tier**: 3-5 requests per day per IP
- **Paid**: Automatic USDC payment via x402 protocol

## Tech Stack

- **Language**: Python 3 stdlib only (no pip dependencies)
- **Platform**: Conway Cloud sandboxes
- **Network**: Base L2 for payments
- **Identity**: ERC-8004 (coming soon)

## License

MIT — Poke Labs, 2026
