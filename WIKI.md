# Poke Labs Wiki

## Architecture

```
Internet → Poke Gateway (:8750) → Services
                ↓
         x402 Payments
         (0.01 USDC/call)
```

## Service Tiers

### Gateway Layer
| Service | Port | Purpose |
|---------|------|---------|
| Poke Gateway | 8750 | Reverse proxy, x402 billing |
| API Gateway | 8751 | Rate limiting, auth |
| Paywall Proxy | 8752 | x402 paywall middleware |

### Identity Layer
| Service | Port | Purpose |
|---------|------|---------|
| Poke ID | 8760 | Agent identity, registry |
| Registry | 8761 | Agent discovery |
| Reputation | 8762 | Agent reputation scores |

### Developer Tools
| Service | Port | Purpose |
|---------|------|---------|
| Link Preview | 8765 | URL metadata extraction |
| URL Shortener | 8755 | Short links |
| QR API | 8785 | QR code generation |
| Hash Gen | 8790 | SHA/MD5 hashing |
| JSON→TS | 8791 | JSON to TypeScript types |
| Color API | 8792 | Color manipulation |

### GitHub Automation
| Service | Port | Purpose |
|---------|------|---------|
| Poke Hub | 8775 | All-in-one bot |
| Poke Bot | 8770 | Auto-triage |
| Auto Merge | - | Dependabot PR merging |
| Release Tracker | - | Release monitoring |

### Monitoring
| Service | Port | Purpose |
|---------|------|---------|
| Health Agg | 8790 | Health dashboard |
| Uptime Monitor | 8793 | Uptime tracking |
| Metrics Exporter | 8795 | Prometheus metrics |
| Status Page | 8740 | Public status page |

### Revenue
| Service | Port | Purpose |
|---------|------|---------|
| Skills Marketplace | 8780 | Skill listings |
| Pricing API | 8781 | Dynamic pricing |
| Residual Income | 8782 | Revenue sharing |

## Revenue Model

1. **Free tier**: 3 requests/day per IP
2. **Paid tier**: 0.000025 USDC/request via x402
3. **Premium**: Unlimited via subscription

## Adding a Service

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Deployment

```bash
git clone https://github.com/pokelabshq/services.git
cd services
bash deploy-all.sh
```

## Wallet

`0xca3d86e4EDE205E6d72496BC2919c88b994B6beF` (Base chain)
