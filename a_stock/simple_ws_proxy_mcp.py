#!/usr/bin/env python3
"""
WebSocket 代理 - 调用真实的 MCP Agents
通过 MCP 协议与 OpenAgents 通信，返回真实的 agent 分析结果
"""
import asyncio
import websockets
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MCP 配置
MCP_URL = "http://localhost:8700/mcp"
MAX_WAIT_TIME = 30  # 最多等待 30 秒


def send_mcp_message(text: str) -> bool:
    """通过 MCP 发送消息到 general 频道"""
    try:
        response = requests.post(MCP_URL, json={
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "tools/call",
            "params": {
                "name": "send_channel_message",
                "arguments": {
                    "channel": "general",
                    "text": text
                }
            }
        }, timeout=5)
        
        result = response.json()
        success = result.get("result", {}).get("content", [{}])[0].get("text") == "True"
        logger.info(f"MCP 消息发送{'成功' if success else '失败'}")
        return success
    except Exception as e:
        logger.error(f"MCP 发送失败: {e}")
        return False


def retrieve_mcp_messages(limit: int = 10) -> list:
    """从 MCP 获取频道消息"""
    try:
        response = requests.post(MCP_URL, json={
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "tools/call",
            "params": {
                "name": "retrieve_channel_messages",
                "arguments": {
                    "channel": "general",
                    "limit": limit
                }
            }
        }, timeout=5)
        
        result = response.json()
        content = result.get("result", {}).get("content", [{}])[0].get("text")
        
        if content and content != "None":
            try:
                messages = json.loads(content)
                return messages if isinstance(messages, list) else []
            except:
                pass
        return []
    except Exception as e:
        logger.error(f"MCP 获取消息失败: {e}")
        return []


async def call_agents_via_mcp(query: str) -> str:
    """
    通过 MCP 调用 agents 并等待响应
    
    Args:
        query: 用户查询
        
    Returns:
        agents 的响应文本，如果失败返回错误信息
    """
    logger.info(f"📤 收到查询: {query}")
    
    # 1. 记录当前时间戳
    start_time = time.time()
    
    # 2. 发送消息到 MCP
    if not send_mcp_message(query):
        return "❌ 消息发送失败，请稍后重试"
    
    logger.info("⏳ 等待 agents 处理...")
    
    # 3. 轮询读取响应文件（最多等待 MAX_WAIT_TIME 秒）
    attempt = 0
    response_dir = Path("responses")
    response_dir.mkdir(exist_ok=True)
    
    while time.time() - start_time < MAX_WAIT_TIME:
        attempt += 1
        await asyncio.sleep(2)  # 每 2 秒检查一次
        
        # 查找新的响应文件
        try:
            response_files = sorted(response_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            for response_file in response_files:
                # 只检查在查询后创建的文件
                if response_file.stat().st_mtime > start_time:
                    try:
                        with open(response_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            response_text = data.get("response", "")
                            if response_text:
                                logger.info(f"✅ 收到 planner 响应（第 {attempt} 次尝试，文件: {response_file.name}）")
                                # 读取后删除文件
                                response_file.unlink()
                                return response_text
                    except Exception as e:
                        logger.error(f"读取响应文件失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"扫描响应文件失败: {e}")
        
        logger.debug(f"第 {attempt} 次检查，暂无响应...")
    
    # 超时
    logger.warning(f"⏰ 等待超时（{MAX_WAIT_TIME} 秒）")
    return f"⏰ 处理超时，agents 可能正在忙碌中，请稍后重试"


async def generate_response_via_agents(query: str) -> str:
    """
    通过真实的 agents 生成响应
    
    Args:
        query: 用户查询
        
    Returns:
        格式化的响应文本
    """
    try:
        # 调用 MCP agents
        agent_response = await call_agents_via_mcp(query)
        
        # 如果响应是错误消息，直接返回
        if agent_response.startswith("❌") or agent_response.startswith("⏰"):
            return agent_response
        
        # 尝试解析 agent 响应（可能是结构化数据）
        try:
            data = json.loads(agent_response)
            # 如果有 summary_text，使用它
            if isinstance(data, dict) and "summary_text" in data:
                return data["summary_text"]
        except:
            pass
        
        # 返回原始响应
        return agent_response
        
    except Exception as e:
        logger.error(f"生成响应失败: {e}")
        return f"❌ 系统错误: {str(e)}"


async def handle_client(websocket):
    """处理 WebSocket 客户端连接"""
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"✅ 新客户端连接: {client_id}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "channel_message":
                    content = data.get("content", "")
                    logger.info(f"📨 收到消息: {content}")
                    
                    # 通过 agents 生成响应
                    response_text = await generate_response_via_agents(content)
                    
                    # 发送响应
                    response = {
                        "type": "agent_response",
                        "content": response_text,
                        "timestamp": int(time.time() * 1000)
                    }
                    
                    await websocket.send(json.dumps(response, ensure_ascii=False))
                    logger.info(f"✅ 响应已发送")
                else:
                    logger.warning(f"未知消息类型: {msg_type}")
                    
            except json.JSONDecodeError:
                logger.error("JSON 解析失败")
            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"❌ 客户端断开: {client_id}")
    except Exception as e:
        logger.error(f"连接错误: {e}")


async def main():
    """启动 WebSocket 服务器"""
    port = 8702
    logger.info(f"🚀 WebSocket 代理启动中...")
    logger.info(f"   端口: {port}")
    logger.info(f"   MCP URL: {MCP_URL}")
    logger.info(f"   模式: 真实 MCP Agents")
    logger.info("=" * 60)
    
    async with websockets.serve(handle_client, "0.0.0.0", port):
        logger.info(f"✅ WebSocket 服务器运行在 ws://0.0.0.0:{port}")
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 服务器已停止")

