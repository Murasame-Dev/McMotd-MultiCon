"""
Motd 快速查询模块
用于在对应群内快速查询 Motd 信息
格式为：
群号:{
    "default": "地址",
    "别名1": "地址",
    "别名2": "地址"
    }
以 json 文件形式存储在 根目录/data/quickquery.json 中
指令为/addmotd 别名 地址
如果为/addmotd 地址 为 default
此时可直接通过/motd 直接查询 default 服务器状态
或者 /motd 别名 查询对应服务器状态
列出别名为: /motdlist
/delmotd 别名 删除对应别名
/delmotd default 删除默认服务器
指令在__main__.py中
数据存储目录定义在 config.py 中:MCMOTD_QUICKQUERY_DATA_PATH
"""

from nonebot import get_plugin_config

from ..config import Config

config = get_plugin_config(Config)

import json
from pathlib import Path
from typing import Dict, Optional


class QuickQueryManager:
    """快速查询管理器"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        初始化快速查询管理器
        
        Args:
            data_path: JSON 数据文件路径，如果为 None 则使用配置中的路径
        """
        if data_path is None:
            data_path = config.MCMOTD_QUICKQUERY_DATA_PATH
        self.data_path = Path(data_path)
        self.data: Dict[str, Dict[str, str]] = {}
        self._ensure_data_file()
        self._load_data()
    
    def _ensure_data_file(self):
        """确保数据文件和目录存在"""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_path.exists():
            self.data_path.write_text("{}", encoding="utf-8")
    
    def _load_data(self):
        """从文件加载数据"""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"保存数据失败: {e}")
    
    def add_server(self, group_id: str, alias: str, address: str) -> str:
        """
        添加服务器地址
        
        Args:
            group_id: 群号
            alias: 别名(如果是 "default" 则为默认服务器)
            address: 服务器地址
            
        Returns:
            操作结果消息
        """
        group_id = str(group_id)
        
        if group_id not in self.data:
            self.data[group_id] = {}
        
        self.data[group_id][alias] = address
        self._save_data()
        
        if alias == "default":
            return f"已设置默认服务器: {address}"
        else:
            return f"已添加别名 '{alias}': {address}"
    
    def get_server(self, group_id: str, alias: str = "default") -> Optional[str]:
        """
        获取服务器地址
        
        Args:
            group_id: 群号
            alias: 别名,默认为 "default"
            
        Returns:
            服务器地址,如果不存在则返回 None
        """
        group_id = str(group_id)
        
        if group_id not in self.data:
            return None
        
        return self.data[group_id].get(alias)
    
    def list_servers(self, group_id: str) -> Dict[str, str]:
        """
        列出群组的所有服务器
        
        Args:
            group_id: 群号
            
        Returns:
            别名到地址的字典
        """
        group_id = str(group_id)
        return self.data.get(group_id, {})
    
    def delete_server(self, group_id: str, alias: str) -> str:
        """
        删除服务器别名
        
        Args:
            group_id: 群号
            alias: 别名
            
        Returns:
            操作结果消息
        """
        group_id = str(group_id)
        
        if group_id not in self.data:
            return "本群还没有添加任何服务器"
        
        if alias not in self.data[group_id]:
            return f"别名 '{alias}' 不存在"
        
        address = self.data[group_id][alias]
        del self.data[group_id][alias]
        
        # 如果群组没有服务器了,删除整个群组记录
        if not self.data[group_id]:
            del self.data[group_id]
        
        self._save_data()
        
        if alias == "default":
            return f"已删除默认服务器: {address}"
        else:
            return f"已删除别名 '{alias}': {address}"


# 全局实例
_quick_query_manager: Optional[QuickQueryManager] = None


def get_quick_query_manager() -> QuickQueryManager:
    """获取快速查询管理器实例"""
    global _quick_query_manager
    if _quick_query_manager is None:
        _quick_query_manager = QuickQueryManager()
    return _quick_query_manager