#!/usr/bin/env python3
"""
Summary Agent - Worker agent for generating multi-index summaries.

Features:
- Generate structured summaries for multiple indices
- Format analysis results into user-readable content
- Support comparison and trend visualization

Usage:
    python agents/summary_agent.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.worker_agent import WorkerAgent
from openagents.models.event_context import EventContext
from openagents.models.event import Event


class SummaryAgent(WorkerAgent):
    """Agent that generates summaries."""

    default_agent_id = "summary-agent"

    async def on_startup(self):
        """Called when agent starts."""
        print("Summary Agent is running! Ready to generate summaries.")

    async def on_shutdown(self):
        """Called when agent shuts down."""
        print("Summary Agent stopped.")

    async def react(self, context: EventContext):
        """
        React to summary requests.
        
        Expected event payload:
        {
            "type": "summary_request",
            "analysis_result": {...},
            "reply_to": "planner"
        }
        """
        event = context.incoming_event

        # Skip our own messages
        if event.source_id == self.agent_id:
            return

        # Check if this is a summary request
        if event.payload.get("type") != "summary_request":
            return

        analysis_result = event.payload.get("analysis_result")
        reply_to = event.payload.get("reply_to") or event.source_id

        print(f"Received summary request")

        # Generate summary
        summary = await self._generate_summary(analysis_result)

        # Send result back
        await self._send_result(reply_to, summary)

    async def _generate_summary(self, analysis_result: Dict) -> Dict:
        """
        Generate summary from analysis result.
        
        Args:
            analysis_result: Analysis result dict
            
        Returns:
            Summary dict with blocks
        """
        # Extract data
        overall_sentiment = analysis_result.get("overall_sentiment", "未知")
        overall_confidence = analysis_result.get("overall_confidence", 0)
        overall_reasoning = analysis_result.get("overall_reasoning", [])
        indices_analysis = analysis_result.get("indices_analysis", {})
        comparison = analysis_result.get("comparison", {})
        trends = analysis_result.get("trends", {})
        timestamp = analysis_result.get("timestamp", "")

        # Build structured blocks
        blocks = []

        # Header
        blocks.append({
            "type": "header",
            "content": f"📊 市场行情分析报告",
        })

        # Overall sentiment section
        blocks.append({
            "type": "section",
            "title": "整体市场情绪",
            "content": self._format_overall_sentiment(
                overall_sentiment,
                overall_confidence,
                overall_reasoning
            ),
        })

        # Indices performance table
        blocks.append(self._create_indices_table(indices_analysis))

        # Comparison section (only if multiple indices)
        if comparison:
            comparison_section = self._create_comparison_section(comparison)
            if comparison_section:  # Only add if not None
                blocks.append(comparison_section)

        # Trends section
        if trends:
            blocks.append(self._create_trends_section(trends))

        # Detailed analysis for each index
        blocks.extend(self._create_detailed_sections(indices_analysis))

        # Summary text (for simple display)
        summary_text = self._create_summary_text(analysis_result)

        return {
            "summary_text": summary_text,
            "blocks": blocks,
            "timestamp": timestamp,
        }

    def _format_overall_sentiment(
        self, sentiment: str, confidence: float, reasoning: List[str]
    ) -> str:
        """Format overall sentiment section."""
        lines = [
            f"**{sentiment}** (置信度: {confidence * 100:.0f}%)",
            "",
            "**分析依据:**",
        ]
        
        for reason in reasoning:
            lines.append(f"• {reason}")
        
        return "\n".join(lines)

    def _create_indices_table(self, indices_analysis: Dict) -> Dict:
        """Create indices performance table."""
        headers = ["指数", "最新", "涨跌幅", "情绪", "7日趋势"]
        rows = []

        for index_name, analysis in indices_analysis.items():
            latest_close = analysis.get("latest_close", 0)
            change_pct = analysis.get("change_pct", 0)
            sentiment = analysis.get("sentiment", "未知")
            trend = analysis.get("trend_7d", {})
            trend_direction = trend.get("direction", "未知")
            trend_change = trend.get("cumulative_change_pct", 0)

            # Format change with emoji
            change_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            change_str = f"{change_emoji} {change_pct:+.2f}%"

            # Format trend
            trend_str = f"{trend_direction} ({trend_change:+.2f}%)"

            rows.append([
                index_name,
                f"{latest_close:.2f}",
                change_str,
                sentiment,
                trend_str,
            ])

        return {
            "type": "table",
            "title": "各指数表现",
            "headers": headers,
            "rows": rows,
        }

    def _create_comparison_section(self, comparison: Dict) -> Optional[Dict]:
        """Create comparison section."""
        strongest = comparison.get("strongest", [])
        weakest = comparison.get("weakest", [])
        
        # 计算总的指数数量（去重）
        all_index_names = set()
        for idx in strongest:
            all_index_names.add(idx["name"])
        for idx in weakest:
            all_index_names.add(idx["name"])
        
        # 如果只有 1 个指数，不显示对比部分
        if len(all_index_names) <= 1:
            return None

        content_lines = []

        if strongest:
            content_lines.append("**💪 强势指数:**")
            for idx in strongest:
                name = idx["name"]
                change = idx["change_pct"]
                content_lines.append(f"• {name}: {change:+.2f}%")
            content_lines.append("")

        if weakest:
            content_lines.append("**📉 弱势指数:**")
            for idx in weakest:
                name = idx["name"]
                change = idx["change_pct"]
                content_lines.append(f"• {name}: {change:+.2f}%")

        return {
            "type": "section",
            "title": "指数对比",
            "content": "\n".join(content_lines),
        }

    def _create_trends_section(self, trends: Dict) -> Dict:
        """Create trends section."""
        content_lines = []

        for index_name, trend in trends.items():
            direction = trend.get("direction", "未知")
            strength = trend.get("strength", 0)
            cumulative = trend.get("cumulative_change_pct", 0)
            positive_days = trend.get("positive_days", 0)
            negative_days = trend.get("negative_days", 0)
            total_days = trend.get("total_days", 0)

            # Determine emoji
            if direction == "上升":
                emoji = "📈"
            elif direction == "下降":
                emoji = "📉"
            else:
                emoji = "↔️"

            content_lines.append(
                f"• **{index_name}** {emoji}: {direction} "
                f"(累计{cumulative:+.2f}%, {positive_days}涨{negative_days}跌)"
            )

        return {
            "type": "section",
            "title": "近7日趋势",
            "content": "\n".join(content_lines),
        }

    def _create_detailed_sections(self, indices_analysis: Dict) -> List[Dict]:
        """Create detailed analysis sections for each index."""
        sections = []

        for index_name, analysis in indices_analysis.items():
            sentiment = analysis.get("sentiment", "未知")
            confidence = analysis.get("confidence", 0)
            reasoning = analysis.get("reasoning", [])

            content_lines = [
                f"**情绪:** {sentiment} (置信度: {confidence * 100:.0f}%)",
                "",
                "**分析:**",
            ]

            for reason in reasoning:
                content_lines.append(f"• {reason}")

            sections.append({
                "type": "section",
                "title": f"{index_name} 详细分析",
                "content": "\n".join(content_lines),
            })

        return sections

    def _create_summary_text(self, analysis_result: Dict) -> str:
        """Create simple text summary."""
        overall_sentiment = analysis_result.get("overall_sentiment", "未知")
        overall_confidence = analysis_result.get("overall_confidence", 0)
        comparison = analysis_result.get("comparison", {})

        lines = [
            f"📊 市场行情分析",
            "",
            f"整体情绪: {overall_sentiment} (置信度: {overall_confidence * 100:.0f}%)",
        ]

        strongest = comparison.get("strongest", [])
        if strongest:
            lines.append("")
            lines.append("强势指数:")
            for idx in strongest[:2]:
                lines.append(f"• {idx['name']}: {idx['change_pct']:+.2f}%")

        return "\n".join(lines)

    async def _send_result(self, target_agent: str, data: Dict):
        """Send summary result to target agent."""
        event = Event(
            event_name="stock.summary.response",
            destination_id=target_agent,
            source_id=self.agent_id,
            payload={
                "type": "summary_response",
                "data": data,
                "source": self.agent_id,
            },
        )
        await self.client.send_event(event)
        print(f"Sent summary result to {target_agent}")


async def main():
    """Run the summary agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Summary Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument(
        "--url",
        default=None,
        help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)",
    )
    args = parser.parse_args()

    agent = SummaryAgent()

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
