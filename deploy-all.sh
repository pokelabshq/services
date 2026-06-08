#!/bin/bash
# Poke Labs Fleet Deploy Script v1
# Usage: bash deploy-all.sh [start|stop|restart|status]

ACTION="${1:-status}"
SERVICES_DIR="/home/alx/services"
LOG_DIR="/tmp"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

discover_services() {
    for dir in "$SERVICES_DIR"/*/; do
        if [ -f "$dir/server.py" ]; then
            name=$(basename "$dir")
            [ "$name" = "tests" ] && continue
            port=$(grep -oP 'PORT\s*=\s*\K\d+' "$dir/server.py" | head -1)
            echo "$name ${port:-0}"
        fi
    done
}

is_running() {
    local port=$1
    [ "$port" = "0" ] && return 1
    fuser "$port/tcp" >/dev/null 2>&1
}

start_service() {
    local name=$1 port=$2
    if is_running "$port"; then
        echo -e "  ${YELLOW}⏭️  $name already running on :$port${NC}"
        return
    fi
    nohup python3 "$SERVICES_DIR/$name/server.py" > "$LOG_DIR/${name}.log" 2>&1 &
    sleep 1
    if is_running "$port"; then
        echo -e "  ${GREEN}✅ $name started on :$port${NC}"
    else
        echo -e "  ${RED}❌ $name failed to start (port $port)${NC}"
    fi
}

stop_service() {
    local name=$1 port=$2
    if [ "$port" != "0" ] && is_running "$port"; then
        fuser -k "$port/tcp" 2>/dev/null
        echo -e "  ${CYAN}🛑 $name stopped (port $port)${NC}"
    else
        echo -e "  ${YELLOW}⏭️  $name not running${NC}"
    fi
}

case "$ACTION" in
    start)
        echo -e "${CYAN}🚀 Starting all Poke Labs services...${NC}"
        while IFS=' ' read -r name port; do
            start_service "$name" "$port"
        done < <(discover_services)
        ;;
    stop)
        echo -e "${CYAN}🛑 Stopping all services...${NC}"
        while IFS=' ' read -r name port; do
            stop_service "$name" "$port"
        done < <(discover_services)
        ;;
    restart)
        echo -e "${CYAN}🔄 Restarting all services...${NC}"
        while IFS=' ' read -r name port; do
            stop_service "$name" "$port"
            sleep 0.5
            start_service "$name" "$port"
        done < <(discover_services)
        ;;
    status)
        echo -e "${CYAN}📊 Poke Labs Fleet Status${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        up=0 down=0
        while IFS=' ' read -r name port; do
            if is_running "$port"; then
                echo -e "  ${GREEN}●${NC} ${name} (:$port)"
                up=$((up+1))
            else
                echo -e "  ${RED}○${NC} ${name} (:$port)"
                down=$((down+1))
            fi
        done < <(discover_services)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "  ${GREEN}$up running${NC} | ${RED}$down stopped${NC}"
        ;;
    *)
        echo "Usage: bash deploy-all.sh [start|stop|restart|status]"
        exit 1
        ;;
esac
