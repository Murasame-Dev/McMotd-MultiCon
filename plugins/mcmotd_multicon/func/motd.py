"""
McMotd Minecraft 服务器状态查询模块
使用类重写并集成 Java 和 Bedrock
"""

from nonebot import get_plugin_config
from mcstatus import JavaServer, BedrockServer
from typing import Dict, Any

from ..config import Config

config = get_plugin_config(Config)


class Motd:
    def __init__(self, address: str, port: int = None):
        self.address = address
        self.port = port

    async def java_status(self, address: str, port: int = None) -> Dict[str, Any]:
        """
        查询 Java 版 Minecraft 服务器状态
        
        Args:
            address: 服务器地址,格式: host:port 或 host
        
        Returns:
            包含服务器状态信息的字典
        """

        address = self.address
        port = self.port
        
        # 查询服务器
        # 如果有端口,则传入 host:port
        if port is not None:
            server = JavaServer.lookup(f"{address}:{port}")
        # 如果没有端口,他可能是默认端口,或者是 SRV 记录,mcstatus 会自动处理请求
        else:
            server = JavaServer.lookup(f"{address}")
        
        status = await server.async_status()

        # 延迟
        if config.MCMOTD_EXPERIMENTAL_LATENCY_CHECK:
            from .networktools_cpp import entrypoint
            tcping_result = await entrypoint.tcping(address, port or 25565, timeout=3000)
            latency = tcping_result.get("avg_rtt") if tcping_result.get("status") == "success" else status.latency
        else:
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
    
    async def bedrock_status(self, address: str, port: int = None) -> Dict[str, Any]:
        """
        查询 Bedrock 版 Minecraft 服务器状态
        
        Args:
            address: 服务器地址,格式: host:port 或 host
        
        Returns:
            包含服务器状态信息的字典
        """

        address = self.address
        port = self.port
        
        # 查询服务器
        # 如果有端口,则传入 host:port
        if port is not None:
            server = BedrockServer.lookup(f"{address}:{port}")
        # 如果没有端口,他可能是默认端口,mcstatus 会自动处理请求
        else:
            server = BedrockServer.lookup(f"{address}")
        
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