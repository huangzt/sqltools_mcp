# SQLTools MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io)

[[English](README_EN.md)] | [中文]

一个功能强大的多数据库工具服务，基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 开发。它允许 AI 助手（如 Claude Desktop）直接连接、查询和分析各种类型的数据库。

## ✨ 核心特性

- 🔌 **广泛的数据库支持**：
  - **MySQL**: 使用 `pymysql`
  - **PostgreSQL**: 使用 `psycopg2-binary`
  - **SQL Server (MSSQL)**: 使用 `pymssql`
  - **达梦 (DM8)**: 使用 `jaydebeapi` (JDBC 驱动)
  - **SQLite**: 内置支持，无需额外驱动
- 🔄 **动态切换连接**：支持在同一个会话中随时切换到不同的数据库实例。
- 🌍 **智能配置**：支持通过环境变量预设默认连接，即插即用。
- 🛡️ **安全增强**：
  - **SQL 注入保护**：针对 SQLite 等标识符引用进行了安全加固。
  - **风险操作检查**：对 `DROP`、`TRUNCATE`、`DELETE` 等潜在破坏性操作提供预检提示。
- 📊 **性能优化**：
  - **分页支持**：工具如 `list_tables` 支持分页（limit/offset），防止处理大型 schema 时阻塞。
  - **智能提示**：当连接失败时提供具体的修复建议（Suggestions）。
- 📝 **符合 MCP 标准**：完整实现工具注解（Annotations），包括 `readOnlyHint`、`destructiveHint` 等。

## 📦 快速安装

推荐使用 `uv` 进行管理，也可以使用标准的 `pip`。

### 1. 克隆并安装环境
```bash
git clone https://github.com/huangzt/sqltools_mcp
cd sqltools-mcp
pip install -e .
```

### 2. 安装数据库驱动
根据你需要连接的数据库类型安装对应依赖：
```bash
# MySQL
pip install pymysql

# PostgreSQL
pip install psycopg2-binary

# SQL Server (MSSQL)
pip install pymssql

# 达梦 DM8 (需要安装 Java 环境)
pip install jaydebeapi JPype1
```

## ⚙️ 配置指南

### 环境变量
你可以在启动 MCP 服务时设置以下环境变量来实现自动连接：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DB_TYPE` | 数据库类型 (mysql, postgres, mssql, dm8, sqlite) | `sqlite` |
| `DB_HOST` | 数据库主机地址 | `localhost` |
| `DB_PORT` | 端口号 (0 则使用各协议默认端口) | `0` |
| `DB_USER` | 数据库用户名 | - |
| `DB_PASSWORD` | 数据库密码 | - |
| `DB_NAME` | 数据库名 (SQLite 为文件绝对路径) | - |

### 集成到 Claude Desktop

编辑你的 `claude_desktop_config.json` 文件：

```json
{
  "mcpServers": {
    "sqltools": {
      "command": "python",
      "args": ["-m", "sqltools_mcp.server"],
      "env": {
        "DB_TYPE": "mysql",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_USER": "root",
        "DB_PASSWORD": "your_password",
        "DB_NAME": "my_app_db"
      }
    }
  }
}
```

## 🛠️ 可用工具 (Tools)

所有工具接口说明现已统一使用 **英文**，以便 AI 模型更准确地理解和调用。

### 1. `connect_database`
连接或切换到目标数据库。
- **参数**: `dbtype`, `host`, `port`, `username`, `password`, `dbname`.
- **特性**: 自动断开旧连接，验证新连接可用性。

### 2. `execute_sql`
执行 SQL 查询。
- **参数**: `query` (必填), `timeout`.
- **特性**: 支持 SELECT 和 DML 语句；自动处理数据类型转换（如 Decimal 转换为 float，datetime 转换为 ISO 字符串）。

### 3. `list_tables`
列出数据库中的所有表。
- **参数**: `schema`, `limit` (默认 100), `offset` (默认 0).
- **特性**: 支持分页，返回表类型和行数估计。

### 4. `describe_table`
查看特定表的结构。
- **参数**: `table_name` (必填), `schema`.
- **特性**: 返回详尽的列信息：名称、类型、是否可空、主键标志、默认值等。

### 5. `get_connection_status`
检查当前连接状态。
- **特性**: 返回当前连接的协议类型和基本配置（不含密码）。

## 🗄️ 数据库适配器特别说明

### 达梦 DM8
- **驱动**: 自动搜索 `assets/DmJdbcDriver18.jar` 或环境变量 `DM_HOME`。
- **注意**: 确保系统中已安装 JRE/JDK 8+。

### SQLite
- **路径**: `dbname` 参数必须提供文件的**绝对路径**。
- **安全**: 已处理双引号转义，防止针对表名的注入。

### SQL Server
- Support SQL Server authentication.

## 🔧 开发与测试

### 使用 MCP Inspector
```bash
npx @modelcontextprotocol/inspector python -m sqltools_mcp.server
```

### 运行单元测试
```bash
pytest tests/
```

## 📄 开源协议
基于 [MIT License](LICENSE) 开源。
