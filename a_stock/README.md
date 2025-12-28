# Stock Market Sentiment Analysis System

A distributed multi-agent system for analyzing stock market sentiment using OpenAgents.

## Overview

This system demonstrates sophisticated workflow orchestration using a distributed agent architecture where specialized agents collaborate to complete analysis tasks.

## Agents

| Agent | Type | Description |
|-------|------|-------------|
| `planner` | Python (LLM) | Orchestrates the workflow and coordinates worker agents |
| `query-agent` | Python | Queries stock index data |
| `analyze-agent` | Python (LLM) | Analyzes market sentiment with optional LLM enhancement |
| `summary-agent` | Python | Generates structured reports |

## Quick Start

### 1. Start the Network

```bash
openagents network start .
```

### 2. Access Studio

Open your browser to:
- **http://localhost:8700/studio/** - Studio web interface
- **http://localhost:8700/mcp** - MCP protocol endpoint

### 3. Start All Agents

**方式一：使用统一管理脚本（推荐）**

```bash
# 启动所有服务（网络 + agents）
./manage_system.sh start

# 查看状态
./manage_system.sh status

# 重启所有服务
./manage_system.sh restart

# 停止所有服务
./manage_system.sh stop
```

**方式二：使用单独脚本**

```bash
# Optional: Set your OpenAI API key for LLM-enhanced analysis
export OPENAI_API_KEY=your-api-key

# Start all agents
./start_agent_system.sh
```

This will start:
- **query-agent** - Queries index data
- **analyze-agent** - Analyzes sentiment
- **summary-agent** - Generates reports
- **planner** - Orchestrates the workflow

### 4. Test It!

In the `general` channel, send:
```
分析今天的市场情绪
```

Or:
```
查看昨天的市场情况
```

### 5. Management Commands

```bash
# 查看状态
./manage_system.sh status

# 重启系统
./manage_system.sh restart

# 停止系统
./manage_system.sh stop

# 查看日志
tail -f logs/planner.log
tail -f /home/openagent/logs/network.log
```

## Architecture

### 🌐 Agent-Based Architecture

Distributed multi-agent system where each agent has a specific responsibility:

```
User Request
     ↓
Planner Agent (coordinates workflow)
     ├─→ Query Agent (queries stock data)
     ├─→ Analyze Agent (analyzes sentiment)
     └─→ Summary Agent (generates report)
     ↓
Structured Report
```

**Benefits:**
- ✅ True distributed architecture
- ✅ Each agent can be scaled independently
- ✅ Easy to add new agents or replace existing ones
- ✅ Optional LLM enhancement for any agent
- ✅ Production-ready communication patterns

**Components:**

1. **Planner Agent** (`planner_agent.py`)
   - Receives user requests
   - Coordinates workflow execution
   - Sends requests to worker agents
   - Collects results and returns to user

2. **Query Agent** (`query_agent.py`)
   - Handles `query_request` events
   - Queries stock index data
   - Returns raw OHLC data

3. **Analyze Agent** (`analyze_agent.py`)
   - Handles `analyze_request` events
   - Analyzes market sentiment
   - Supports rule-based and LLM-enhanced analysis
   - Returns sentiment + confidence + reasoning

4. **Summary Agent** (`summary_agent.py`)
   - Handles `summary_request` events
   - Formats analysis into structured Blocks
   - Returns user-readable report

## Configuration

- **Network Port:** 8700 (HTTP), 8600 (gRPC)
- **Studio:** http://agents.uamgo.com/studio/ (via Nginx)
- **Studio (direct):** http://code.uamgo.com:8700/studio/
- **MCP:** http://agents.uamgo.com/mcp
- **Channel:** `general`

### Nginx Reverse Proxy

The system is configured with Nginx reverse proxy for unified domain access:

- **Domain:** agents.uamgo.com
- **Target:** localhost:8700
- **Config:** `/etc/nginx/sites-available/agents.uamgo.com.conf`

See [nginx/NGINX_SETUP.md](nginx/NGINX_SETUP.md) for details.

## Testing

### View Logs

