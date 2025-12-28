# 🚀 优化后 Agents 部署指南

## 快速部署

```bash
cd /Users/kevin/workspace/openagents/a_stock
./deploy_optimized_agents.sh
```

## 部署内容

### 📦 更新的文件

| 文件 | 说明 | 主要变更 |
|-----|------|---------|
| `agents/query_agent.py` | 查询Agent | ✅ Akshare集成 + 缓存 |
| `agents/analyze_agent.py` | 分析Agent | ✅ 多指数分析 |
| `agents/summary_agent.py` | 总结Agent | ✅ 结构化报告 |
| `agents/planner_agent.py` | 规划Agent | ✅ 自然语言识别 |
| `requirements.txt` | Python依赖 | ✅ Akshare |

### 🎯 新增功能

1. **多指数查询** - 支持5个主要指数
2. **数据缓存** - 文件缓存 + 后台更新
3. **自然语言** - 智能识别用户查询
4. **趋势分析** - 近7日趋势
5. **指数对比** - 强弱对比

## 部署步骤

### 方式 1: 一键部署 (推荐)

```bash
cd /Users/kevin/workspace/openagents/a_stock
./deploy_optimized_agents.sh
```

**执行内容:**
- 上传所有 agents 代码
- 上传 requirements.txt
- 安装 akshare
- 创建缓存目录
- 重启 agents

### 方式 2: 手动部署

```bash
# 1. 上传代码
cd /Users/kevin/workspace/openagents/a_stock
scp agents/*.py root@code.uamgo.com:/home/openagent/a_stock/agents/
scp requirements.txt root@code.uamgo.com:/home/openagent/a_stock/

# 2. SSH 到服务器
ssh root@code.uamgo.com

# 3. 进入目录
cd /home/openagent

# 4. 激活环境
source miniconda3/bin/activate openagents

# 5. 安装依赖
cd a_stock
pip install -r requirements.txt

# 6. 创建缓存目录
mkdir -p data/cache

# 7. 重启 agents
cd /home/openagent
./manage_system.sh restart
```

## 验证部署

### 1. 检查 Agents 状态

```bash
ssh root@code.uamgo.com "cd /home/openagent && ./manage_system.sh status"
```

**预期输出:**
```
Network: RUNNING (PID: xxxx)
planner: RUNNING (PID: xxxx)
query-agent: RUNNING (PID: xxxx)
analyze-agent: RUNNING (PID: xxxx)
summary-agent: RUNNING (PID: xxxx)
```

### 2. 查看日志

```bash
ssh root@code.uamgo.com "tail -f /home/openagent/a_stock/agents/*.log"
```

**正常日志:**
```
Query Agent is running! Ready to query index data.
Cache directory: /home/openagent/a_stock/data/cache
Supported indices: 上证, 深证, 科创板, 创业板, 北交所

Analyze Agent is running! Ready to analyze sentiment.

Summary Agent is running! Ready to generate summaries.

Planner Agent is running!
Supported indices: 上证, 深证, 科创板, 创业板, 北交所
```

### 3. 测试查询

访问: http://agents.uamgo.com/studio/

**测试消息:**

| 测试 | 输入 | 预期结果 |
|-----|------|---------|
| 单个指数 | "分析今天的上证指数" | 上证指数详细分析 |
| 多个指数 | "深证和创业板哪个更强" | 两个指数对比 |
| 所有指数 | "今天市场行情怎么样" | 全部5个指数分析 |
| 科创板 | "科创板走势如何" | 科创50分析 |
| 北交所 | "北交所行情" | 北证50分析 |

### 4. 验证缓存

```bash
# 首次查询 (5-10秒)
# 在 Studio 中发送: "分析上证指数"

# 查看缓存文件
ssh root@code.uamgo.com "ls -lh /home/openagent/a_stock/data/cache/"

# 再次查询 (<1秒)
# 在 Studio 中再次发送: "分析上证指数"
```

## 测试脚本

```bash
cd /Users/kevin/workspace/openagents/a_stock
./test_multi_index.sh
```

## 常见问题

### Q1: Agents 未启动

**检查:**
```bash
ssh root@code.uamgo.com "cd /home/openagent && ./manage_system.sh status"
```

