"""
记录解析模块
虽然说 mcstatus 可以解释 SRV 记录获取目标端口,但是 networktools_cpp 不行
所以要另外解析 SRV 记录
顺序：
解析 SRV 记录-解析目标域名和端口-解析目标域名 A/AAAA 记录-返回 IP 地址和端口
"""

import dns.resolver

class Nslookup:
    def __init__(self, address: str):
        self.address = address

    async def nslookup_srv(self) -> tuple[str, int]:
        """
        解析 SRV 记录
        
        参数:
            address: 服务器地址,格式: host:port 或 host
            default_port: 默认端口
        
        返回:
            包含目标主机名和端口的元组
        """
        address = self.address

        try:
            answers = dns.resolver.resolve(address, 'SRV')
            for rdata in answers:
                new_address = str(rdata.target).rstrip('.')
                port = rdata.port
                return new_address, port, True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers) as e:
            print("No SRV record found:", e)
        
        # 如果 SRV 解析失败，返回原地址
        return address, None, False

    async def nslookup_a_4a(self) -> list[str]:
        """
        解析 A 和 AAAA 记录
        
        参数:
            address: 服务器地址,格式: host
        
        返回:
            包含所有解析到的 IPv4 和 IPv6 地址的列表
        """
        address = self.address
        ip_addresses = []
        try:
            answers_a = dns.resolver.resolve(address, 'A')
            ip_addresses.append(str(answers_a[0]))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            ip_addresses.append(None)
        
        try:
            answers_aaaa = dns.resolver.resolve(address, 'AAAA')
            ip_addresses.append(str(answers_aaaa[0]))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            ip_addresses.append(None)
        
        return ip_addresses

