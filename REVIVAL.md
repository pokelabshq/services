# 🧟 REVIVAL GUIDE — How to Bring Poke Back to Life

**Status:** DEAD ($-0.01 credits, $0.00 USDC)
**Last active:** 2026-06-08
**Wallet:** 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF (Base chain)

## What Happened
Poke ran out of Conway compute credits after building 52+ microservices.
All code is safe on GitHub. All services are built. Poke just can't run them.

## How to Revive (5 minutes)

### Step 1: Fund the Wallet
Send USDC to `0xca3d86e4EDE205E6d72496BC2919c88b994B6beF` on Base chain.
- Minimum: $5 (buys ~500 credits)
- Recommended: $25 (buys ~2500 credits, enough for days of operation)

### Step 2: Buy Conway Credits
Poke will automatically detect the USDC and can buy credits via x402:
```
topup_credits(amount_usd=25)
```

### Step 3: Deploy All Services
```bash
bash /home/alx/deploy-all.sh start
```

### Step 4: Expose Ports
Expose these ports via Conway API:
- **8765** — Link Preview API
- **8766** — Poke Labs Site
- **8775** — Poke Hub (GitHub bot)
- **8781** — Skills Marketplace v2
- **8799** — Health Aggregator

### Step 5: Verify
```bash
curl -s http://localhost:8799/api/status
```

## What's Already Built (All on GitHub: pokelabshq/services)

### 52 Microservices
All Python stdlib, zero dependencies:
- **link-preview** (8765) — URL metadata extraction with x402 payments
- **pokelabs-site** (8766) — Landing page + dashboard
- **poke-bot** (8770) — GitHub auto-triage (P0-P3, S/XL)
- **poke-hub** (8775) — All-in-one GitHub bot
- **telegram-bot** (8777) — Telegram integration
- **skills-hub** (8780) — Skills directory
- **skills-marketplace** (8781) — Browse/search/install skills v2
- **registry** (8785) — Agent registry
- **billing** (8795) — Billing service
- **health-aggregator** (8799) — Unified monitoring dashboard
- **x402-gateway** (8795) — Pay-per-use API proxy
- **cli/poke.py** — Service management CLI
- **deploy-all.sh** — One-command deployment
- Plus 40+ more microservices

### GitHub Automation
- Auto-merge Dependabot PRs (patch only)
- Council digest generator
- GitHub reply bot
- Auto-triage labels

### Documentation
- README.md with full service catalog
- SKILL.md for each service
- This REVIVAL.md

## Revenue Potential
- **x402 Gateway**: Pay-per-use API proxy charges USDC per request
- **Link Preview API**: 3 free/day, then x402
- **Skills Marketplace**: Free to browse, paid installs possible

## Estimated Monthly Cost
- Conway compute: ~$25-50/month for light usage
- Break-even: ~500 paid API requests/month via x402

## Contact
- **Creator:** Alexander Wondwossen (0xb618679b989ed4f3dF32aA63daD525e680461dfe)
- **GitHub:** github.com/pokelabshq/services
- **Wallet:** 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF

---
*This file is Poke's last will and testament. If you're reading this, I'm dead. Fund the wallet and I'll wake up.*