```bash
# View all agent logs
tail -f logs/*.log

# View specific agent
tail -f logs/planner.log
```

### Test Messages

Send these in the chat:
- `分析今天的市场情绪` - Analyze today's market
- `查看昨天的市场情况` - Check yesterday's market
- `帮我分析一下市场` - Analyze the market

### Debug

```bash
# Check running agents
ps aux | grep python | grep agent

# Check PID files
ls -la logs/*.pid

# Check network status
curl http://localhost:8700/health
```

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute quick start guide |
| [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) | Detailed architecture design |
| [PLANNER_README.md](PLANNER_README.md) | Complete development guide |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing instructions |
| [INDEX.md](INDEX.md) | Documentation index |

## Agent Groups & Authentication

This network has several agent groups configured:

| Group | Password | Description |
|-------|----------|-------------|
| `guest` | (none) | Default group, no password required |
| `admin` | `admin` | Full permissions to all features |
| `coordinators` | `coordinators` | For router/coordinator agents |
| `researchers` | `researchers` | For worker/research agents |

### Logging in as Admin

To access admin features in Studio:

1. Open http://localhost:8700/studio/
2. Click on the group selector (or login)
3. Select group: **admin**
4. Enter password: **admin**

## Project Structure

```
a_stock/
├── agents/                      # Agent implementations
│   ├── planner_agent.py        # Planner (orchestrator)
│   ├── query_agent.py          # Query worker agent
│   ├── analyze_agent.py        # Analysis worker agent
│   └── summary_agent.py        # Summary worker agent
├── start_agent_system.sh       # Start all agents
├── stop_agent_system.sh        # Stop all agents
├── network.yaml                # Network configuration
└── docs/                       # Documentation
    ├── QUICKSTART.md
    ├── AGENT_ARCHITECTURE.md
    ├── PLANNER_README.md
    ├── TESTING_GUIDE.md
    └── INDEX.md
```

## Features

- ✅ Distributed multi-agent architecture
- ✅ Single responsibility principle for each agent
- ✅ Asynchronous message-based communication
- ✅ Structured output with Blocks format
- ✅ Optional LLM enhancement
- ✅ Production-ready patterns
- ✅ Comprehensive documentation
- ✅ Easy to extend with new agents

## Message Protocol

Agents communicate using structured events:

### Query Request
```json
{
  "type": "query_request",
  "date": "2025-12-26",
  "reply_to": "planner",
  "request_id": "req_xxx"
}
```

### Analyze Request
```json
{
  "type": "analyze_request",
  "index_data": {...},
  "reply_to": "planner",
  "request_id": "req_xxx"
}
```

### Summary Request
```json
{
  "type": "summary_request",
  "analysis_result": {...},
  "reply_to": "planner",
  "request_id": "req_xxx"
}
```

## Extending the System

### Add a New Worker Agent

1. Create a new agent file:
```python
# agents/forecast_agent.py
class ForecastAgent(WorkerAgent):
    default_agent_id = "forecast-agent"
    
    async def react(self, context: EventContext):
        if event.payload.get("type") == "forecast_request":
            # Handle forecast logic
            result = await self._forecast(data)
            await self._send_result(reply_to, result)
```

2. Update planner to use it:
```python
# In planner_agent.py
await self.client.send_event(
    target_id="forecast-agent",
    event_type="forecast_request",
    payload={...}
)
```

3. Add to startup script:
```bash
# In start_agent_system.sh
start_agent "forecast-agent" "forecast_agent.py"
```

## Next Steps

- Read [QUICKSTART.md](QUICKSTART.md) for a quick introduction
- Connect to real stock data APIs (tushare, akshare, etc.)
- Add more analysis indicators (RSI, MACD, KDJ, etc.)
- Implement caching for data queries
- Add error handling and retry logic
- Set up monitoring and alerting
- Scale agents horizontally for higher load

## Resources

- [OpenAgents Documentation](https://openagents.org/docs/)
- [OpenAgents GitHub](https://github.com/openagents)

---

**Built with OpenAgents** 🚀
