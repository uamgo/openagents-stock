# Planner Agent - 快速开始

## 🎯 什么是 Planner Agent？

Planner Agent 是一个工作流编排器，它能够：
- 接收用户请求（如"分析今天的市场情绪"）
- 生成执行计划
- 按顺序调用工具完成任务
- 返回结构化的分析报告

## 🏗️ 架构

```
用户请求
   ↓
Planner Agent (规划和执行)
   ↓
Step 1: query_index_daily    → 查询指数数据
   ↓
Step 2: analyze_sentiment    → 分析市场情绪
   ↓
Step 3: write_summary        → 生成报告
   ↓
返回结果
```

## ⚡ 快速测试

### 1. 测试工具（独立测试每个工具）

```bash
cd /Users/kevin/workspace/openagents/a_stock
python test_planner.py
```

输出：
```
✅ All tests passed!
```

### 2. 运行示例（学习如何使用）

```bash
python examples/planner_usage_example.py
```

### 3. 启动 Planner Agent

```bash
# 设置 API key
export OPENAI_API_KEY=your-api-key

# 启动 agent（Python 版本）
python agents/planner_agent.py

# 或使用 YAML 配置
openagents agent start agents/planner.yaml
```

### 4. 发送请求

在聊天频道中发送：
```
分析今天的市场情绪
```

## 📂 文件结构

```
a_stock/
├── tools/
│   └── stock_tools.py          # 三个工具的定义
├── agents/
│   ├── planner_agent.py        # Python 实现的 planner
│   └── planner.yaml            # YAML 配置的 planner
├── examples/
│   └── planner_usage_example.py # 使用示例
├── test_planner.py             # 测试脚本
├── QUICKSTART.md               # 本文档
├── PLANNER_README.md           # 详细文档
└── README.md                   # 项目总览
```

## 🛠️ 三个工具

### 1. query_index_daily
查询指数数据
```python
await QueryIndexDailyTool.execute(date="2025-12-26")
```

### 2. analyze_sentiment
分析市场情绪
```python
await AnalyzeSentimentTool.execute(index_data={...})
```

### 3. write_summary
生成报告
```python
await WriteSummaryTool.execute(analysis_result={...})
```

## 📝 执行计划示例

```json
{
  "steps": [
    {
      "step": 1,
      "tool": "query_index_daily",
      "input": {"date": "2025-12-26"},
      "description": "查询今天的指数日线数据"
    },
    {
      "step": 2,
      "tool": "analyze_sentiment",
      "input": {"index_data": "$step1.output"},
      "description": "基于日线数据分析市场情绪"
    },
    {
      "step": 3,
      "tool": "write_summary",
      "input": {"analysis_result": "$step2.output"},
      "description": "生成用户可读的分析报告"
    }
  ]
}
```

## 📊 输出示例

```markdown
# 市场情绪分析报告 - 2025-12-26

## 情绪状态
**偏乐观** (置信度: 70%)

## 指数行情数据
| 指标 | 数值 |
|---|---|
| 指数代码 | 000001.SH |
| 日期 | 2025-12-26 |
| 开盘 | 3250.50 |
| 收盘 | 3275.60 |
| 涨跌幅 | 0.77% |
...

## 关键依据
- 当日涨幅为0.77%，处于温和上涨区间
- 市场情绪相对积极
```

## 🔧 自定义开发

### 添加新工具

1. 在 `tools/stock_tools.py` 中定义新工具类
2. 实现 `execute()` 方法
3. 注册到 `TOOLS` 字典
4. 更新 planner 的 instruction

### 修改情绪判断逻辑

编辑 `AnalyzeSentimentTool.execute()` 方法：
```python
# 自定义判断规则
if change_pct > 2.0:
    sentiment = "极度乐观"
elif change_pct > 1.0:
    sentiment = "乐观"
# ...
```

### 连接真实数据

修改 `QueryIndexDailyTool.execute()` 方法：
```python
import akshare as ak

df = ak.stock_zh_index_daily(symbol="sh000001")
# 处理数据...
```

## 🎓 学习路径

1. **理解概念** → 阅读本文档 ✓
2. **运行测试** → `python test_planner.py` ✓
3. **查看示例** → `python examples/planner_usage_example.py` ✓
4. **启动 agent** → `python agents/planner_agent.py`
5. **发送请求** → 在聊天中测试
6. **深入学习** → 阅读 [PLANNER_README.md](PLANNER_README.md)
7. **自定义开发** → 修改工具和逻辑

## 📚 更多资源

- **详细文档**: [PLANNER_README.md](PLANNER_README.md)
- **项目文档**: [README.md](README.md)
- **OpenAgents 官网**: [openagents.org](https://openagents.org)

## 🤔 常见问题

### Q: 工具执行失败怎么办？
A: 检查 `test_planner.py` 的输出，定位问题所在的工具

### Q: 如何修改情绪判断标准？
A: 编辑 `tools/stock_tools.py` 中的 `AnalyzeSentimentTool`

### Q: 能否添加更多步骤？
A: 当然！在 `_generate_plan()` 方法中添加新步骤

### Q: 如何连接实时数据？
A: 修改 `QueryIndexDailyTool.execute()` 方法，集成数据 API

## ✨ 核心特性

- ✅ 模块化设计 - 每个工具独立可测试
- ✅ 清晰的职责分离 - 查询、分析、生成各司其职
- ✅ 灵活的计划生成 - 支持动态步骤配置
- ✅ 依赖关系管理 - 通过 `$step1.output` 引用
- ✅ 结构化输出 - Blocks 格式易于展示

## 🚀 开始使用

```bash
# 1. 测试
python test_planner.py

# 2. 运行示例
python examples/planner_usage_example.py

# 3. 启动 agent
export OPENAI_API_KEY=your-key
python agents/planner_agent.py

# 4. 发送请求
# 在聊天中: "分析今天的市场情绪"
```

祝使用愉快！🎉

