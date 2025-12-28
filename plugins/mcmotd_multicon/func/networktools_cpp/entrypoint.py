"""
networktools_cpp 封装模块
提供对 C++ 网络工具的 Python 接口
"""

import sys
from pathlib import Path
from typing import TypedDict, Literal

# 添加 C++ 模块路径（就在当前目录）
cpp_module_path = Path(__file__).parent
sys.path.insert(0, str(cpp_module_path))

import networktools_cpp


class PingResult(TypedDict):
    """Ping 结果"""
    status: Literal["success", "error"]
    avg_rtt: float | None
    loss_rate: float | None
    details: list[dict] | None
    error: str | None


class TracertResult(TypedDict):
    """路由追踪结果"""
    status: Literal["success", "error"]
    hops: list[dict] | None
    error: str | None


class TcpingResult(TypedDict):
    """TCP Ping 结果"""
    status: Literal["success", "error"]
    avg_rtt: float | None
    details: list[dict] | None
    error: str | None


async def ping(dest: str, count: int = 4, ttl: int = 64, timeout: int = 1000) -> PingResult:
    """
    执行 IPv4 ICMP ping
    
    参数:
        dest: 目标主机名或IP地址
        count: ping 次数，默认 4
        ttl: 生存时间，默认 64
        timeout: 超时时间(毫秒)，默认 1000
    
    返回:
        PingResult 字典
    """
    try:
        result = networktools_cpp.ping(dest, count, ttl, timeout)
        return result
    except Exception as e:
        return {
            "status": "error",
            "avg_rtt": None,
            "loss_rate": None,
            "details": None,
            "error": str(e)
        }


async def pingv6(dest: str, count: int = 4, ttl: int = 64, timeout: int = 1000) -> PingResult:
    """
    执行 IPv6 ICMP ping
    
    参数:
        dest: 目标主机名或IPv6地址
        count: ping 次数，默认 4
        ttl: 生存时间，默认 64
        timeout: 超时时间(毫秒)，默认 1000
    
    返回:
        PingResult 字典
    """
    try:
        result = networktools_cpp.pingv6(dest, count, ttl, timeout)
        return result
    except Exception as e:
        return {
            "status": "error",
            "avg_rtt": None,
            "loss_rate": None,
            "details": None,
            "error": str(e)
        }


async def tracert(dest: str, max_hops: int = 30, timeout: int = 1000) -> TracertResult:
    """
    执行路由追踪
    
    参数:
        dest: 目标主机名或IP地址
        max_hops: 最大跳数，默认 30
        timeout: 超时时间(毫秒)，默认 1000
    
    返回:
        TracertResult 字典
    """
    try:
        result = networktools_cpp.tracert(dest, max_hops, timeout)
        return result
    except Exception as e:
        return {
            "status": "error",
            "hops": None,
            "error": str(e)
        }


async def tcping(dest: str, port: int, timeout: int = 1000) -> TcpingResult:
    """
    执行 TCP 连接测试
    
    参数:
        dest: 目标主机名或IP地址
        port: 目标端口
        timeout: 超时时间(毫秒)，默认 1000
    
    返回:
        TcpingResult 字典
    """
    try:
        result = networktools_cpp.tcping(dest, port, timeout)
        return result
    except Exception as e:
        return {
            "status": "error",
            "avg_rtt": None,
            "details": None,
            "error": str(e)
        }

