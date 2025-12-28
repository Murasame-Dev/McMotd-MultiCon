"""
McMotd 额外信息显示模块
此模块负责在多实例连接时,当不同实例返回的 MOTD 或图标不同时,添加额外的信息提示用户
算是一个有意思的小功能

格式:
f"有意思的是,其他节点传入的其他与主节点有些许特殊:"
f"\n"
f"{server_name}: {server_info}" - 其他节点名称: 该节点的 MOTD 描述或图标显示,若有其一与主干节点相同,则不显示
"""

from typing import Dict, Any, List
from collections import defaultdict
from .colorcodes import remove_color_codes

def get_special_info(local_result: Dict[str, Any], remote_results: List[Dict[str, Any]], show_special: bool) -> str:
    # 检查是否启用特殊信息显示
    if not show_special or not remote_results:
        return ""
    
    # 获取本地节点信息并清理颜色代码
    local_motd = remove_color_codes(local_result.get("motd", ""))
    local_icon = local_result.get("icon")
    
    # 用于聚合相同信息的节点
    motd_groups = defaultdict(list)
    icon_groups = defaultdict(list)
    
    # 遍历所有远程节点结果
    for remote in remote_results:
        if not remote.get("success"):
            continue
        
        data = remote.get("data", {})
        name = remote.get("name", "未知")
        remote_motd = remove_color_codes(data.get("motd", ""))
        remote_icon = data.get("icon")
        
        # 过滤掉查询失败的情况
        if remote_motd in ["查询失败", ""]:
            continue
        
        # 比较 MOTD，不同则记录
        if remote_motd != local_motd:
            motd_groups[remote_motd].append(name)
        
        # 比较图标，不同则记录（过滤掉"无图标"的情况）
        if remote_icon != local_icon and remote_icon is not None:
            icon_key = "有图标" if remote_icon else "无图标"
            icon_groups[icon_key].append(name)
    
    # 如果没有差异则不显示
    if not motd_groups and not icon_groups:
        return ""
    
    # 构建输出信息
    lines = ["========================"]
    lines.append("有意思的是,其他节点传入的信息与主节点有些许特殊:")
    
    # 添加 MOTD 差异信息
    for motd, names in motd_groups.items():
        nodes = ", ".join(names)
        lines.append(f"{nodes}:\n {motd}")
    
    # 添加图标差异信息
    for icon_status, names in icon_groups.items():
        nodes = ", ".join(names)
        lines.append(f"{nodes}:\n {icon_status}")
    
    return "\n".join(lines)