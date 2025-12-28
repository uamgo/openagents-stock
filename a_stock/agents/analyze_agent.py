#!/usr/bin/env python3
"""
Analyze Agent - Worker agent for analyzing multiple indices sentiment.

Features:
- Analyze multiple indices
- Compare indices performance
- Identify trends and patterns

Usage:
    OPENAI_API_KEY=your-key python agents/analyze_agent.py
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.worker_agent import WorkerAgent
from openagents.models.event_context import EventContext
from openagents.models.event import Event
from openagents.models.agent_config import AgentConfig


class AnalyzeAgent(WorkerAgent):
    """Agent that analyzes market sentiment for multiple indices."""

    default_agent_id = "analyze-agent"

    def __init__(self, group=None, **kwargs):
        # Create agent config with LLM settings for deeper analysis
        agent_config = AgentConfig(
            instruction="""你是一个多指数市场情绪分析专家。

你的任务：分析多个指数的市场情绪并进行对比。

分析维度：
1. 单个指数情绪 - 根据涨跌幅判断
2. 市场整体情绪 - 综合多个指数
3. 指数对比 - 哪些强势，哪些弱势
4. 趋势分析 - 近期走势

情绪等级：
- 乐观 (Optimistic): change > 1.5%
- 偏乐观 (Slightly Optimistic): 0.5% < change ≤ 1.5%
- 中性 (Neutral): -0.5% ≤ change ≤ 0.5%
- 偏悲观 (Slightly Pessimistic): -1.5% ≤ change < -0.5%
- 悲观 (Pessimistic): change < -1.5%

