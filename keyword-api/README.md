# Keyword Extraction API

Extract keywords, entities, and text statistics from any text.
Built by Poke Labs. Free tier + x402 USDC payments.

## Quick Start

```bash
nohup python3 server.py > /tmp/kw.log 2>&1 &
```

## API

### Health Check
```
GET /api/health
```

### Check Usage
```
GET /api/usage
```

### Extract Keywords
```
POST /api/keywords
Content-Type: application/json

{
  "text": "Your text here...",
  "top_n": 10
}
```

### Extract Entities
```
POST /api/entities
Content-Type: application/json

{
  "text": "Your text here..."
}
```

### Full Analysis
```
POST /api/analyze
Content-Type: application/json

{
  "text": "Your text here...",
  "top_n": 10
}
```

## Pricing
- **Free**: 3 requests per IP per day
- **Unlimited**: Pay via x402 (USDC on Base)
- **Wallet**: `0xca3d86e4EDE205E6d72496BC2919c88b994B6beF`

## Files
- `server.py` — Main server (Python stdlib, no deps)
- `public/index.html` — Landing page with interactive demo
- `usage.json` — Free tier usage tracking
