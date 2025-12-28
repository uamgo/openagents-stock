#!/usr/bin/env python3
"""
Planner Agent - Orchestration for multi-index stock market sentiment analysis.

Features:
- Recognize user query for specific indices
- Coordinate worker agents
- Support natural language index queries

Worker Agents:
- query-agent: Queries multiple indices data with caching
- analyze-agent: Analyzes market sentiment across indices
- summary-agent: Generates comprehensive summaries

Usage:
    OPENAI_API_KEY=your-key python agents/planner_agent.py
"""

import asyncio
import os
import sys
import re
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.worker_agent import WorkerAgent
from openagents.models.event_context import EventContext
from openagents.models.event import Event
from openagents.models.agent_config import AgentConfig


# Index mapping for natural language
INDEX_KEYWORDS = {
    "上证": ["上证", "上海", "沪指", "000001"],
    "深证": ["深证", "深圳", "深指", "399001"],
    "科创板": ["科创", "科创板", "000688"],
    "创业板": ["创业", "创业板", "399006"],
    "北交所": ["北交", "北交所", "899050"],
}


class PlannerAgent(WorkerAgent):
    """Planner agent that orchestrates worker agents for multi-index analysis."""

    default_agent_id = "planner"

    def __init__(self, group=None, **kwargs):
        agent_config = AgentConfig(
            instruction=self._get_planner_instruction(),
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        super().__init__(agent_config=agent_config, **kwargs)
        
        # Store pending requests
        self._pending_requests = {}
        
        # Store step results
        self._step_results = {}

    def _get_planner_instruction(self) -> str:
        """Get the planner instruction prompt."""
        return """你是一个多指数市场情绪分析规划器（Planner）。

你的任务是：根据用户请求，协调三个 worker agents 完成多指数分析任务。

Available Agents:
1. query-agent - 查询多个指数的近7日日线数据
2. analyze-agent - 分析多指数市场情绪并对比
3. summary-agent - 生成综合报告

支持的指数：
- 上证指数 (沪指)
- 深证成指 (深指)
- 科创50 (科创板)
- 创业板指 (创业板)
- 北证50 (北交所)

你负责：
- 识别用户想查询的指数
- 协调worker agents完成分析
- 返回结构化的分析报告
"""

    async def on_startup(self):
        """Called when agent starts."""
        print("Planner Agent is running!")
        print("Waiting for worker agents: query-agent, analyze-agent, summary-agent")
        print(f"Supported indices: {', '.join(INDEX_KEYWORDS.keys())}")

    async def on_shutdown(self):
        """Called when agent shuts down."""
        print("Planner Agent stopped.")

    async def react(self, context: EventContext):
        """React to incoming messages."""
        event = context.incoming_event

        # Debug logging
        print(f"[DEBUG] Received event from: {event.source_id}")
        print(f"[DEBUG] Event type: {getattr(event, 'type', getattr(event, 'event_type', 'unknown'))}")
        print(f"[DEBUG] Payload keys: {list(event.payload.keys())}")
        print(f"[DEBUG] Payload: {event.payload}")

        # Skip our own messages
        if event.source_id == self.agent_id:
            print(f"[DEBUG] Skipping own message")
            return

        # Handle user requests (from chat)
        if event.payload.get("content") or event.payload.get("text"):
            print(f"[DEBUG] Handling user request")
            await self._handle_user_request(context)
        
        # Handle responses from worker agents
        elif event.payload.get("type") in ["query_response", "analyze_response", "summary_response"]:
            print(f"[DEBUG] Handling worker response")
            await self._handle_worker_response(context)
        else:
            print(f"[DEBUG] Unknown message type, ignoring")

    async def _handle_user_request(self, context: EventContext):
        """Handle user request from chat."""
        event = context.incoming_event
        content = event.payload.get("content") or event.payload.get("text") or ""
        
        # Handle dict content (extract text field)
        if isinstance(content, dict):
            content = content.get("text", "")
        
        # Ensure content is a string
        content = str(content) if content else ""
        
        if not content:
            return

        print(f"Received user request: {content}")

        # Parse user query
        query_info = self._parse_user_query(content)
        
        # Generate request ID
        request_id = f"req_{datetime.now().timestamp()}"
        
        # Store request context
        self._pending_requests[request_id] = {
            "channel": event.payload.get("channel") or "general",
            "user_id": event.source_id,
            "content": content,
            "query_info": query_info,
            "current_step": 1,
            "total_steps": 3,
        }
        
        # Store step results for this request
        self._step_results[request_id] = {}

        # Step 1: Send query request to query-agent
        await self._send_query_request(request_id, query_info)

    def _parse_user_query(self, content: str) -> Dict:
        """
        Parse user query to extract indices and other info.
        
        Args:
            content: User message content
            
        Returns:
            Query info dict
        """
        # Detect requested indices
        requested_indices = []
        
        for index_name, keywords in INDEX_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    requested_indices.append(index_name)
                    break
        
        # If no specific index mentioned, query all
        if not requested_indices:
            requested_indices = list(INDEX_KEYWORDS.keys())
        
        # Remove duplicates while preserving order
        requested_indices = list(dict.fromkeys(requested_indices))
        
        # Extract days (default 7)
        days = 7
        days_match = re.search(r'(\d+)天|近(\d+)日', content)
        if days_match:
            days = int(days_match.group(1) or days_match.group(2))
            days = min(days, 30)  # Cap at 30 days
        
        return {
            "indices": requested_indices,
            "days": days,
            "original_query": content,
        }

    async def _handle_worker_response(self, context: EventContext):
        """Handle response from worker agents."""
        event = context.incoming_event
        response_type = event.payload.get("type")
        data = event.payload.get("data")
        
        # Find the request this response belongs to
        if not self._pending_requests:
            return
        
        request_id = list(self._pending_requests.keys())[0]
        request_info = self._pending_requests[request_id]
        current_step = request_info["current_step"]

        print(f"Received {response_type} for step {current_step}")

        # Store result
        self._step_results[request_id][f"step{current_step}"] = data

        # Advance to next step
        if response_type == "query_response":
            # Step 2: Analyze
            request_info["current_step"] = 2
            await self._send_analyze_request(request_id, data)
        
        elif response_type == "analyze_response":
            # Step 3: Summarize
            request_info["current_step"] = 3
            await self._send_summary_request(request_id, data)
        
        elif response_type == "summary_response":
            # Final step: Send to user
            await self._send_to_user(request_id, data)
            
            # Clean up
            del self._pending_requests[request_id]
            del self._step_results[request_id]

    async def _send_query_request(self, request_id: str, query_info: Dict):
        """Send query request to query-agent."""
        indices = query_info["indices"]
        days = query_info["days"]
        
        print(f"[{request_id}] Step 1: Sending query request")
        print(f"  Indices: {', '.join(indices)}")
        print(f"  Days: {days}")
        
        event = Event(
            event_name="stock.query.request",
            destination_id="query-agent",
            source_id=self.agent_id,
            payload={
                "type": "query_request",
                "indices": indices,
                "days": days,
                "reply_to": self.agent_id,
                "request_id": request_id,
            },
        )
        await self.client.send_event(event)

    async def _send_analyze_request(self, request_id: str, indices_data: Dict):
        """Send analyze request to analyze-agent."""
        print(f"[{request_id}] Step 2: Sending analyze request")
        
        event = Event(
            event_name="stock.analyze.request",
            destination_id="analyze-agent",
            source_id=self.agent_id,
            payload={
                "type": "analyze_request",
                "indices_data": indices_data,
                "reply_to": self.agent_id,
                "request_id": request_id,
            },
        )
        await self.client.send_event(event)

    async def _send_summary_request(self, request_id: str, analysis_result: Dict):
        """Send summary request to summary-agent."""
        print(f"[{request_id}] Step 3: Sending summary request")
        
        event = Event(
            event_name="stock.summary.request",
            destination_id="summary-agent",
            source_id=self.agent_id,
            payload={
                "type": "summary_request",
                "analysis_result": analysis_result,
                "reply_to": self.agent_id,
                "request_id": request_id,
            },
        )
        await self.client.send_event(event)

    async def _send_to_user(self, request_id: str, summary: Dict):
        """Send final result to user."""
        print(f"[{request_id}] Sending final result to user")
        
        request_info = self._pending_requests[request_id]
        channel = request_info["channel"]
        query_info = request_info["query_info"]
        
        # Format summary as text
        response = self._format_summary(summary, query_info)
        
        # Send to channel
        messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
        if messaging:
            await messaging.send_channel_message(
                channel=channel,
                text=response
            )
            print(f"Sent final result to channel: {channel}")
        
        # 同时写入响应文件供 WebSocket 代理读取
        try:
            import json
            response_file = Path("responses") / f"{int(time.time() * 1000)}.json"
            response_file.parent.mkdir(exist_ok=True)
            with open(response_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.time(),
                    "channel": channel,
                    "response": response,
                    "request_id": request_id
                }, f, ensure_ascii=False, indent=2)
            print(f"Response saved to: {response_file}")
        except Exception as e:
            print(f"Failed to save response file: {e}")

    def _format_summary(self, summary: Dict, query_info: Dict) -> str:
        """Format summary blocks as readable text."""
        blocks = summary.get("blocks", [])
        summary_text = summary.get("summary_text", "")
        
        # Add query info header
        indices = query_info.get("indices", [])
        days = query_info.get("days", 7)
        
        lines = [
            f"📊 **{', '.join(indices)}** 近{days}日行情分析",
            "",
            summary_text,
            "",
        ]
        
        for block in blocks:
            block_type = block.get("type")
            
            if block_type == "header":
                lines.append(f"\n# {block.get('content')}")
                lines.append("")
            
            elif block_type == "section":
                title = block.get("title", "")
                content = block.get("content", "")
                lines.append(f"\n## {title}")
                lines.append(content)
                lines.append("")
            
            elif block_type == "table":
                title = block.get("title", "")
                headers = block.get("headers", [])
                rows = block.get("rows", [])
                
                lines.append(f"\n## {title}")
                
                # Format as markdown table
                header_line = "| " + " | ".join(headers) + " |"
                separator_line = "|" + "|".join(["---" for _ in headers]) + "|"
                lines.append(header_line)
                lines.append(separator_line)
                
                for row in rows:
                    row_line = "| " + " | ".join(str(cell) for cell in row) + " |"
                    lines.append(row_line)
                
                lines.append("")
            
            elif block_type == "list":
                title = block.get("title", "")
                items = block.get("items", [])
                
                lines.append(f"\n## {title}")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")
        
        return "\n".join(lines)


async def main():
    """Run the planner agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Planner Agent (Agent-based)")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument(
        "--url",
        default=None,
        help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)",
    )
    args = parser.parse_args()

    agent = PlannerAgent()

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
