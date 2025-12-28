from pydantic import BaseModel, Field
from typing import List


class Config(BaseModel):
    """MCMotd 多实例连接插件配置"""
    
    # 服务器模式配置
    MCMOTD_ENABLE_SERVER: bool = False  # 是否启用服务器模式
    MCMOTD_SERVER_IP: str = "127.0.0.1"  # 服务器监听地址
    MCMOTD_SERVER_Port: int = Field(default=60000, ge=1, le=65535)  # 服务器端口
    MCMOTD_SERVER_ALLOW_NAMES: List[str] = Field(default_factory=list)  # 允许连接的客户端名称列表
    MCMOTD_SERVER_STATUS_TIMEOUT: int = Field(default=10, ge=1, le=60)  # 状态查询超时时间(秒)
    
    # 客户端模式配置
    MCMOTD_ENABLE_CLIENT: bool = False  # 是否启用客户端模式
    MCMOTD_CONNECT_SERVERS: List[str] = Field(default_factory=list)  # 要连接的服务器地址列表
    MCMOTD_CLIENT_NAME: str = ""  # 客户端名称
    
    # 通用配置
    MCMOTD_SERVER_TOKEN: str = ""  # WebSocket 连接令牌
    MCMOTD_SPECIAL_INFO_SHOW: bool = False  # 是否显示不同节点的特殊信息
    MCMOTD_QUICKQUERY_DATA_PATH: str = "data/quickquery.json"  # 快速查询数据存储路径