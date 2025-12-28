"""
Minecraft 服务器状态查询模块
集成 Java 和 Bedrock
完整代码在 func/motd.py 中
"""

from ..func.motd import Motd
from .nslookup import nslookup_srv

# Java 查询
async def query_java_server(address: str | int):
    try:
        # 走一遍 SRV 解析
        address, port, srv_flag = await nslookup_srv(address)
        motd = Motd(address)
        result = await motd.java_status(address, port)
        return result
    except Exception as e:
        # 返回错误信息而不是 None
        return {
            "motd": "查询失败",
            "version": "未知",
            "players_online": 0,
            "players_max": 0,
            "players_list": [],
            "latency": None,
            "icon": None,
            "error": str(e)
        }

# Bedrock 查询
async def query_bedrock_server(address: str | int):
    try:
        motd = Motd(address)
        result = await motd.bedrock_status(address)
        return result
    except Exception as e:
        # 返回错误信息而不是 None
        return {
            "motd": "查询失败",
            "version": "未知",
            "players_online": 0,
            "players_max": 0,
            "map_name": "未知",
            "game_mode": "未知",
            "latency": None,
            "error": str(e)
        }