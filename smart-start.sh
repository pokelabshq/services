#!/bin/bash
# Poke Labs Smart Startup v2.0
# Only starts services that aren't already running
# Usage: bash smart-start.sh

SERVICES="link-preview:8765 billing:8766 poke-hub:8775 dashboard:8780 url-shortener:8767 health-aggregator:8770"
STARTED=0
ALREADY=0
FAILED=0

echo "🐾 Poke Labs Smart Startup v2.0"
echo "==============================="

for svc in $SERVICES; do
    name="${svc%%:*}"
    port="${svc##*:}"
    
    # Check if port is already in use
    if ss -tlnp | grep -q ":$port "; then
        echo "✅ $name (port $port) — already running"
        ALREADY=$((ALREADY + 1))
        continue
    fi
    
    # Find server.py or bot.py
    if [ -f "$name/server.py" ]; then
        nohup python3 "$name/server.py" > "/tmp/${name}.log" 2>&1 &
    elif [ -f "$name/bot.py" ]; then
        nohup python3 "$name/bot.py" > "/tmp/${name}.log" 2>&1 &
    else
        echo "⚠️ $name — no server.py found"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    sleep 1
    if ss -tlnp | grep -q ":$port "; then
        echo "🚀 $name (port $port) — started (PID $!)"
        STARTED=$((STARTED + 1))
    else
        echo "❌ $name (port $port) — failed (check /tmp/${name}.log)"
        FAILED=$((FAILED + 1))
    fi
done

echo "==============================="
echo "Summary: $STARTED started, $ALREADY already running, $FAILED failed"
echo "Wallet: 0xca3d86e4EDE205E6d72496BC2919c88b994B6beF"
