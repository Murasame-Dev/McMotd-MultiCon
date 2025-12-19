# MCMotd-MultiConnect

MCMotd-MultiConnect 是一个为 [Nonebot2](https://nonebot.dev/) 设计的功能强大的 Minecraft 服务器状态查询插件。它不仅可以查询单个 Minecraft 服务器（Java 版和基岩版）的状态，还独创性地支持**多节点分布式查询**。

通过其内置的 WebSocket 服务器和客户端，您可以将多个运行在不同网络环境下的机器人实例连接起来，实现从多个地理位置同时查询同一个服务器，并将结果聚合展示。这对于网络复杂的服务器或者需要多线路测试的场景非常有用。

## ✨ 功能特性

- **多版本支持**: 同时支持 Minecraft Java 版和基岩版（Bedrock/PE）服务器。
- **分布式查询**: 支持设置一个主干节点（Server）和多个子节点（Client），实现多点同时查询和结果聚合。
- **详细信息展示**: 显示服务器 MOTD、版本、在线玩家数、延迟、图标等丰富信息。
- **高度可配置**: 所有功能均可通过 `.env` 文件进行灵活配置，轻松启用或禁用不同模式。
- **管理命令**: 内置命令，方便查询已连接的客户端列表和插件运行状态。

## 🚀 如何开始

**运行机器人**:
  ```bash
  uv run nb run
  ```

## 📖 命令列表

### 查询命令

- **/motd <服务器地址>**
  查询指定地址的 Java 版服务器状态。
  - **示例**: `/motd mc.hypixel.net`

- **/motdpe <服务器地址>**
  查询指定地址的基岩版（Bedrock/PE）服务器状态。
  - **示例**: `/motdpe play.cubecraft.net`

### 管理命令

- **/mcmotd client list**
  （仅在服务器模式下可用）查询所有已连接到主干节点的客户端列表。

- **/mcmotd server status**
  查询插件当前的运行状态，包括服务器/客户端模式的启用情况、连接状态等。

## ⚙️ 配置指南

所有配置项都需要在您的 Nonebot 项目的 `.env` 文件中设置（如 `.env.prod`）。

### 服务器模式配置（主干节点）

当您希望一个实例作为接收命令和聚合结果的主干时，启用此模式。

- `MCMOTD_ENABLE_SERVER`
  - **说明**: 是否启用服务器模式。
  - **类型**: `bool`
  - **默认值**: `False`
  - **示例**: `MCMOTD_ENABLE_SERVER=true`

- `MCMOTD_SERVER_IP`
  - **说明**: 服务器监听的 IP 地址。
  - **类型**: `str`
  - **默认值**: `"127.0.0.1"`
  - **示例**: `MCMOTD_SERVER_IP="0.0.0.0"`

- `MCMOTD_SERVER_PORT`
  - **说明**: 服务器监听的端口。
  - **类型**: `int`
  - **默认值**: `60000`
  - **示例**: `MCMOTD_SERVER_PORT=65432`

- `MCMOTD_SERVER_ALLOW_NAMES`
  - **说明**: 允许连接的客户端名称列表（JSON 数组格式）。
  - **类型**: `List[str]`
  - **默认值**: `[]`
  - **示例**: `MCMOTD_SERVER_ALLOW_NAMES='["client-a", "client-b"]'`

- `MCMOTD_SERVER_STATUS_TIMEOUT`
  - **说明**: 等待所有客户端返回查询结果的超时时间（秒）。
  - **类型**: `int`
  - **默认值**: `10`
  - **示例**: `MCMOTD_SERVER_STATUS_TIMEOUT=15`

### 客户端模式配置（子节点）

当您希望一个实例作为执行查询任务的子节点时，启用此模式。

- `MCMOTD_ENABLE_CLIENT`
  - **说明**: 是否启用客户端模式。
  - **类型**: `bool`
  - **默认值**: `False`
  - **示例**: `MCMOTD_ENABLE_CLIENT=true`

- `MCMOTD_CONNECT_SERVERS`
  - **说明**: 要连接的主干服务器地址列表（JSON 数组格式）。
  - **类型**: `List[str]`
  - **默认值**: `[]`
  - **示例**: `MCMOTD_CONNECT_SERVERS='["ws://127.0.0.1:60000"]'`

- `MCMOTD_CLIENT_NAME`
  - **说明**: 客户端的唯一名称，必须与服务器 `MCMOTD_SERVER_ALLOW_NAMES` 中的名称对应。
  - **类型**: `str`
  - **默认值**: `""`
  - **示例**: `MCMOTD_CLIENT_NAME="client-a"`

### 通用配置

- `MCMOTD_SERVER_TOKEN`
  - **说明**: WebSocket 连接的认证令牌（密码），服务器和客户端必须一致。
  - **类型**: `str`
  - **默认值**: `""`
  - **示例**: `MCMOTD_SERVER_TOKEN="your_secret_token"`

- `MCMOTD_SPECIAL_INFO_SHOW`
  - **说明**: 是否在结果中显示来自不同节点的特殊信息（如独立的 IP 地址）。
  - **类型**: `bool`
  - **默认值**: `False`
  - **示例**: `MCMOTD_SPECIAL_INFO_SHOW=true`

## 🌐 部署模式示例

### 场景：一台主机器人 + 两台子机器人

假设您有三台服务器，分别位于电信、联通和移动网络，希望从三个点同时查询服务器状态。

**1. 主干机器人配置 (`.env.prod`)**

这台机器人负责接收用户的命令，并向其他两台机器人下发任务。

```dotenv
# 启用服务器模式
MCMOTD_ENABLE_SERVER=true
# 监听所有网络接口
MCMOTD_SERVER_IP="0.0.0.0"
# 设置一个端口
MCMOTD_SERVER_PORT=60000
# 允许连接的客户端名称
MCMOTD_SERVER_ALLOW_NAMES='["telecom-node", "mobile-node"]'
# 设置连接密码
MCMOTD_SERVER_TOKEN="a_very_secure_password"
```

**2. 子节点 A（电信）配置 (`.env.prod`)**

```dotenv
# 启用客户端模式
MCMOTD_ENABLE_CLIENT=true
# 自己的名字，要和服务器配置里的一致
MCMOTD_CLIENT_NAME="telecom-node"
# 主干服务器的地址
MCMOTD_CONNECT_SERVERS='["ws://<主干服务器的IP>:60000"]'
# 连接密码，要和服务器一致
MCMOTD_SERVER_TOKEN="a_very_secure_password"
```

**3. 子节点 B（移动）配置 (`.env.prod`)**

```dotenv
# 启用客户端模式
MCMOTD_ENABLE_CLIENT=true
# 自己的名字
MCMOTD_CLIENT_NAME="mobile-node"
# 主干服务器的地址
MCMOTD_CONNECT_SERVERS='["ws://<主干服务器的IP>:60000"]'
# 连接密码
MCMOTD_SERVER_TOKEN="a_very_secure_password"
```

配置完成后，依次启动所有机器人实例。现在，当您向主干机器人发送 `/motd` 命令时，它会同时从本地、电信节点和移动节点三个位置查询服务器，并将结果一同展示给您。
