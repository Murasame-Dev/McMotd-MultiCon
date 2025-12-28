"""
McMotd_MultiCon 插件
基于 McStatus 库实现多服务器状态聚合显示

插件功能介绍:
-----------
McMotd_MultiCon 是一个 Nonebot2 插件,在正常提供服务器状态解析功能的基础上,增加了多实例连接的功能。
它允许多个 McMotd 插件实例通过 Websocket 连接到主干服务器额外开放的 FastAPI 服务器,然后由主干服务器下发状态请求
客户端实例收到请求后便请求服务器状态并将结果返回给主干服务器
主干服务器整合消息后将结果发送给用户

基于 mcstatus 库和 Nonebot2 框架,支持 OneBot-V11 协议。

命令列表:
--------
/motd <地址> - 查询指定地址的 Java 服务器状态并输出
/motd <别名> - 查询已保存的别名服务器状态
/motd - 查询默认服务器状态(需先设置)
/motdpe <地址> - 查询指定地址的 Bedrock(PE) 服务器状态并输出
/addmotd <地址> - 添加默认服务器
/addmotd <别名> <地址> - 添加别名服务器
/motdlist - 列出本群所有已保存的服务器
/delmotd <别名> - 删除指定别名的服务器
/delmotd default - 删除默认服务器
/mcmotd client list - 查询所有已连接此 McMotd 实例的客户端列表
/mcmotd server status - 查询服务器状态信息
"""

from nonebot import on_command, get_driver, get_plugin_config
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot.exception import FinishedException
# 用户权限
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

import asyncio

from .config import Config
from .utils.motdjava import query_java_server
from .utils.motdpe import query_bedrock_server
from .utils.format import format_java_status_with_config, format_bedrock_status_with_config
from .utils.quickquery import get_quick_query_manager
from .ws.fastapi_wserver import start_server, get_connected_clients
from .ws.wsclient import start_client, get_client_status

config = get_plugin_config(Config)

