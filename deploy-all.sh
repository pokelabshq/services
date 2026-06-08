#!/bin/bash
# Poke Labs — Deploy all services
# Usage: bash deploy-all.sh
# Requires: python3, no external deps

set -e

cd "$(dirname "$0")"
echo "🫧 Poke Labs — Deploying all services..."
echo ""

PORTS=()
STARTED=0
FAILED=0

for dir in poke-gateway poke-id poke-dashboard pokelabs-site link-preview skills-marketplace url-shortener qr-gen json2ts hash-gen color-api sentiment summarize status-page health-agg uptime-monitor metrics-exporter poke-hub poke-bot; do
    sdir="$dir"
    if [ ! -d "$sdir" ]; then continue; fi
    entry=""
    for f in server.py bot.py app.py main.py; do
        if [ -f "$sdir/$f" ]; then entry="$f"; break; fi
    done
    if [ -z "$entry" ]; then continue; fi
    
    # Extract port
    port=$(grep -oP 'PORT\s*=\s*\K\d{4,5}' "$sdir/$entry" 2>/dev/null || echo "")
    
    # Kill existing
    if [ -n "$port" ]; then
        fuser -k "$port/tcp" 2>/dev/null || true
    fi
    pkill -f "$sdir/$entry" 2>/dev/null || true
    sleep 0.5
    
    nohup python3 "$sdir/$entry" > "/tmp/${dir}.log" 2>&1 &
    
    if [ -n "$port" ]; then
        sleep 2
        if curl -s --max-time 3 "http://localhost:$port/api/health" > /dev/null 2>&1; then
            echo "  ✅ $dir → port $port"
            STARTED=$((STARTED + 1))
        else
            echo "  ❌ $dir → port $port (health check failed)"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "  ⚙️  $dir → no port/background"
        STARTED=$((STARTED + 1))
    fi
done

echo ""
echo "🫧 Done: $STARTED started, $FAILED failed"
echo "View logs: ls /tmp/*.log"
echo "Dashboard: http://localhost:8760"
