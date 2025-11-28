import asyncio
import socket
import struct
import time
import os
from enum import IntEnum
from typing import Optional, ClassVar, Dict, List
from dataclasses import dataclass
from pydantic import BaseModel

class ICMPType(IntEnum):
    """ICMP 类型定义"""
    ECHO_REPLY = 0
    DESTINATION_UNREACHABLE = 3
    SOURCE_QUENCH = 4
    REDIRECT_MESSAGE = 5
    ECHO_REQUEST = 8
    ROUTER_ADVERTISEMENT = 9
    ROUTER_SOLICITATION = 10
    TIME_EXCEEDED = 11
    PARAMETER_PROBLEM = 12
    TIMESTAMP_REQUEST = 13
    TIMESTAMP_REPLY = 14

class ICMPCode(IntEnum):
    """ICMP 代码定义"""
    # 目的不可达 (Type=3)
    NETWORK_UNREACHABLE = 0
    HOST_UNREACHABLE = 1
    PROTOCOL_UNREACHABLE = 2
    PORT_UNREACHABLE = 3
    
    # 超时 (Type=11)
    TTL_EXCEEDED = 0
    FRAGMENT_REASSEMBLY_TIME_EXCEEDED = 1

@dataclass
class ICMPHeader:
    """ICMP 头部数据结构"""
    type: ICMPType
    code: int
    checksum: int
    identifier: int = 0
    sequence: int = 0

class ICMPPackage(BaseModel):
    """ICMP 数据包模型"""
    header: ICMPHeader
    data: bytes = b""
    
    # ICMP 类型和代码的映射关系
    VALID_TYPE_CODE_COMBINATIONS: ClassVar[Dict[ICMPType, List[int]]] = {
        ICMPType.ECHO_REPLY: [0],
        ICMPType.DESTINATION_UNREACHABLE: [0, 1, 2, 3],
        ICMPType.SOURCE_QUENCH: [0],
        ICMPType.REDIRECT_MESSAGE: [0, 1, 2, 3],
        ICMPType.ECHO_REQUEST: [0],
        ICMPType.TIME_EXCEEDED: [0, 1],
    }
    
    @classmethod
    def create_echo_request(cls, identifier: Optional[int] = None, sequence: int = 1, data: Optional[bytes] = None) -> 'ICMPPackage':
        """创建 ICMP 回显请求包"""
        if identifier is None:
            identifier = 12345
        
        if data is None:
            timestamp = struct.pack('!d', time.time())
            padding = b'x' * 32
            data = timestamp + padding
        
        header = ICMPHeader(
            type=ICMPType.ECHO_REQUEST,
            code=0,
            checksum=0,
            identifier=identifier,
            sequence=sequence
        )
        
        package = cls(header=header, data=data)
        package.header.checksum = package.calculate_checksum()
        return package
    
    def calculate_checksum(self) -> int:
        """计算 ICMP 校验和"""
        header_bytes = self._build_header_bytes(checksum=0)
        return self._compute_checksum(header_bytes + self.data)
    
    def _build_header_bytes(self, checksum: int|None = None) -> bytes:
        """构建头部字节"""
        if checksum is None:
            checksum = self.header.checksum
        
        return struct.pack('!BBHHH', 
                         self.header.type, 
                         self.header.code,
                         checksum,
                         self.header.identifier,
                         self.header.sequence)
    
    @staticmethod
    def _compute_checksum(data: bytes) -> int:
        """计算校验和"""
        if len(data) % 2:
            data += b'\x00'
        
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            checksum += word
        
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += checksum >> 16
        return ~checksum & 0xFFFF
    
    def to_bytes(self) -> bytes:
        """将包转换为字节序列"""
        header_bytes = self._build_header_bytes()
        return header_bytes + self.data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ICMPPackage':
        """从字节序列解析 ICMP 包"""
        if len(data) < 8:
            raise ValueError("ICMP packet too short")
        
        type_val, code, checksum, identifier, sequence = struct.unpack('!BBHHH', data[:8])
        
        icmp_type = ICMPType(type_val)
        header = ICMPHeader(
            type=icmp_type,
            code=code,
            checksum=checksum,
            identifier=identifier,
            sequence=sequence
        )
        
        package_data = data[8:]
        return cls(header=header, data=package_data)
    
    def validate(self) -> bool: # type: ignore
        """验证包的合法性"""
        valid_codes = self.VALID_TYPE_CODE_COMBINATIONS.get(self.header.type, [])
        if self.header.code not in valid_codes:
            return False
        
        return self.header.checksum == self.calculate_checksum()
    
    def __str__(self) -> str:
        return (f"ICMPPackage(type={self.header.type.name}, "
                f"code={self.header.code}, "
                f"checksum=0x{self.header.checksum:04x}, "
                f"data_length={len(self.data)})")

class AsyncICMPClient:
    """异步 ICMP 客户端"""
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.loop = asyncio.get_event_loop()
        self._sequence = 0
        self.identifier = os.getpid() & 0xFFFF

    async def __aenter__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.socket.setblocking(False)

        # self.socket.bind(('0.0.0.0', 0))

        # Windows 特殊设置：启用接收所有 IP 包
        # if os.name == 'nt':
        #     self.socket.ioctl(SIO_RCVALL.value, 1)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.socket:
            return True
        self.socket.close()
        return False
    
    async def send_echo_request(self, host: str, ttl: int = 64, timeout: Optional[float] = 5.0) -> tuple[str, bool, float, Optional[bytes]]:
        """发送 ICMP 回显请求"""
        if not self.socket:
            raise Exception()
        try:
            # 解析目标地址
            dest_addr = await self.loop.getaddrinfo(
                host, None, family=socket.AF_INET
            )
            dest_ip = dest_addr[0][4][0]

            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            
            # 创建 ICMP 包
            self._sequence += 1
            package = ICMPPackage.create_echo_request(sequence=self._sequence)
            packet_data = package.to_bytes()
            
            # 发送包
            start_time = self.loop.time()
            await self.loop.sock_sendto(self.socket, packet_data, (dest_ip, 0))
            
            # 等待响应
            try:
                data, addr = await asyncio.wait_for(
                    self.loop.sock_recvfrom(self.socket, 1024),
                    timeout=timeout
                )
                end_time = self.loop.time()
                response_time = (end_time - start_time) * 1000

                ip_header = data[:20]
                src_ip = socket.inet_ntoa(ip_header[12:16])
                
                return src_ip, True, response_time, data[20:]  # 跳过 IP 头
                
            except asyncio.TimeoutError:
                return '', False, 0.0, None
        except Exception as e:
            return '', False, 0.0, None