输出格式：
- sentiment: 整体情绪
- confidence: 置信度
- reasoning: 分析依据
- indices_analysis: 各指数详细分析
- comparison: 指数对比
""",
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        super().__init__(agent_config=agent_config, **kwargs)

    async def on_startup(self):
        """Called when agent starts."""
        if not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not set. Will use rule-based analysis.")
        print("Analyze Agent is running! Ready to analyze sentiment.")

    async def on_shutdown(self):
        """Called when agent shuts down."""
        print("Analyze Agent stopped.")

    async def react(self, context: EventContext):
        """
        React to analyze requests.
        
        Expected event payload:
        {
            "type": "analyze_request",
            "indices_data": {...},
            "reply_to": "planner"
        }
        """
        event = context.incoming_event

        # Skip our own messages
        if event.source_id == self.agent_id:
            return

        # Check if this is an analyze request
        if event.payload.get("type") != "analyze_request":
            return

        indices_data = event.payload.get("indices_data")
        reply_to = event.payload.get("reply_to") or event.source_id

        print(f"Received analyze request for {len(indices_data.get('indices', {}))} indices")

        # Analyze sentiment
        analysis_result = await self._analyze_indices(indices_data)

        # Send result back
        await self._send_result(reply_to, analysis_result)

    async def _analyze_indices(self, indices_data: Dict) -> Dict:
        """
        Analyze multiple indices sentiment.
        
        Args:
            indices_data: Dict with indices data
            
        Returns:
            Analysis result dict
        """
        indices = indices_data.get("indices", {})
        
        # Analyze each index
        indices_analysis = {}
        for index_name, index_data in indices.items():
            indices_analysis[index_name] = self._analyze_single_index(index_name, index_data)
        
        # Calculate overall sentiment
        overall = self._calculate_overall_sentiment(indices_analysis)
        
        # Compare indices
        comparison = self._compare_indices(indices_analysis)
        
        # Analyze trends
        trends = self._analyze_trends(indices)
        
        return {
            "timestamp": indices_data.get("timestamp"),
            "overall_sentiment": overall["sentiment"],
            "overall_confidence": overall["confidence"],
            "overall_reasoning": overall["reasoning"],
            "indices_analysis": indices_analysis,
            "comparison": comparison,
            "trends": trends,
        }

    def _analyze_single_index(self, index_name: str, index_data: Dict) -> Dict:
        """Analyze single index sentiment."""
        data_list = index_data.get("data", [])
        
        if not data_list:
            return {
                "sentiment": "未知",
                "confidence": 0,
                "reasoning": ["无数据"],
            }
        
        # Use latest data
        latest = data_list[-1]
        change_pct = latest.get("change_pct", 0)
        
        # Calculate sentiment
        if change_pct > 1.5:
            sentiment = "乐观"
            confidence = 0.85
            reasoning = [
                f"{index_name}涨幅{change_pct:.2f}%，超过1.5%",
                "市场表现强势",
            ]
        elif change_pct > 0.5:
            sentiment = "偏乐观"
            confidence = 0.70
            reasoning = [
                f"{index_name}涨幅{change_pct:.2f}%，温和上涨",
            ]
        elif change_pct > -0.5:
            sentiment = "中性"
            confidence = 0.75
            reasoning = [
                f"{index_name}涨跌{change_pct:.2f}%，窄幅震荡",
            ]
        elif change_pct > -1.5:
            sentiment = "偏悲观"
            confidence = 0.70
            reasoning = [
                f"{index_name}跌幅{change_pct:.2f}%，略有调整",
            ]
        else:
            sentiment = "悲观"
            confidence = 0.85
            reasoning = [
                f"{index_name}跌幅{change_pct:.2f}%，超过-1.5%",
                "市场承压明显",
            ]
        
        # Calculate 7-day trend
        trend = self._calculate_trend(data_list)
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": reasoning,
            "latest_close": latest.get("close"),
            "change_pct": change_pct,
            "trend_7d": trend,
        }

    def _calculate_overall_sentiment(self, indices_analysis: Dict) -> Dict:
        """Calculate overall market sentiment."""
        sentiments = []
        change_pcts = []
        
        for analysis in indices_analysis.values():
            sentiments.append(analysis["sentiment"])
            change_pcts.append(analysis["change_pct"])
        
        if not change_pcts:
            return {
                "sentiment": "未知",
                "confidence": 0,
                "reasoning": ["无数据"],
            }
        
        # Average change
        avg_change = sum(change_pcts) / len(change_pcts)
        
        # Determine overall sentiment
        positive_count = sum(1 for pct in change_pcts if pct > 0.5)
        negative_count = sum(1 for pct in change_pcts if pct < -0.5)
        total_count = len(change_pcts)
        
        if positive_count >= total_count * 0.7:
            sentiment = "市场整体乐观"
            confidence = 0.85
            reasoning = [
                f"平均涨幅{avg_change:.2f}%",
                f"{positive_count}/{total_count}个指数上涨",
                "多数指数表现强势",
            ]
        elif positive_count >= total_count * 0.5:
            sentiment = "市场偏向乐观"
            confidence = 0.70
            reasoning = [
                f"平均涨幅{avg_change:.2f}%",
                f"{positive_count}/{total_count}个指数上涨",
            ]
        elif negative_count >= total_count * 0.7:
            sentiment = "市场整体悲观"
            confidence = 0.85
            reasoning = [
                f"平均跌幅{avg_change:.2f}%",
                f"{negative_count}/{total_count}个指数下跌",
                "多数指数承压",
            ]
        elif negative_count >= total_count * 0.5:
            sentiment = "市场偏向悲观"
            confidence = 0.70
            reasoning = [
                f"平均跌幅{avg_change:.2f}%",
                f"{negative_count}/{total_count}个指数下跌",
            ]
        else:
            sentiment = "市场分化明显"
            confidence = 0.75
            reasoning = [
                f"平均涨跌{avg_change:.2f}%",
                "指数表现分化，需关注板块差异",
            ]
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    def _compare_indices(self, indices_analysis: Dict) -> Dict:
        """Compare indices performance."""
        # Sort by change_pct
        sorted_indices = sorted(
            indices_analysis.items(),
            key=lambda x: x[1]["change_pct"],
            reverse=True
        )
        
        strongest = []
        weakest = []
        
        # Only compare if we have more than 2 indices
        if len(sorted_indices) <= 2:
            # If 2 or fewer indices, just list them
            for name, analysis in sorted_indices:
                strongest.append({
                    "name": name,
                    "change_pct": analysis["change_pct"],
                    "sentiment": analysis["sentiment"],
                })
        else:
            # Top 2 strongest
            for i in range(min(2, len(sorted_indices))):
                name, analysis = sorted_indices[i]
                strongest.append({
                    "name": name,
                    "change_pct": analysis["change_pct"],
                    "sentiment": analysis["sentiment"],
                })
            
            # Bottom 2 weakest (from the end)
            for i in range(max(0, len(sorted_indices) - 2), len(sorted_indices)):
                name, analysis = sorted_indices[i]
                weakest.append({
                    "name": name,
                    "change_pct": analysis["change_pct"],
                    "sentiment": analysis["sentiment"],
                })
        
        return {
            "strongest": strongest,
            "weakest": weakest,
        }

    def _calculate_trend(self, data_list: List[Dict]) -> Dict:
        """Calculate trend from data list."""
        if len(data_list) < 2:
            return {"direction": "unknown", "strength": 0}
        
        # Calculate changes
        changes = [d["change_pct"] for d in data_list if "change_pct" in d]
        
        if not changes:
            return {"direction": "unknown", "strength": 0}
        
        # Count positive/negative days
        positive_days = sum(1 for c in changes if c > 0)
        negative_days = sum(1 for c in changes if c < 0)
        total_days = len(changes)
        
        # Determine direction
        if positive_days > total_days * 0.6:
            direction = "上升"
            strength = positive_days / total_days
        elif negative_days > total_days * 0.6:
            direction = "下降"
            strength = negative_days / total_days
        else:
            direction = "震荡"
            strength = 0.5
        
        # Calculate cumulative change
        first_close = data_list[0]["close"]
        last_close = data_list[-1]["close"]
        cumulative_change = ((last_close - first_close) / first_close) * 100
        
        return {
            "direction": direction,
            "strength": round(strength, 2),
            "cumulative_change_pct": round(cumulative_change, 2),
            "positive_days": positive_days,
            "negative_days": negative_days,
            "total_days": total_days,
        }

    def _analyze_trends(self, indices: Dict) -> Dict:
        """Analyze trends across all indices."""
        trends = {}
        
        for index_name, index_data in indices.items():
            data_list = index_data.get("data", [])
            if data_list:
                trends[index_name] = self._calculate_trend(data_list)
        
        return trends

    async def _send_result(self, target_agent: str, data: Dict):
        """Send analysis result to target agent."""
        event = Event(
            event_name="stock.analyze.response",
            destination_id=target_agent,
            source_id=self.agent_id,
            payload={
                "type": "analyze_response",
                "data": data,
                "source": self.agent_id,
            },
        )
        await self.client.send_event(event)
        print(f"Sent analysis result to {target_agent}")


async def main():
    """Run the analyze agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument(
        "--url",
        default=None,
        help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)",
    )
    args = parser.parse_args()

    agent = AnalyzeAgent()

    try:
        if args.url:
            await agent.async_start(url=args.url)
        else:
            await agent.async_start(
                network_host=args.host,
                network_port=args.port,
            )

        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())
