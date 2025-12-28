"""
此模块为 McMotd 的 FastAPI 服务器,负责处理其他客户端的 Websocket 连接请求
由强劲的 FastAPI 框架提供支持
MCMOTD_ENABLE_SERVER: bool = False
MCMOTD_Server_Port: int
MCMOTD_Server_STATUS_TIMEOUT: int
MCMOTD_SERVER_TOKEN: str | int = ""
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import asyncio
import uvicorn
from nonebot.log import logger

app = FastAPI()

# 存储已连接的客户端
connected_clients: Dict[str, WebSocket] = {}
# 存储等待响应的请求
pending_requests: Dict[str, asyncio.Future] = {}

class WebSocketServer:
    def __init__(self, config):
        self.config = config
        self.server = None
    
    async def query_all_clients(self, query_type: str, address: str, timeout: int) -> List[Dict[str, Any]]:
        """向所有客户端发送查询请求并收集结果"""
        results = []
        
        logger.info(f"当前已连接客户端数量: {len(connected_clients)}")
        logger.info(f"客户端列表: {list(connected_clients.keys())}")
        
        if not connected_clients:
            logger.warning("没有客户端连接")
            return results
        
        for client_name, websocket in connected_clients.items():
            try:
                request_id = f"{client_name}_{asyncio.get_event_loop().time()}"
                future = asyncio.Future()
                pending_requests[request_id] = future
                
                # 发送查询请求
                logger.info(f"向客户端 {client_name} 发送查询请求: {query_type} {address}")
                await websocket.send_json({
                    "type": "query",
                    "request_id": request_id,
                    "query_type": query_type,
                    "address": address
                })
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(future, timeout=timeout)
                    logger.info(f"收到客户端 {client_name} 的响应")
                    results.append({
                        "name": client_name,
                        "success": True,
                        "data": response
                    })
                except asyncio.TimeoutError:
                    logger.warning(f"客户端 {client_name} 响应超时")
                    results.append({
                        "name": client_name,
                        "success": False,
                        "error": "超时"
                    })
                finally:
                    pending_requests.pop(request_id, None)
                    
            except Exception as e:
                logger.error(f"查询客户端 {client_name} 失败: {e}")
                results.append({
                    "name": client_name,
                    "success": False,
                    "error": str(e)
                })
        
        return results

server_instance: WebSocketServer = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await websocket.accept()
    client_name = None
    
    try:
        # 接收认证消息
        auth_data = await websocket.receive_json()
        
        if auth_data.get("type") != "auth":
            await websocket.close(code=1008, reason="需要认证")
            return
        
        # 验证令牌
        if auth_data.get("token") != server_instance.config.MCMOTD_SERVER_TOKEN:
            await websocket.close(code=1008, reason="令牌无效")
            return
        
        # 验证客户端名称
        client_name = auth_data.get("name")
        if client_name not in server_instance.config.MCMOTD_SERVER_ALLOW_NAMES:
            await websocket.close(code=1008, reason="客户端名称不在允许列表中")
            return
        
        # 检查是否已连接
        if client_name in connected_clients:
            await websocket.close(code=1008, reason="客户端已连接")
            return
        
        # 添加到已连接列表
        connected_clients[client_name] = websocket
        logger.info(f"客户端 {client_name} 已连接")
        
        # 发送认证成功消息
        await websocket.send_json({"type": "auth_success"})
        
        # 处理消息
        while True:
            data = await websocket.receive_json()
            
            # 处理查询响应
            if data.get("type") == "query_response":
                request_id = data.get("request_id")
                if request_id in pending_requests:
                    pending_requests[request_id].set_result(data.get("data"))
            
            # 处理心跳
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info(f"客户端 {client_name} 断开连接")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        if client_name and client_name in connected_clients:
            del connected_clients[client_name]

async def start_server(config):
    """启动 FastAPI 服务器"""
    global server_instance
    server_instance = WebSocketServer(config)
    logger.info(f"WebSocket 服务器实例已创建,允许的客户端: {config.MCMOTD_SERVER_ALLOW_NAMES}")
    
    server_config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=config.MCMOTD_SERVER_Port,
        log_level="info"
    )
    server = uvicorn.Server(server_config)
    await server.serve()

def get_connected_clients() -> List[str]:
    """获取已连接的客户端列表"""
    return list(connected_clients.keys())

def get_server_instance() -> WebSocketServer:
    """获取服务器实例"""
    return server_instance