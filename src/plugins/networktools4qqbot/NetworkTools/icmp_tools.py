import asyncio
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from icmp_package import AsyncICMPClient


class PingResult(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"
    ERROR = "error"

@dataclass
class TracertHop:
    hop_number: int
    ip_address: str
    hostname: Optional[str]
    response_times: list[Optional[float]]
    status: PingResult

class ICMPManager:
    """ICMP 管理器，封装 ping 和 tracert 功能"""
    
    def __init__(self, timeout: float = 5.0, max_hops: int = 30):
        self.timeout = timeout
        self.max_hops = max_hops
    
    async def ping(self, addr: str, count: int = 4, interval: float = 1.0) -> tuple[dict[str, Any], str]:
        """
        执行 ping 操作
        
        Args:
            addr: 目标地址
            count: ping 次数
            interval: 每次ping的间隔时间
            
        Returns:
            包含统计信息的字典
        """
        message = ""
        message += f"Pinging {addr} with {count} packets:\n"
        
        results = {
            'target': addr,
            'packets_sent': count,
            'packets_received': 0,
            'packet_loss': 0.0,
            'rtt_min': float('inf'),
            'rtt_max': 0.0,
            'rtt_avg': 0.0,
            'rtt_times': [],
            'message':message
        }
        
        total_rtt = 0.0
        
        for i in range(count):
            try:
                start_time = asyncio.get_event_loop().time()
                async with AsyncICMPClient() as cli:
                    readdr, success, response_time, response_data = await cli.send_echo_request(addr, ttl=64, timeout=self.timeout)
                end_time = asyncio.get_event_loop().time()
                
                if success:
                    rtt = (end_time - start_time) * 1000  # 转换为毫秒
                    results['packets_received'] += 1
                    total_rtt += rtt
                    results['rtt_times'].append(rtt)
                    
                    # 更新最小/最大 RTT
                    if rtt < results['rtt_min']:
                        results['rtt_min'] = rtt
                    if rtt > results['rtt_max']:
                        results['rtt_max'] = rtt
                    
                    message += f"Reply from {addr}: bytes={len(response_data) if response_data else 0} time={rtt:.2f}ms TTL=64\n"
                else:
                    message += "Request timed out.\n"
                
                # 不是最后一次ping则等待间隔
                if i < count - 1:
                    await asyncio.sleep(interval)
                    
            except Exception as e:
                message += f"Ping error: {e}\n"
        
        # 计算统计信息
        if results['packets_received'] > 0:
            results['rtt_avg'] = total_rtt / results['packets_received']
            results['packet_loss'] = (1 - results['packets_received'] / count) * 100
        
        # 打印统计摘要
        message += self._get_ping_statistics(results)
        return results, message
    
    async def tracert(self, addr: str, max_hops: Optional[int] = None) -> tuple[list[TracertHop], str]:
        """
        执行 traceroute 操作
        
        Args:
            addr: 目标地址
            max_hops: 最大跳数
            
        Returns:
            路径跳数列表
        """
        if max_hops is None:
            max_hops = self.max_hops

        message = ""
        message += f"Tracing route to {addr} over a maximum of {max_hops} hops:\n"
        
        hops: list[TracertHop] = []
        destination_reached = False
        
        for ttl in range(1, max_hops + 1):
            hop_result = await self._tracert_hop(addr, ttl)
            hops.append(hop_result)

            message += self._print_tracert_hop(hop_result)
            
            # 检查是否到达目标
            if (hop_result.status == PingResult.SUCCESS and 
                hop_result.ip_address == await self._resolve_hostname(addr)):
                destination_reached = True
                break
            
            # 如果连续超时，可能已经无法继续追踪
            if (len(hops) > 3 and 
                all(h.status == PingResult.TIMEOUT for h in hops[-3:])):
                message += "Trace terminated: multiple consecutive timeouts\n"
                break
        
        if not destination_reached:
            message += "Trace incomplete: maximum hops reached\n"

        return hops, message
    
    async def _tracert_hop(self, addr: str, ttl: int) -> TracertHop:
        """
        执行 traceroute 的单跳，进行3次探测
        
        Args:
            addr: 目标地址
            ttl: 当前 TTL 值
            
        Returns:
            跳数结果
        """
        response_times = []
        ip_address = None
        hostname = None
        final_status = PingResult.TIMEOUT

        async def run(addr: str, ttl: int, timeout: float):
            async with AsyncICMPClient() as cli:
                reip, success, response_time, response_data = await cli.send_echo_request(addr, ttl, timeout)
            return reip, success, response_time, response_data
        
        tasks = []
        for _ in range(3):
            tasks.append(asyncio.create_task(run(addr, ttl, self.timeout)))
        
        # 进行3次探测
        for task in tasks:
            reip, success, response_time, response_data = await task
            try:
                if success:
                    response_times.append(response_time)
                    final_status = PingResult.SUCCESS
                    
                    # 只在第一次成功时获取IP和主机名
                    if ip_address is None:
                        dest_ip = reip
                        if dest_ip:
                            ip_address = dest_ip
                            hostname = await self._reverse_dns_lookup(dest_ip)
                        else:
                            response_times.append(None)
                else:
                    response_times.append(None)
                    
            except Exception as e:
                response_times.append(None)
                final_status = PingResult.ERROR
        
        # 如果3次都超时，IP地址显示为 "*"
        if all(rt is None for rt in response_times):
            ip_address = "*"
        
        return TracertHop(
            hop_number=ttl,
            ip_address=ip_address or "*",
            hostname=hostname,
            response_times=response_times,
            status=final_status
        )
    
    async def _resolve_hostname(self, hostname: str) -> Optional[str]:
        """解析主机名到 IP 地址"""
        try:
            loop = asyncio.get_event_loop()
            addrinfo = await loop.getaddrinfo(
                hostname, None, family=socket.AF_INET
            )
            return addrinfo[0][4][0]
        except Exception:
            return None
    
    async def _reverse_dns_lookup(self, ip: str) -> Optional[str]:
        """反向 DNS 查询"""
        try:
            loop = asyncio.get_event_loop()
            hostname = await loop.getnameinfo((ip, 0), 0)
            return hostname[0] if hostname[0] != ip else None
        except Exception:
            return None
    
    def _get_ping_statistics(self, results: dict[str, Any]):
        """打印 ping 统计信息"""
        message = "\n"
        message += f"Ping statistics for {results['target']}:\n"
        message += (f"    Packets: Sent = {results['packets_sent']}, "
                    f"Received = {results['packets_received']}, "
                    f"Lost = {results['packets_sent'] - results['packets_received']} "
                    f"({results['packet_loss']:.1f}% loss)\n")
        
        if results['packets_received'] > 0:
            message += "Approximate round trip times in milli-seconds:\n"
            message += (f"    Minimum = {results['rtt_min']:.2f}ms, "
                        f"Maximum = {results['rtt_max']:.2f}ms, "
                        f"Average = {results['rtt_avg']:.2f}ms\n")
        message += "\n"
        return message
    
    def _print_tracert_hop(self, hop: TracertHop):
        """打印 traceroute 单跳结果"""
        message = ""
        if hop.status == PingResult.SUCCESS:
            hostname_display = f" [{hop.hostname}]" if hop.hostname else ""
            message += f"{hop.hop_number:2d} "
            for r in hop.response_times:
                if r:
                    message += f"{r:4.2f} ms "
                else:
                    message += f"{"*":8s} "
            message += f"{hop.ip_address}{hostname_display}\n"

        elif hop.status == PingResult.TIMEOUT:
            message += f"{hop.hop_number:2d} {"*":8s} {"*":8s} {"*":8s} Request timed out.\n"
        else:
            message += f"{hop.hop_number:2d} {"*":8s} {"*":8s} {"*":8s} Error occurred.\n"

        return message


# 高级功能：批量 ping 和网络诊断
class NetworkDiagnostics:
    """网络诊断工具"""
    
    def __init__(self):
        self.icmp_manager = ICMPManager()
    
    async def batch_ping(self, addresses: list[str], count: int = 2) -> dict[str, dict[str, Any]]:
        """批量 ping 多个地址"""
        message = f"Batch pinging {len(addresses)} addresses...\n"
        results = {}
        
        tasks = [self.icmp_manager.ping(addr, count) for addr in addresses]
        ping_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for addr, result in zip(addresses, ping_results):
            if isinstance(result, Exception):
                results[addr] = {'error': str(result)}
            else:
                results[addr] = result
        
        return results
    
    async def network_latency_map(self, addresses: list[str]) -> list[tuple[str, float]]:
        """网络延迟地图"""
        results = await self.batch_ping(addresses, count=3)
        
        latency_map = []
        for addr, result in results.items():
            if 'rtt_avg' in result and result['rtt_avg'] > 0:
                latency_map.append((addr, result['rtt_avg']))
        
        # 按延迟排序
        return sorted(latency_map, key=lambda x: x[1])
    
    async def connectivity_test(self, test_addresses: list[str]|None = None) -> dict[str, bool]:
        """连通性测试"""
        if test_addresses is None:
            test_addresses = [
                "8.8.8.8",        # Google DNS
                "1.1.1.1",        # Cloudflare DNS
                "208.67.222.222", # OpenDNS
            ]
        
        results = await self.batch_ping(test_addresses, count=1)

        connectivity = {}
        for addr, result in results.items():
            connectivity[addr] = result.get('packets_received', 0) > 0

        return connectivity
