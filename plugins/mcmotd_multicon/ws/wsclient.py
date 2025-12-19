"""
此模块为 McMotd 的额外 Websocket 客户端,负责处理与服务器的连接请求
MCMOTD_ENABLE_CLIENT: bool = False
MCMOTD_CONNECT_SERVERS: list[str] = []
MCMOTD_Server_Token: str | int = ""
"""

import asyncio
import websockets
import json
from nonebot.log import logger

from ..utils.motdjava import query_java_server
from ..utils.motdpe import query_bedrock_server

client_status = "未连接"
active_connections = []

async def handle_query_request(websocket, data):
    """处理服务器发来的查询请求"""
    request_id = data.get("request_id")
    query_type = data.get("query_type")
    address = data.get("address")
    
    logger.info(f"收到查询请求: {query_type} {address} (request_id: {request_id})")
    
    try:
        # 根据类型查询服务器
        if query_type == "java":
            result = await query_java_server(address)
        elif query_type == "bedrock":
            result = await query_bedrock_server(address)
        else:
            raise ValueError(f"未知的查询类型: {query_type}")
        
        # 清理不能序列化的字段
        if "raw" in result:
            del result["raw"]
        
        # 转换 MOTD 为字符串
        if "motd" in result:
            motd = result["motd"]
            if isinstance(motd, dict):
                result["motd"] = motd.get("text", str(motd))
            else:
                result["motd"] = str(motd)
        
        logger.info(f"查询完成,准备发送响应 (request_id: {request_id})")
        
        # 发送响应
        await websocket.send(json.dumps({
            "type": "query_response",
            "request_id": request_id,
            "data": result
        }))
        
        logger.info(f"响应已发送 (request_id: {request_id})")
        
    except Exception as e:
        logger.error(f"处理查询请求失败: {e}")
        await websocket.send(json.dumps({
            "type": "query_response",
            "request_id": request_id,
            "error": str(e)
        }))

async def connect_to_server(server_url: str, config):
    """连接到 WebSocket 服务器"""
    global client_status
    
    uri = f"ws://{server_url}/ws"
    logger.info(f"尝试连接到服务器: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            # 发送认证消息
            await websocket.send(json.dumps({
                "type": "auth",
                "token": config.MCMOTD_Server_Token,
                "name": config.MCMOTD_CLIENT_NAME
            }))
            
            # 等待认证响应
            auth_response = json.loads(await websocket.recv())
            if auth_response.get("type") != "auth_success":
                logger.error(f"认证失败: {auth_response}")
                return
            
            logger.info(f"已连接到服务器: {server_url}")
            client_status = f"已连接到 {server_url}"
            active_connections.append(websocket)
            
            # 启动心跳任务
            heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
            
            try:
                # 处理消息
                async for message in websocket:
                    data = json.loads(message)
                    logger.debug(f"收到消息: {data.get('type')}")
                    
                    if data.get("type") == "query":
                        await handle_query_request(websocket, data)
                    elif data.get("type") == "pong":
                        pass  # 心跳响应
                        
            finally:
                heartbeat_task.cancel()
                active_connections.remove(websocket)
                
    except Exception as e:
        logger.error(f"连接服务器失败 {server_url}: {e}")
        client_status = f"连接失败: {e}"

async def send_heartbeat(websocket):
    """发送心跳消息"""
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send(json.dumps({"type": "ping"}))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"发送心跳失败: {e}")

async def start_client(config):
    """启动 WebSocket 客户端"""
    global client_status
    
    while True:
        try:
            # 连接到所有服务器
            tasks = [
                connect_to_server(server, config)
                for server in config.MCMOTD_CONNECT_SERVERS
            ]
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"客户端错误: {e}")
            client_status = f"错误: {e}"
        
        # 重连延迟
        await asyncio.sleep(5)

def get_client_status() -> str:
    """获取客户端状态"""
    return client_status