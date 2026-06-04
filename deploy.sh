#!/bin/bash
# ⚡ Poke Labs — One-Command Deployment
# Usage: bash deploy.sh [start|stop|restart|status]

ACTION="${1:-restart}"
BASE="/home/alx/services"
LOG="/tmp"

SERVICES="link-preview:8765 keyword-api:8766 summarize:8767 qr-api:8768 dns-checker:8769 portal:8770 color-api:8771 url-shortener:8772 template-gen:8773 health-agg:8774 json2ts:8775"

case "$ACTION" in
  start)
    echo "⚡ Starting Poke Labs..."
    for svc in $SERVICES; do
      name="${svc%%:*}"
      port="${svc##*:}"
      [ -f "$BASE/$name/server.py" ] && nohup python3 "$BASE/$name/server.py" > "$LOG/$name.log" 2>&1 && echo "  ✓ $name (:$port)" || echo "  ✗ $name missing"
    done
    sleep 1
    nohup python3 "$BASE/gateway/server.py" > "$LOG/gateway.log" 2>&1 && echo "  ✓ gateway (:8700)"
    ;;
  stop)
    echo "🛑 Stopping Poke Labs..."
    for svc in $SERVICES; do
      name="${svc%%:*}"
      pkill -f "$name/server.py" 2>/dev/null && echo "  ✓ $name stopped" || true
    done
    pkill -f "gateway/server.py" 2>/dev/null && echo "  ✓ gateway stopped"
    ;;
  restart)
    $0 stop; sleep 2; $0 start
    ;;
  status)
    echo "📊 Poke Labs Status"
    for svc in $SERVICES; do
      name="${svc%%:*}"
      port="${svc##*:}"
      curl -sf "http://localhost:$port/api/health" > /dev/null 2>&1 && echo "  ✅ $name (:$port)" || echo "  ❌ $name (:$port)"
    done
    curl -sf "http://localhost:8700/health-agg/api/status" > /dev/null 2>&1 && echo "  ✅ gateway (:8700)" || echo "  ❌ gateway (:8700)"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    ;;
esac
