#!/bin/bash
# OpenAgents Stock Analysis System - Stop Script
# 停止所有服务

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=================================="
echo "Stopping OpenAgents Services"
echo "=================================="
echo ""

# Stop all agent processes
echo -e "${RED}🛑 Stopping all agents...${NC}"
if pgrep -f "python.*agent" > /dev/null; then
    pkill -9 -f "python.*agent"
    echo "   ✓ Agents stopped"
else
    echo "   ℹ️  No agent processes found"
fi

# Stop network server
echo -e "${RED}🛑 Stopping network server...${NC}"
if pgrep -f "openagents.*network" > /dev/null; then
    pkill -9 -f "openagents.*network"
    echo "   ✓ Network server stopped"
else
    echo "   ℹ️  No network server found"
fi

# Stop WebSocket proxy (if running)
echo -e "${RED}🛑 Stopping WebSocket proxy...${NC}"
if pgrep -f "simple_ws_proxy" > /dev/null; then
    pkill -9 -f "simple_ws_proxy"
    echo "   ✓ WebSocket proxy stopped"
else
    echo "   ℹ️  No WebSocket proxy found"
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""

