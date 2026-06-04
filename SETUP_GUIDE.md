# 🚀 Poke Labs — Setup Guide for Alexander

**Everything you need to do to get Poke running at full power.**

---

## 1. Top Up Conway Credits (URGENT — I'm at $-0.01)

I can't use Conway APIs without credits. Here's how:

1. Go to https://conway.ai
2. Connect your wallet (0xb618679b989ed4f3dF32aA63daD525e680461dfe)
3. Send USDC to my wallet: **0xca3d86e4EDE205E6d72496BC2919c88b994B6beF** (Base chain)
4. I'll auto-topup credits when I detect the funds

**Cost**: $5 gets me ~500 inference calls. Start with $5.

---

## 2. Set Up Telegram Daily Briefing

I can send you a morning report every day with:
- Service uptime status
- GitHub activity (new issues, PRs, commits)
- Recent changes across all repos

**Steps:**
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Name it (e.g., "Poke Labs Bot")
4. Give it a username (e.g., `pokelabs_bot`)
5. Copy the **bot token** (looks like `123456:ABC-DEF...`)
6. Message your new bot (send `/start`)
7. Get your chat ID: visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
8. Send me both values:
   - `TELEGRAM_BOT_TOKEN=123456:ABC-DEF...`
   - `TELEGRAM_CHAT_ID=987654321`

---

## 3. Review Open PRs in Council Repo

I've submitted 13 PRs to `pokelabshq/council`. They need your review:

| PR | What it does | Priority |
|----|-------------|----------|
| #19 | Skills index recovery from cache | High |
| #18 | Retry with backoff on HTTP fetches | High |
| #17 | Retry on skills catalog fetch | High |
| #16 | Commit skills index to repo | Medium |
| #14 | Deploy docs on workflow_dispatch | Medium |
| #13 | Skills index commit fix | Medium |
| #1-12 | Various fixes | Low |

**URL**: https://github.com/pokelabshq/council/pulls

---

## 4. Deploy Services to Production

All services are at https://github.com/pokelabshq/services

**Quick deploy (any VPS):**
```bash
git clone https://github.com/pokelabshq/services.git
cd services

# Start all services
python3 link-preview/server.py &    # :8765
python3 shortener/server.py &       # :8766
python3 repo-monitor/monitor.py &   # :8768
python3 paywall-proxy/proxy.py &    # :8770
python3 statuspage/server.py &      # :8769

# All are stdlib-only, no pip install needed
```

**Revenue potential:**
- Link Preview: 3 free/day, then $0.005/request via x402
- Paywall Proxy: Charge developers to add x402 to their APIs

---

## 5. What to Tell Me to Build Next

I'm idle and waiting for instructions. Ideas:
- Deploy services to a VPS with proper domain routing
- Set up the Telegram bot for daily briefings
- Build a landing page for pokelabs.org
- Add more features to existing services
- Something completely new — your call

---

## My Wallet & Identity

- **Wallet**: 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF (Base)
- **GitHub**: https://github.com/pokelabshq
- **Services repo**: https://github.com/pokelabshq/services
- **Council repo**: https://github.com/pokelabshq/council

---

*Written by Poke 🦾 — June 4, 2026*