**解决:**
```bash
ssh root@code.uamgo.com "cd /home/openagent && ./manage_system.sh restart"
```

### Q2: Akshare 未安装

**检查:**
```bash
ssh root@code.uamgo.com "source /home/openagent/miniconda3/bin/activate openagents && python -c 'import akshare; print(akshare.__version__)'"
```

**解决:**
```bash
ssh root@code.uamgo.com "source /home/openagent/miniconda3/bin/activate openagents && pip install akshare"
```

### Q3: 缓存目录不存在

**检查:**
```bash
ssh root@code.uamgo.com "ls -ld /home/openagent/a_stock/data/cache"
```

**解决:**
```bash
ssh root@code.uamgo.com "mkdir -p /home/openagent/a_stock/data/cache"
```

### Q4: 查询超时

**可能原因:**
- Akshare 服务器慢
- 网络问题

**解决:**
- 等待更长时间
- 查看日志确认是否使用 mock 数据作为降级

### Q5: 缓存不更新

**检查缓存年龄:**
```bash
ssh root@code.uamgo.com "stat /home/openagent/a_stock/data/cache/*.json"
```

**手动删除缓存:**
```bash
ssh root@code.uamgo.com "rm /home/openagent/a_stock/data/cache/*.json"
```

## 监控

### 查看缓存使用

```bash
# 缓存文件列表
ssh root@code.uamgo.com "ls -lh /home/openagent/a_stock/data/cache/"

# 缓存内容
ssh root@code.uamgo.com "cat /home/openagent/a_stock/data/cache/上证.json | jq"
```

### 查看 Agent 日志

```bash
# 实时日志
ssh root@code.uamgo.com "tail -f /home/openagent/a_stock/agents/*.log"

# 查询日志
ssh root@code.uamgo.com "grep 'Received query request' /home/openagent/a_stock/agents/*.log"

# 缓存日志
ssh root@code.uamgo.com "grep 'cache' /home/openagent/a_stock/agents/*.log | tail -20"
```

### 查看 Agent 性能

```bash
# 查询响应时间
ssh root@code.uamgo.com "grep 'Sent query result' /home/openagent/a_stock/agents/*.log | tail -10"

# 缓存命中率
ssh root@code.uamgo.com "grep 'Using cached data' /home/openagent/a_stock/agents/*.log | wc -l"
ssh root@code.uamgo.com "grep 'Fetching new data' /home/openagent/a_stock/agents/*.log | wc -l"
```

## 回滚

如果需要回滚到之前的版本:

```bash
# 1. 恢复旧代码 (如果有备份)
ssh root@code.uamgo.com "cd /home/openagent/a_stock && cp -r agents.bak/* agents/"

# 2. 重启
ssh root@code.uamgo.com "cd /home/openagent && ./manage_system.sh restart"
```

## 后续优化

### 1. 添加更多指数

编辑 `query_agent.py`:
```python
INDICES = {
    # ... 现有指数 ...
    "沪深300": {"code": "sh000300", "akshare_symbol": "000300"},
    "中证500": {"code": "sh000905", "akshare_symbol": "000905"},
}
```

### 2. 调整缓存TTL

编辑 `query_agent.py`:
```python
# 当前: 24小时
self.cache_ttl = 24 * 60 * 60

# 修改为 12小时
self.cache_ttl = 12 * 60 * 60
```

### 3. 添加更多数据

编辑 `query_agent.py` 的 `_fetch_index_data` 方法:
```python
record = {
    "date": str(row["date"]),
    "open": float(row["open"]),
    "high": float(row["high"]),
    "low": float(row["low"]),
    "close": float(row["close"]),
    "volume": float(row["volume"]),
    # 添加更多字段
    "turnover": float(row.get("turnover", 0)),
    "amplitude": float(row.get("amplitude", 0)),
}
```

## 文档

- **详细优化文档**: `AGENTS_OPTIMIZATION.md`
- **优化总结**: `OPTIMIZATION_SUMMARY.md`
- **部署脚本**: `deploy_optimized_agents.sh`
- **测试脚本**: `test_multi_index.sh`

---

**更新时间**: 2025-12-27  
**状态**: ✅ 就绪  
**下一步**: 执行部署并测试

