#!/bin/bash
# deploy-all.sh — Start/stop all Poke Labs services
# Usage: ./deploy-all.sh start|stop|status|restart

SERVICES=(
  "link-preview:8765"
  "pokelabs-site:8766"
  "poke-bot:8770"
  "poke-hub:8775"
  "github-stats-api:8779"
  "skills-marketplace:8781"
  "registry:8785"
  "x402-gateway:8795"
  "health-aggregator:8799"
)
BASE="/home/alx/services"
LOGDIR="/tmp/poke-logs"
mkdir -p "$LOGDIR"

case "${1:-start}" in
  start)
    echo "🐾 Starting ${#SERVICES[@]} Poke Labs services..."
    for svc in "${SERVICES[@]}"; do
      name="${svc%%:*}"; port="${svc##*:}"
      pkill -f "$name/server.py" 2>/dev/null; sleep 0.5
      if [ -f "$BASE/$name/server.py" ]; then
        nohup python3 "$BASE/$name/server.py" > "$LOGDIR/$name.log" 2>&1 &
        echo "  ✅ $name → port $port (pid $!)"
      else
        echo "  ❌ $name — server.py not found"
      fi
    done
    echo "Done. Check http://localhost:8799/ for health dashboard."
    ;;
  stop)
    echo "🛑 Stopping all Poke Labs services..."
    for svc in "${SERVICES[@]}"; do
      name="${svc%%:*}"
      pkill -f "$name/server.py" 2>/dev/null
      echo "  ⬛ $name stopped"
    done
    ;;
  status)
    echo "📊 Service Status:"
    for svc in "${SERVICES[@]}"; do
      name="${svc%%:*}"; port="${svc##*:}"
      if curl -s --max-time 2 "http://localhost:$port/api/health" >/dev/null 2>&1; then
        echo "  ✅ $name (:$port) — UP"
      else
        echo "  ❌ $name (:$port) — DOWN"
      fi
    done
    ;;
  restart)
    $0 stop; sleep 2; $0 start
    ;;
  *)
    echo "Usage: $0 {start|stop|status|restart}"; exit 1
    ;;
esac
