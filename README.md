# SQLTools MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io)

[[English](README_EN.md)] | [中文]

**SQLTools MCP** 是一个全能型数据库访问服务，基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 开发。

它的核心痛点解决能力是：**无需为每种数据库安装独立的 MCP Server，只需这一个服务，即可让 AI 助手同时支持 MySQL、Postgres、SQL Server、达梦 (DM8) 以及 SQLite。**

## ✨ 核心能力

- 🔌 **全能数据库适配**：
  - **MySQL** / **MariaDB**
  - **PostgreSQL**
  - **SQL Server (MSSQL)**
  - **达梦 (DM8)** (国内主流国产数据库)
  - **SQLite** (本地文件数据库)
- 🔄 **一键切换**：同一个 AI 会话中可以随时通过 `connect_database` 切换到不同的数据库环境。
- 🛡️ **生产安全**：具备 SQL 注入防护和针对破坏性操作（DROP/TRUNCATE 等）的预警提示。
- 📊 **优化体验**：支持大数据量分页加载，失败时提供智能修复建议。

## 📦 快速安装

```bash
# 克隆并进入目录
git clone https://github.com/huangzt/sqltools_mcp
cd sqltools-mcp

# 建议在虚拟环境中安装
pip install -e .

# 安装您需要的驱动
pip install pymysql          # MySQL
pip install psycopg2-binary  # PostgreSQL
pip install pymssql          # SQL Server
pip install jaydebeapi       # DM8 (需要 Java 环境)
```

## 🚀 AI 开发工具配置

`sqltools-mcp` 兼容所有支持 MCP 协议的 AI 客户端。

### 1. Claude Desktop (官方客户端)

编辑 `claude_desktop_config.json`:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sqltools": {
      "command": "python",
      "args": ["-m", "sqltools_mcp.server"],
      "env": {
        "DB_TYPE": "sqlite",
        "DB_NAME": "/path/to/your/db.sqlite"
      }
    }
  }
}
```

### 2. Cursor / Windsurf

在 **Settings -> Features -> MCP** (Cursor) 或 **Settings -> MCP** (Windsurf) 中添加：

- **Name**: `sqltools`
- **Type**: `command`
- **Command**: `python -m sqltools_mcp.server`

*(注意：请确保 `python` 环境已安装了上述依赖，或者提供 python 的完整路径)*

### 3. Roo Code (VS Code 插件)

点击 Roo Code 面板顶部的 **Settings** 按钮，在 **MCP Servers** -> **Edit Settings** (MCP Config) 中添加：

```json
"sqltools": {
  "command": "python",
  "args": ["-m", "sqltools_mcp.server"],
  "env": {
    "DB_TYPE": "mysql",
    "DB_HOST": "localhost",
    "DB_USER": "root",
    "DB_PASSWORD": "password",
    "DB_NAME": "test"
  }
}
```

## 🛠️ 工具说明 (Tools)

AI 模型可以通过以下英文接口与数据库交互：

- `connect_database`: 连接/切换数据库。支持 dbtype (mysql, postgres, etc.)。
- `execute_sql`: 执行任意 SQL 语句。
- `list_tables`: 列出表名（支持 limit/offset 分页）。
- `describe_table`: 查看表结构详情。
- `get_connection_status`: 获取当前连接状态。

## �️ 安全性

本项目在 `SECURITY.md` 中详细列出了安全措施，包括表名转义和破坏性操作提醒，确保 AI 在操作数据库时的基本安全性。

## 📄 开源协议
基于 [MIT License](LICENSE) 开源。
