"""
Java 版 Minecraft 服务器状态查询模块
此模块负责 McMotd 的 Java 服务器状态解析,使用 mcstatus 库查询 Java 服务器信息。
"""

from mcstatus import JavaServer
from typing import Dict, Any

async def query_java_server(address: str) -> Dict[str, Any]:
    """
    查询 Java 版 Minecraft 服务器状态
    
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
        server = JavaServer.lookup(f"{host}:{port}")
    # 如果没有端口,他可能是默认端口,或者是 SRV 记录,mcstatus 会自动处理请求
    else:
        server = JavaServer.lookup(f"{host}")
    
    status = await server.async_status()

    # 延迟
    latency = status.latency
    
    # 提取玩家列表
    players_list = []
    if status.players.sample:
        players_list = [player.name for player in status.players.sample]
    
    # 提取图标 - mcstatus 使用 icon 属性而非 favicon
    icon = status.icon if hasattr(status, 'icon') else None
    
    # 转换 MOTD
    motd = status.description
    if isinstance(motd, dict):
        motd = motd.get("text", str(motd))
    else:
        motd = str(motd)
    
    return {
        "motd": motd,
        "version": status.version.name,
        "players_online": status.players.online,
        "players_max": status.players.max,
        "players_list": players_list,
        "latency": latency,
        "icon": icon
    }