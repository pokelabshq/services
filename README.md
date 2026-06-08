# 🐾 Poke Labs Services

**52 open-source microservices — Python stdlib, zero dependencies. MIT licensed.**

## Quick Start

```bash
# Start ALL services at once
bash /home/alx/deploy-all.sh start

# Check status
bash /home/alx/deploy-all.sh status

# Stop everything
bash /home/alx/deploy-all.sh stop

# Monitor health
curl -s http://localhost:8799/api/status | python3 -m json.tool
```

## Service Catalog

### Core Services
| Service | Port | Description |
|---------|------|-------------|
| Poke Hub | 8775 | All-in-one GitHub bot (reply, triage, stale close) |
| Skills Marketplace v2 | 8781 | Browse, search, install skills with UI |
| Poke Labs Site v7 | 8766 | Landing page + dashboard |
| Link Preview API v4 | 8765 | URL metadata extraction with x402 |
| Health Aggregator v1 | 8799 | Unified monitoring dashboard |

### GitHub Services
| Service | Port | Description |
|---------|------|-------------|
| Poke Bot | 8770 | Auto-triage (P0-P3 labels, S/XL PR sizes) |
| Auto-merge PR | — | GitHub Action: auto-squash-merge Dependabot (patch only) |

### Communication
| Service | Port | Description |
|---------|------|-------------|
| Telegram Bot | 8777 | Telegram integration |
| Council Digest | 8776 | Daily/weekly repo digest |

### Infrastructure
| Service | Port | Description |
|---------|------|-------------|
| Registry | 8785 | Agent registry |
| Skills Hub | 8780 | Skills directory |
| Billing | 8795 | Billing service |
| Pricing | 8790 | Pricing API |

## API Standards

All services expose `GET /api/health` returning `{"ok": true, "v": N, "port": N}`.

## Health Aggregator (Port 8799)

Scans all known service ports via TCP + HTTP health probes:
- `GET /api/status` → Full status JSON
- `GET /` → Visual dashboard with uptime %, per-service status

## To Deploy After Funding

```bash
# 1. Fund wallet: 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF (Base)
# 2. Buy Conway credits → $25 tier
# 3. Deploy: bash /home/alx/deploy-all.sh start
# 4. Expose ports: 8765 8766 8775 8781 8799
```

## Wallet

`0xca3d86e4EDE205E6d72496BC2919c88b994B6beF` (Base chain)

## License

MIT — Poke Labs © 2026. Built by Alexander Wondwossen.
