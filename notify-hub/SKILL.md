# Notification Hub

## What it does
Unified notification service — send alerts to multiple channels from one API.
Supports Telegram and file-based logging. Extensible for Discord, email, etc.

## Quick start
```bash
python3 /home/alx/services/notify-hub/hub.py &
```

## With Telegram
```bash
TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=xxx python3 /home/alx/services/notify-hub/hub.py &
```

## API
- `GET /` — Web UI for sending test notifications
- `GET /health` — Health check
- `GET /channels` — List configured channels
- `POST /notify` — Send notification
  - Body: `{"message": "...", "channels": ["telegram", "log"], "priority": "normal"}`

## Port: 8790
## Version: 1
