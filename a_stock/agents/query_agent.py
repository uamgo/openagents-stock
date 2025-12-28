#!/usr/bin/env python3
"""
Query Agent - Worker agent for querying multiple index daily data with caching.

Features:
- Query multiple indices (上证, 深证, 科创板, 创业板, 北交所)
- Cache data to file with TTL (1 day)
- Background data refresh
- Support last 7 days data

Usage:
    python agents/query_agent.py
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from openagents.agents.worker_agent import WorkerAgent
from openagents.models.event_context import EventContext
from openagents.models.event import Event


# Index configurations
INDICES = {
    "上证": {"code": "sh000001", "name": "上证指数", "akshare_symbol": "000001"},
    "深证": {"code": "sz399001", "name": "深证成指", "akshare_symbol": "399001"},
    "科创板": {"code": "sh000688", "name": "科创50", "akshare_symbol": "000688"},
    "创业板": {"code": "sz399006", "name": "创业板指", "akshare_symbol": "399006"},
    "北交所": {"code": "bj899050", "name": "北证50", "akshare_symbol": "899050"},
}


class QueryAgent(WorkerAgent):
    """Agent that queries index daily data with caching."""

    default_agent_id = "query-agent"
    
    def __init__(self, agent_id=None):
        super().__init__(agent_id=agent_id or self.default_agent_id)
        
        # Data cache directory
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache TTL: 1 day
        self.cache_ttl = 24 * 60 * 60
        
        # Background update tasks
        self._update_tasks = {}

    async def on_startup(self):
        """Called when agent starts."""
        print("Query Agent is running! Ready to query index data.")
        print(f"Cache directory: {self.cache_dir}")
        print(f"Supported indices: {', '.join(INDICES.keys())}")

    async def on_shutdown(self):
        """Called when agent shuts down."""
        # Cancel all background tasks
        for task in self._update_tasks.values():
            task.cancel()
        print("Query Agent stopped.")

    async def react(self, context: EventContext):
        """
        React to query requests.
        
        Expected event payload:
        {
            "type": "query_request",
            "indices": ["上证", "深证"] or null (all),
            "days": 7,
            "reply_to": "planner"
        }
        """
        event = context.incoming_event

        # Skip our own messages
        if event.source_id == self.agent_id:
            return

        # Check if this is a query request
        if event.payload.get("type") != "query_request":
            return

        indices = event.payload.get("indices") or list(INDICES.keys())
        days = event.payload.get("days", 7)
        reply_to = event.payload.get("reply_to") or event.source_id

        print(f"Received query request for indices: {indices}, days: {days}")

        # Query the data
        indices_data = await self._query_indices(indices, days)

        # Send result back
        await self._send_result(reply_to, indices_data, context)

    async def _query_indices(self, indices: List[str], days: int) -> Dict:
        """
        Query multiple indices data with caching.
        
        Args:
            indices: List of index names
            days: Number of days to query
            
        Returns:
            Dict with all indices data
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "days": days,
            "indices": {}
        }
        
        for index_name in indices:
            if index_name not in INDICES:
                print(f"Unknown index: {index_name}")
                continue
            
            # Try to load from cache
            cached_data = await self._load_from_cache(index_name)
            
            if cached_data and not self._is_cache_expired(index_name):
                # Use cached data
                print(f"Using cached data for {index_name}")
                result["indices"][index_name] = cached_data
                
                # Check if need background update
                if self._need_background_update(index_name):
                    print(f"Scheduling background update for {index_name}")
                    self._schedule_background_update(index_name, days)
            else:
                # Fetch new data
                print(f"Fetching new data for {index_name}")
                new_data = await self._fetch_index_data(index_name, days)
                result["indices"][index_name] = new_data
                
                # Save to cache
                await self._save_to_cache(index_name, new_data)
        
        return result

    async def _fetch_index_data(self, index_name: str, days: int) -> Dict:
        """
        Fetch index data using akshare.
        
        Args:
            index_name: Index name (e.g., "上证")
            days: Number of days
            
        Returns:
            Index data dict
        """
        index_config = INDICES[index_name]
        
        try:
            # Import akshare
            import akshare as ak
            from datetime import timedelta
            
            print(f"Fetching {index_name} data from akshare")
            
            # Use index_zh_a_hist API (支持所有主要指数)
            symbol = index_config["akshare_symbol"]
            
            # Get recent N+5 days to ensure we have enough data
            start_date = (datetime.now() - timedelta(days=int(days)+10)).strftime("%Y%m%d")
            df = ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date)
            
            if df.empty:
                raise Exception(f"No data returned for {symbol}")
            
            # Get last N days
            df = df.tail(int(days))
            
            # Convert to records
            records = []
            for _, row in df.iterrows():
                record = {
                    "date": str(row["日期"]),
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": float(row["成交量"]),
                }
                
                # Calculate change
                if len(records) > 0:
                    prev_close = records[-1]["close"]
                    record["change"] = record["close"] - prev_close
                    record["change_pct"] = (record["change"] / prev_close) * 100
                else:
                    record["change"] = 0
                    record["change_pct"] = 0
                
                records.append(record)
            
            latest = records[-1] if records else {}
            latest_price = latest.get("close", 0)
            latest_change_pct = latest.get("change_pct", 0)
            
            print(f"  ✅ {index_name}: 最新价 {latest_price:.2f}, 涨跌幅 {latest_change_pct:+.2f}%")
            
            return {
                "code": index_config["code"],
                "name": index_config["name"],
                "data": records,
                "fetch_time": datetime.now().isoformat(),
            }
            
        except Exception as e:
            print(f"❌ Error fetching {index_name} data: {e}")
            import traceback
            traceback.print_exc()
            # Return mock data as fallback
            return self._generate_mock_data(index_name, days)

    def _generate_mock_data(self, index_name: str, days: int) -> Dict:
        """Generate mock data as fallback."""
        index_config = INDICES[index_name]
        
        # Base values
        base_close = 3000 if "上证" in index_name else 10000
        
        records = []
        days = int(days)  # 确保 days 是整数
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
            close = base_close + (i * 10) + ((-1) ** i * 5)
            
            record = {
                "date": date,
                "open": close - 5,
                "high": close + 8,
                "low": close - 8,
                "close": close,
                "volume": 250000000000,
            }
            
            if len(records) > 0:
                prev_close = records[-1]["close"]
                record["change"] = close - prev_close
                record["change_pct"] = (record["change"] / prev_close) * 100
            else:
                record["change"] = 0
                record["change_pct"] = 0
            
            records.append(record)
        
        return {
            "code": index_config["code"],
            "name": index_config["name"],
            "data": records,
            "fetch_time": datetime.now().isoformat(),
            "is_mock": True,
        }

    def _get_cache_file(self, index_name: str) -> Path:
        """Get cache file path for an index."""
        return self.cache_dir / f"{index_name}.json"

    async def _load_from_cache(self, index_name: str) -> Optional[Dict]:
        """Load data from cache file."""
        cache_file = self._get_cache_file(index_name)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache for {index_name}: {e}")
            return None

    async def _save_to_cache(self, index_name: str, data: Dict):
        """Save data to cache file."""
        cache_file = self._get_cache_file(index_name)
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved cache for {index_name}")
        except Exception as e:
            print(f"Error saving cache for {index_name}: {e}")

    def _is_cache_expired(self, index_name: str) -> bool:
        """Check if cache is expired (> 1 day)."""
        cache_file = self._get_cache_file(index_name)
        
        if not cache_file.exists():
            return True
        
        mtime = cache_file.stat().st_mtime
        age = datetime.now().timestamp() - mtime
        
        return age > self.cache_ttl

    def _need_background_update(self, index_name: str) -> bool:
        """Check if cache needs background update (older than 12 hours)."""
        cache_file = self._get_cache_file(index_name)
        
        if not cache_file.exists():
            return False
        
        mtime = cache_file.stat().st_mtime
        age = datetime.now().timestamp() - mtime
        
        # Update if older than 12 hours
        return age > (self.cache_ttl / 2)

    def _schedule_background_update(self, index_name: str, days: int):
        """Schedule background data update."""
        # Cancel existing task if any
        if index_name in self._update_tasks:
            self._update_tasks[index_name].cancel()
        
        # Create new task
        task = asyncio.create_task(self._background_update(index_name, days))
        self._update_tasks[index_name] = task

    async def _background_update(self, index_name: str, days: int):
        """Background update task."""
        try:
            print(f"Background update started for {index_name}")
            new_data = await self._fetch_index_data(index_name, days)
            await self._save_to_cache(index_name, new_data)
            print(f"Background update completed for {index_name}")
        except Exception as e:
            print(f"Background update failed for {index_name}: {e}")
        finally:
            # Remove from tasks
            if index_name in self._update_tasks:
                del self._update_tasks[index_name]

    async def _send_result(self, target_agent: str, data: Dict, context: EventContext):
        """Send query result to target agent."""
        event = Event(
            event_name="stock.query.response",
            destination_id=target_agent,
            source_id=self.agent_id,
            payload={
                "type": "query_response",
                "data": data,
                "source": self.agent_id,
            },
        )
        await self.client.send_event(event)
        print(f"Sent query result to {target_agent}")


async def main():
    """Run the query agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Query Agent")
    parser.add_argument("--host", default="localhost", help="Network host")
    parser.add_argument("--port", type=int, default=8700, help="Network port")
    parser.add_argument(
        "--url",
        default=None,
        help="Connection URL (e.g., grpc://localhost:8600 for direct gRPC)",
    )
    args = parser.parse_args()

    agent = QueryAgent()

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