# 命令处理器
motd = on_command("motd", priority=5, block=True)
motdpe = on_command("motdpe", priority=5, block=True)
mcmotd = on_command("mcmotd", priority=5, block=True)
addmotd = on_command("addmotd", priority=5, block=True, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
delmotd = on_command("delmotd", priority=5, block=True, permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
motdlist = on_command("motdlist", priority=5, block=True)

@motd.handle()
async def handle_motd(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """处理 Java 版服务器状态查询命令"""
    address = args.extract_plain_text().strip()
    
    # 快速查询功能
    qm = get_quick_query_manager()
    group_id = str(event.group_id) if hasattr(event, 'group_id') else str(event.user_id)
    
    if not address:
        # 如果没有参数,尝试查询默认服务器
        default_address = qm.get_server(group_id, "default")
        if default_address:
            address = default_address
        else:
            await motd.finish("请输入服务器地址,例如: /motd mc.hypixel.net\n或使用 /addmotd 添加默认服务器")
    else:
        # 如果有参数,先尝试作为别名查询
        alias_address = qm.get_server(group_id, address)
        if alias_address:
            address = alias_address
    
    # 发送查询提示并获取消息ID
    searching_msg = await motd.send("正在查询服务器状态...")
    searching_msg_id = searching_msg["message_id"]
    
    try:
        # 查询本地服务器
        local_result = await query_java_server(address)
        
        # 如果是服务器模式,查询所有客户端
        remote_results = []
        if config.MCMOTD_ENABLE_SERVER:
            from .ws.fastapi_wserver import get_server_instance
            srv = get_server_instance()
            if srv:
                logger.info(f"开始向客户端下发查询请求: {address}")
                remote_results = await srv.query_all_clients(
                    "java", address, config.MCMOTD_SERVER_STATUS_TIMEOUT
                )
                logger.info(f"收到 {len(remote_results)} 个客户端响应")
            else:
                logger.warning("服务器实例未初始化")
        
        # 撤回查询提示消息
        await bot.delete_msg(message_id=searching_msg_id)
        
        # 格式化并发送结果
        message = format_java_status_with_config(local_result, remote_results, config.MCMOTD_CLIENT_NAME or "本地", address, config.MCMOTD_SPECIAL_INFO_SHOW)
        await motd.finish(message)
        
    except FinishedException:
        raise
    except Exception as e:
        # 出错时也尝试撤回提示消息
        try:
            await bot.delete_msg(message_id=searching_msg_id)
        except:
            pass
        logger.error(f"查询服务器失败: {e}")
        await motd.finish(f"查询失败: {str(e)}")

@motdpe.handle()
async def handle_motdpe(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """处理 Bedrock 版服务器状态查询命令"""
    address = args.extract_plain_text().strip()
    if not address:
        await motdpe.finish("请输入服务器地址,例如: /motdpe play.cubecraft.net")
    
    # 发送查询提示并获取消息ID
    searching_msg = await motdpe.send("正在查询服务器状态...")
    searching_msg_id = searching_msg["message_id"]
    
    try:
        # 查询本地服务器
        local_result = await query_bedrock_server(address)
        
        # 如果是服务器模式,查询所有客户端
        remote_results = []
        if config.MCMOTD_ENABLE_SERVER:
            from .ws.fastapi_wserver import get_server_instance
            srv = get_server_instance()
            if srv:
                logger.info(f"开始向客户端下发查询请求: {address}")
                remote_results = await srv.query_all_clients(
                    "bedrock", address, config.MCMOTD_SERVER_STATUS_TIMEOUT
                )
                logger.info(f"收到 {len(remote_results)} 个客户端响应")
            else:
                logger.warning("服务器实例未初始化")
        
        # 撤回查询提示消息
        await bot.delete_msg(message_id=searching_msg_id)
        
        # 格式化并发送结果
        message = format_bedrock_status_with_config(local_result, remote_results, config.MCMOTD_CLIENT_NAME or "本地", address, config.MCMOTD_SPECIAL_INFO_SHOW)
        await motdpe.finish(message)
        
    except FinishedException:
        raise
    except Exception as e:
        # 出错时也尝试撤回提示消息
        try:
            await bot.delete_msg(message_id=searching_msg_id)
        except:
            pass
        logger.error(f"查询服务器失败: {e}")
        await motdpe.finish(f"查询失败: {str(e)}")

@mcmotd.handle()
async def handle_mcmotd(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """处理插件管理命令"""
    command = args.extract_plain_text().strip().lower()
    
    if command == "client list":
        # 显示已连接的客户端列表
        if not config.MCMOTD_ENABLE_SERVER:
            await mcmotd.finish("服务器模式未启用")
        
        clients = get_connected_clients()
        if not clients:
            await mcmotd.finish("当前没有客户端连接")
        
        msg = "已连接的客户端:\n" + "\n".join(f"- {name}" for name in clients)
        await mcmotd.finish(msg)
        
    elif command == "server status":
        # 显示服务器状态信息
        status_lines = []
        
        if config.MCMOTD_ENABLE_SERVER:
            clients = get_connected_clients()
            status_lines.append(f"服务器模式: 已启用")
            status_lines.append(f"监听端口: {config.MCMOTD_SERVER_Port}")
            status_lines.append(f"已连接客户端: {len(clients)}/{len(config.MCMOTD_SERVER_ALLOW_NAMES)}")
            
            # 显示在线的服务器
            if clients:
                online_servers = ", ".join(clients)
                status_lines.append(f"在线服务器: {online_servers}")
        else:
            status_lines.append("服务器模式: 未启用")
        
        if config.MCMOTD_ENABLE_CLIENT:
            client_status = get_client_status()
            status_lines.append(f"\n客户端模式: 已启用")
            status_lines.append(f"客户端名称: {config.MCMOTD_CLIENT_NAME}")
            status_lines.append(f"连接状态: {client_status}")
        else:
            status_lines.append("\n客户端模式: 未启用")
        
        await mcmotd.finish("\n".join(status_lines))
    else:
        await mcmotd.finish("可用命令:\n/mcmotd client list - 查看客户端列表\n/mcmotd server status - 查看服务器状态")

@addmotd.handle()
async def handle_addmotd(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """处理添加快速查询服务器命令"""
    params = args.extract_plain_text().strip().split(maxsplit=1)
    
    if not params:
        await addmotd.finish("用法:\n/addmotd 地址 - 添加默认服务器\n/addmotd 别名 地址 - 添加别名服务器")
    
    group_id = str(event.group_id) if hasattr(event, 'group_id') else str(event.user_id)
    qm = get_quick_query_manager()
    
    if len(params) == 1:
        # 只有一个参数,作为默认服务器
        result = qm.add_server(group_id, "default", params[0])
        await addmotd.finish(result)
    elif len(params) == 2:
        # 两个参数,别名和地址
        alias, address = params
        result = qm.add_server(group_id, alias, address)
        await addmotd.finish(result)

@motdlist.handle()
async def handle_motdlist(bot: Bot, event: MessageEvent):
    """处理列出所有快速查询服务器命令"""
    group_id = str(event.group_id) if hasattr(event, 'group_id') else str(event.user_id)
    qm = get_quick_query_manager()
    
    servers = qm.list_servers(group_id)
    
    if not servers:
        await motdlist.finish("本群还没有添加任何服务器\n使用 /addmotd 添加服务器")
    
    # 格式化输出
    lines = ["本群已添加的服务器别名:"]
    
    # 优先显示默认服务器
    if "default" in servers:
        lines.append(f"default(默认): {servers['default']}")
    
    # 显示其他别名
    for alias, address in servers.items():
        if alias != "default":
            lines.append(f"{alias}: {address}")
    
    await motdlist.finish("\n".join(lines))

@delmotd.handle()
async def handle_delmotd(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """处理删除快速查询服务器命令"""
    alias = args.extract_plain_text().strip()
    
    if not alias:
        await delmotd.finish("请指定要删除的别名\n例如: /delmotd 别名\n或: /delmotd default")
    
    group_id = str(event.group_id) if hasattr(event, 'group_id') else str(event.user_id)
    qm = get_quick_query_manager()
    
    result = qm.delete_server(group_id, alias)
    await delmotd.finish(result)

# 插件启动时初始化
driver = get_driver()

@driver.on_startup
async def startup():
    """插件启动时的初始化"""
    logger.info("MCMotd_MultiCon 插件启动中...")
    
    # 启动服务器模式
    if config.MCMOTD_ENABLE_SERVER:
        asyncio.create_task(start_server(config))
        logger.info(f"服务器模式已启动,监听端口: {config.MCMOTD_SERVER_Port}")
    
    # 启动客户端模式
    if config.MCMOTD_ENABLE_CLIENT:
        asyncio.create_task(start_client(config))
        logger.info(f"客户端模式已启动,连接到: {config.MCMOTD_CONNECT_SERVERS}")

@driver.on_shutdown
async def shutdown():
    """插件关闭时的清理"""
    logger.info("MCMotd_MultiCon 插件关闭中...")