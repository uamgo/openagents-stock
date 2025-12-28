#!/bin/bash
# OpenAgents Stock Analysis System - Startup Script
# 启动所有服务：网络服务器 + 4个 Agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "OpenAgents Stock Analysis System"
echo "=================================="
echo ""

# Check if services are already running
if pgrep -f "openagents network start" > /dev/null; then
    echo -e "${YELLOW}⚠️  Network server is already running${NC}"
    echo "To restart, run: pkill -9 -f 'openagents.*network'"
    exit 1
fi

# Start network server
echo -e "${GREEN}🚀 Starting network server...${NC}"
/home/openagent/miniconda3/envs/openagents/bin/openagents network start network.yaml --port 8700 > logs/network.log 2>&1 &
NETWORK_PID=$!
echo "   Network PID: $NETWORK_PID"

# Wait for network to be ready
echo "   Waiting for network to initialize..."
sleep 5

# Start Query Agent
echo -e "${GREEN}🔍 Starting Query Agent...${NC}"
/home/openagent/miniconda3/envs/openagents/bin/python agents/query_agent.py --host localhost --port 8700 > logs/query-agent.log 2>&1 &
echo "   Query Agent PID: $!"

# Start Analyze Agent
echo -e "${GREEN}📊 Starting Analyze Agent...${NC}"
/home/openagent/miniconda3/envs/openagents/bin/python agents/analyze_agent.py --host localhost --port 8700 > logs/analyze-agent.log 2>&1 &
echo "   Analyze Agent PID: $!"

# Start Planner Agent
echo -e "${GREEN}🧠 Starting Planner Agent...${NC}"
/home/openagent/miniconda3/envs/openagents/bin/python agents/planner_agent.py --host localhost --port 8700 > logs/planner.log 2>&1 &
echo "   Planner Agent PID: $!"

# Start Summary Agent
echo -e "${GREEN}📝 Starting Summary Agent...${NC}"
/home/openagent/miniconda3/envs/openagents/bin/python agents/summary_agent.py --host localhost --port 8700 > logs/summary-agent.log 2>&1 &
echo "   Summary Agent PID: $!"

echo ""
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo ""
echo "Services:"
echo "  - Network Server: http://localhost:8700"
echo "  - MCP Endpoint: http://localhost:8700/mcp"
echo "  - WebSocket Proxy: ws://localhost:8702 (if running)"
echo ""
echo "Check logs:"
echo "  tail -f logs/network.log"
echo "  tail -f logs/planner.log"
echo ""
echo "Stop services:"
echo "  pkill -9 -f 'python.*agent'"
echo "  pkill -9 -f 'openagents.*network'"
echo ""

