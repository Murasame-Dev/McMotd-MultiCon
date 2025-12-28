"""
文本格式化模块

此模块负责将 Minecraft 服务器查询结果格式化为易读的文本消息,
用于在 QQ 机器人中显示。

请注意:多行文本格式请用
f"123"
f"\n"
f"456"
f"\n"
f"789"
来表示

Java状态格式:
f"{mcstatus_icon}" or 默认图标 - 服务器图标
f"\n"
f"========================\n"
f"\n"
f"{motd}" - 服务器 MOTD 描述,支持多行
f"\n"
f"版本:{version}" - 服务器版本
f"\n"
f"在线人数:{players_online}/{players_max}" - 在线玩家数/最大玩家数
f"\n"
f"玩家列表:{player_list}" - 在线玩家列表 (逗号分隔)
f"\n"
f"========================\n"
f"延迟:"
f"{MCMOTD_CLIENT_NAME}: {latency} ms" - 本服延迟
f"\n"
f"{server_name}: {server_latency} ms" - 其他节点延迟,有多个节点则顺位多行显示
f"\n"

Bedrock状态格式:
默认图标 - 服务器图标
f"\n"
f"========================\n"
f"\n"
f"{motd}" - 服务器 MOTD 描述,支持多行
f"\n"
f"版本:{version}" - 服务器版本
f"\n"
f"在线人数:{players_online}/{players_max}" - 在线玩家数/最大玩家数
f"\n"
f"地图名称:{map_name}" - 服务器地图名称
f"\n"
f"游戏模式:{game_mode}" - 服务器游戏模式
f"\n"
f"========================\n"
f"延迟:"
f"{MCMOTD_CLIENT_NAME}: {latency} ms" - 本服延迟
f"\n"
f"{server_name}: {server_latency} ms" - 其他节点延迟,有多个节点则顺位多行显示
f"\n"
"""

import base64
from typing import Dict, Any, List
from pathlib import Path
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .colorcodes import remove_color_codes
from .specialinfo import get_special_info

def get_default_icon() -> str:
    """获取默认图标的 base64 编码"""
    try:
        icon_path = Path(__file__).parent.parent / "res" / "default.png"
        if icon_path.exists():
            with open(icon_path, "rb") as f:
                icon_data = base64.b64encode(f.read()).decode()
                return icon_data
    except Exception:
        pass
    return ""

def format_java_status(local_result: Dict[str, Any], remote_results: List[Dict[str, Any]], local_name: str, address: str = "") -> Message:
    """格式化 Java 服务器状态为消息文本"""
    msg = Message()
    
    # 服务器图标处理
    icon = local_result.get("icon")
    if icon:
        icon_data = icon.replace('data:image/png;base64,', '')
        msg += MessageSegment.image(f"base64://{icon_data}")
    else:
        default_icon = get_default_icon()
        if default_icon:
            msg += MessageSegment.image(f"base64://{default_icon}")
    
    lines = []
    
    # MOTD - 清除颜色代码
    motd = local_result.get("motd", "无描述")
    clean_motd = remove_color_codes(str(motd))
    lines.append(clean_motd)
    lines.append("========================")
    
    # 服务器信息
    lines.append(f"地址: {address}")
    lines.append(f"版本: {local_result['version']}")
    lines.append(f"在线人数: {local_result['players_online']}/{local_result['players_max']}")
    # 玩家列表
    if local_result.get("players_list"):
        players = ", ".join(local_result["players_list"])
        lines.append(f"玩家列表: {players}")
    lines.append("========================")
    lines.append("延迟:")
    latency = local_result.get('latency')
    latency_str = f"{latency:.2f} ms" if latency is not None else "超时"
    lines.append(f"{local_name}: {latency_str}")
    # 远程节点延迟
    for remote in remote_results:
        if remote.get("success"):
            remote_latency = remote['data'].get('latency')
            remote_latency_str = f"{remote_latency:.2f} ms" if remote_latency is not None else "超时"
            lines.append(f"{remote['name']}: {remote_latency_str}")
        else:
            lines.append(f"{remote['name']}: 查询失败")
    
    msg += MessageSegment.text("\n".join(lines))
    return msg

def format_java_status_with_config(local_result: Dict[str, Any], remote_results: List[Dict[str, Any]], local_name: str, address: str, show_special: bool) -> Message:
    msg = format_java_status(local_result, remote_results, local_name, address)
    special_info = get_special_info(local_result, remote_results, show_special)
    if special_info:
        msg += MessageSegment.text("\n" + special_info)
    return msg

def format_bedrock_status(local_result: Dict[str, Any], remote_results: List[Dict[str, Any]], local_name: str, address: str = "") -> Message:
    """格式化 Bedrock 服务器状态为消息文本"""
    msg = Message()
    
    # 默认图标处理
    default_icon = get_default_icon()
    if default_icon:
        msg += MessageSegment.image(f"base64://{default_icon}")
    
    lines = []
    # MOTD - 清除颜色代码
    motd = str(local_result.get("motd", "无描述"))
    clean_motd = remove_color_codes(motd)
    lines.append(clean_motd)
    lines.append("========================")
    # 服务器信息
    lines.append(f"地址: {address}")
    lines.append(f"版本: {local_result['version']}")
    lines.append(f"在线人数: {local_result['players_online']}/{local_result['players_max']}")
    lines.append(f"地图名称: {local_result['map_name']}")
    lines.append(f"游戏模式: {local_result['game_mode']}")
    lines.append("========================")
    lines.append("延迟:")
    latency = local_result.get('latency')
    latency_str = f"{latency:.2f} ms" if latency is not None else "超时"
    lines.append(f"{local_name}: {latency_str}")
    # 远程节点延迟
    for remote in remote_results:
        if remote.get("success"):
            remote_latency = remote['data'].get('latency')
            remote_latency_str = f"{remote_latency:.2f} ms" if remote_latency is not None else "超时"
            lines.append(f"{remote['name']}: {remote_latency_str}")
        else:
            lines.append(f"{remote['name']}: 查询失败")
    
    msg += MessageSegment.text("\n".join(lines))
    return msg

def format_bedrock_status_with_config(local_result: Dict[str, Any], remote_results: List[Dict[str, Any]], local_name: str, address: str, show_special: bool) -> Message:
    msg = format_bedrock_status(local_result, remote_results, local_name, address)
    special_info = get_special_info(local_result, remote_results, show_special)
    if special_info:
        msg += MessageSegment.text("\n" + special_info)
    return msg