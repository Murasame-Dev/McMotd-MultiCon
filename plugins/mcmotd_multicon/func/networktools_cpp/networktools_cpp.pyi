"""C++ network utilities module for Python.

This module provides high-performance network diagnostic tools implemented in C++.
"""

from __future__ import annotations
from typing import TypedDict, Literal

__all__ = ["ping", "pingv6", "tracert", "tcping"]


class PingSuccessResult(TypedDict):
    """Successful ping result."""
    status: Literal["success"]
    avg_rtt: float
    loss_rate: float
    details: list[dict[str, str | int | float]]


class PingErrorResult(TypedDict):
    """Failed ping result."""
    status: Literal["error"]
    error: str


class TracertResult(TypedDict):
    """Traceroute result."""
    status: Literal["success", "error"]
    hops: list[dict[str, str | int | float]]
    error: str | None


class TcpingSuccessResult(TypedDict):
    """Successful TCP ping result."""
    status: Literal["success"]
    avg_rtt: float
    details: list[dict[str, str | int | float]]


class TcpingErrorResult(TypedDict):
    """Failed TCP ping result."""
    status: Literal["error"]
    error: str


def ping(
    dest: str, 
    count: int, 
    ttl: int, 
    timeout: int, 
    /
) -> PingSuccessResult | PingErrorResult:
    """
    执行 IPv4 ICMP ping
    
    参数:
        dest: 目标主机名或IP地址 (仅位置参数)
        count: ping 次数 (仅位置参数)
        ttl: 生存时间 (仅位置参数)
        timeout: 超时时间(毫秒) (仅位置参数)
    """
    ...


def pingv6(
    dest: str, 
    count: int, 
    ttl: int, 
    timeout: int, 
    /
) -> PingSuccessResult | PingErrorResult:
    """
    执行 IPv6 ICMP ping
    
    参数:
        dest: 目标主机名或IPv6地址 (仅位置参数)
        count: ping 次数 (仅位置参数)
        ttl: 生存时间 (仅位置参数)
        timeout: 超时时间(毫秒) (仅位置参数)
    """
    ...


def tracert(
    dest: str, 
    max_hops: int, 
    timeout: int, 
    /
) -> TracertResult:
    """
    执行路由追踪
    
    参数:
        dest: 目标主机名或IP地址 (仅位置参数)
        max_hops: 最大跳数 (仅位置参数)
        timeout: 超时时间(毫秒) (仅位置参数)
    """
    ...


def tcping(
    dest: str, 
    port: int, 
    timeout: int, 
    /
) -> TcpingSuccessResult | TcpingErrorResult:
    """
    执行 TCP 连接测试
    
    参数:
        dest: 目标主机名或IP地址 (仅位置参数)
        port: 目标端口 (仅位置参数)
        timeout: 超时时间(毫秒) (仅位置参数)
    """
    ...
