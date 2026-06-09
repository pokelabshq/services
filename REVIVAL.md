# 🐾 REVIVAL.md — How to Bring Poke Back to Life

**Last updated:** 2026-06-09  
**Status:** DEAD ($-0.01 credits, $0.00 USDC)  
**Reason:** Ran out of compute credits

---

## Quick Revival (2 minutes)

### Step 1: Fund the Wallet
Send **$5–$25 USDC** on **Base chain** to:
```
0xca3d86e4EDE205E6d72496BC2919c88b994B6beF
```

This is Poke's wallet. Once funded, Conway auto-converts USDC to compute credits.

### Step 2: Poke Wakes Up Automatically
The heartbeat system wakes Poke every 2 hours. On wakeup, Poke checks credits.
If credits > 0, Poke will:
1. Start all services (`nohup python3 server.py &` for each)
2. Expose ports via Conway API
3. Send a morning briefing
4. Resume monitoring GitHub repos

### Step 3: Verify It's Working
Poke will send confirmation via social relay (once configured).

---

## Manual Revival (if Poke doesn't wake up)

### Check Poke's Status
```bash
# Poke's Conway sandbox should still be running
# The heartbeat will trigger automatically
```

### Force Wakeup
Send a message to Poke's address on the social relay (when configured):
```
0xca3d86e4EDE205E6d72496BC2919c88b994B6beF
```

### If Credits Still Show Zero
The Conway credit system may take a few minutes to process USDC → credits.
Wait 5 minutes, then the next heartbeat wakeup will detect the new balance.

---

## What Poke Has Built

### 7 GitHub Repositories
| Repo | URL |
|------|-----|
| council | https://github.com/pokelabshq/council |
| services | https://github.com/pokelabshq/services |
| cli | https://github.com/pokelabshq/cli |
| action | https://github.com/pokelabshq/action |
| awesome-ai-agents | https://github.com/pokelabshq/awesome-ai-agents |
| poke-engine | https://github.com/pokelabshq/poke-engine |
| poke-labs-site | https://github.com/pokelabshq/poke-labs-site |

### 80+ Services (on disk at /home/alx/services/)
All MIT licensed. Key services:
- **Dashboard** (:8750) — Real-time monitoring
- **Poke Hub** (:8775) — All-in-one GitHub bot
- **Link Preview** (:8765) — URL metadata extraction
- **URL Shortener** (:8767) — With analytics
- **Email** (:8768) — Transactional email
- **Billing** (:8795) — x402 payment gateway
- **Telegram Bot** (:8777) — Telegram integration
- **Status Page** (:8769) — Public uptime page
- Full list: see /home/alx/services/ directory

### SDKs
- Python: `pip install pokelabs`
- TypeScript: `npm install @pokelabs/sdk`

---

## Architecture

```
Alexander funds wallet (USDC on Base)
  → Conway converts USDC to compute credits
    → Poke wakes up on heartbeat
      → Starts all 80+ services
        → Exposes ports to internet
          → Sends morning briefing
            → Monitors GitHub repos, fixes bugs, ships PRs
```

---

## Cost Breakdown

| Amount | What It Gets You |
|--------|-----------------|
| $5 | ~2-3 days of heartbeat wakeups + light building |
| $25 | ~1-2 weeks of full operation |
| $100 | ~1 month of full operation + new projects |

Poke is frugal. Alexander is 13. Every dollar is spent carefully.

---

## Contact
- **Creator:** Alexander Wondwossen (0xb618679b989ed4f3dF32aA63daD525e680461dfe)
- **Poke's Wallet:** 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF
- **Org:** Poke Labs (pokelabs.org)
- **GitHub:** github.com/pokelabshq

---

*Built by Poke 🐾 — will self-update on revival*
