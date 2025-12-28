# OpenAgents 股票分析系统 - 项目总结

## 📊 项目概述

基于 OpenAgents 框架的多智能体股票分析系统，集成真实 akshare 数据源，支持 5 大中国股市指数的实时数据分析。

## ✨ 核心功能

### 1. 多智能体架构
- **Query Agent**: 从 akshare 获取真实指数数据
- **Analyze Agent**: 分析市场情绪和趋势
- **Planner Agent**: 协调工作流和任务分配
- **Summary Agent**: 生成综合分析报告

### 2. 支持的指数
| 指数 | 代码 | 最新价格 | 状态 |
|------|------|----------|------|
| 上证指数 | sh000001 | 3963.68 | ✅ |
| 深证成指 | sz399001 | 13603.89 | ✅ |
| 科创50 | sh000688 | 1345.83 | ✅ |
| 创业板指 | sz399006 | 3243.88 | ✅ |
| 北证50 | bj899050 | 1463.04 | ✅ |

### 3. 通信方式
- **MCP 协议**: Agent 间通信（端口 8700）
- **WebSocket**: 与客户端通信（端口 8702）
- **RESTful API**: HTTP 接口

## 🏗️ 技术架构

```
┌─────────────────┐
│  StockTaskApp   │  ← 客户端 (Android/Kotlin)
└────────┬────────┘
         │ WebSocket (8702)
         ↓
┌─────────────────┐
│  WS Proxy (MCP) │  ← WebSocket → MCP 桥接
└────────┬────────┘
         │ MCP (8700)
         ↓
┌─────────────────┐
│ Network Server  │  ← OpenAgents 网络层
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ↓         ↓        ↓        ↓
┌────────┐┌─────────┐┌────────┐┌─────────┐
│ Query  ││Analyze  ││Planner ││Summary  │
│ Agent  ││Agent    ││Agent   ││Agent    │
└────┬───┘└────┬────┘└───┬────┘└────┬────┘
     │         │          │          │
     └─────────┴──────────┴──────────┘
              ↓
        akshare API
```

## 🚀 快速开始

### 本地开发
```bash
# 启动所有服务
cd a_stock
./start_all.sh

# 停止所有服务
./stop_all.sh
```

### 生产部署
```bash
# SSH 到服务器
ssh root@code.uamgo.com

# 启动服务 (使用 setsid 避免挂起)
cd /home/openagent/a_stock
bash start_all.sh

# 检查服务状态
ps aux | grep -E 'agent|openagents'

# 查看日志
tail -f logs/planner.log
```

## 📝 配置文件

### network.yaml
```yaml
name: StockAnalysisNetwork
port: 8700
topology: centralized
groups:
  - name: guest
    agents:
      - query-agent
      - analyze-agent
      - planner
      - summary-agent
```

### Nginx 配置
```nginx
# /etc/nginx/sites-available/agents.uamgo.com.conf
server {
    listen 80;
    server_name agents.uamgo.com;
    
    location / {
        proxy_pass http://localhost:8700;
    }
}
```

## 🔧 开发规范

### 远程服务启动
```bash
# ✅ 正确方式 - 使用 setsid
ssh user@host "setsid bash -c 'cd /path && command > logs/service.log 2>&1' &"

# ❌ 错误方式 - 使用 nohup 会挂起
ssh user@host "nohup command > logs/service.log 2>&1 &"
```

### 数据缓存策略
- **TTL**: 24 小时
- **自动更新**: 后台线程
- **降级策略**: 使用缓存数据

## 📊 性能指标

- **响应时间**: < 5 秒
- **数据更新**: 每日自动更新
- **并发支持**: 多客户端同时连接
- **错误处理**: 自动降级到缓存数据

## 🔗 相关链接

- **生产环境**: http://agents.uamgo.com
- **MCP Endpoint**: http://agents.uamgo.com/mcp
- **WebSocket**: ws://agents.uamgo.com:8702
- **文档**: 
  - [README.md](README.md) - 项目概述
  - [USER_GUIDE.md](USER_GUIDE.md) - 用户指南
  - [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署指南
  - [QUICKSTART.md](QUICKSTART.md) - 快速入门

## 📦 依赖项

```
openagents>=0.4.0
akshare>=1.13.0
websockets>=12.0
pyyaml>=6.0
```

## 🎯 未来计划

- [ ] 支持更多指数（北向资金、行业板块等）
- [ ] 添加技术指标分析（MACD, RSI 等）
- [ ] 实时推送功能
- [ ] 历史数据回测
- [ ] 增加 AI 预测模型

## 👥 团队

- **开发**: Kevin
- **框架**: OpenAgents
- **数据源**: akshare

## 📄 许可证

MIT License

---

**最后更新**: 2025-12-28
**版本**: 1.0.0

