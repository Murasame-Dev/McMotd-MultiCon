"""
Bedrock 版 Minecraft 服务器状态查询模块
此模块负责 McMotd 的 Bedrock (PE) 服务器状态解析,使用 mcstatus 库查询 Bedrock 服务器信息。
"""

from mcstatus import BedrockServer
from typing import Dict, Any

async def query_bedrock_server(address: str) -> Dict[str, Any]:
    """
    查询 Bedrock 版 Minecraft 服务器状态
    
    Args:
        address: 服务器地址,格式: host:port 或 host
    
    Returns:
        包含服务器状态信息的字典
    """
    # 解析地址和端口
    port = None
    if ":" in address:
        host, port = address.rsplit(":", 1)
        port = int(port)
    else:
        host = address
    
    # 查询服务器
    # 如果有端口,则传入 host:port
    if port is not None:
        server = BedrockServer.lookup(f"{host}:{port}")
    # 如果没有端口,他可能是默认端口,mcstatus 会自动处理请求
    else:
        server = BedrockServer.lookup(f"{host}")
    
    status = await server.async_status()

    # 延迟
    latency = status.latency

    # 转换 MOTD
    motd = status.description
    if isinstance(motd, dict):
        motd = motd.get("text", str(motd))
    else:
        motd = str(motd)

    return {
        "motd": motd,
        "version": status.version.version,
        "players_online": status.players.online,
        "players_max": status.players.max,
        "map_name": status.map_name if hasattr(status, 'map_name') else "未知",
        "game_mode": status.gamemode if hasattr(status, 'gamemode') else "未知",
        "latency": latency
    }