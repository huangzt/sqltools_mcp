# SQLTools MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io)

[English] | [[中文](README.md)]

**SQLTools MCP** is an all-in-one database access service built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).

The core value is: **Stop installing separate MCP servers for every single database. This one service provides AI assistants with unified support for MySQL, Postgres, SQL Server, Dameng (DM8), and SQLite.**

## ✨ Features

- 🔌 **Unified Database Support**:
  - **MySQL** / **MariaDB**
  - **PostgreSQL**
  - **SQL Server (MSSQL)**
  - **Dameng (DM8)** (Major Chinese enterprise DB)
  - **SQLite** (Local file DB)
- 🔄 **Hot Switching**: Switch between different database environments or types anytime within the same AI session via `connect_database`.
- 🛡️ **Production Ready**: Built-in SQL injection protection and warning prompts for destructive operations (DROP, TRUNCATE, etc.).
- 📊 **Optimized UX**: Supports pagination for large tables and provides smart fix suggestions for connection errors.

## 📦 Quick Install

```bash
# Clone the repository
git clone https://github.com/huangzt/sqltools_mcp
cd sqltools-mcp

# Install in editable mode
pip install -e .

# Install required drivers as needed
pip install pymysql          # MySQL
pip install psycopg2-binary  # PostgreSQL
pip install pymssql          # SQL Server
pip install jaydebeapi       # DM8 (Requires Java/JRE)
```

## 🚀 AI Client Configuration

`sqltools-mcp` is compatible with any AI client that supports the MCP protocol.

### 1. Claude Desktop

Edit your `claude_desktop_config.json`:
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

Add a new MCP server in **Settings -> Features -> MCP** (Cursor) or **Settings -> MCP** (Windsurf):

- **Name**: `sqltools`
- **Type**: `command`
- **Command**: `python -m sqltools_mcp.server`

*(Note: Ensure the environment or the full path of `python` is correctly specified.)*

### 3. Roo Code (VS Code Extension)

Open Roo Code **Settings**, go to **MCP Servers** -> **Edit Settings**, and add:

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

## 🛠️ Tools

AI models can interact with your databases using these English tools:

- `connect_database`: Connect/Switch to a database. Supports `dbtype`.
- `execute_sql`: Run any SQL statement.
- `list_tables`: Show table names (with limit/offset support).
- `describe_table`: Get detailed schema/column information.
- `get_connection_status`: Retrieve current connection info.

## 🛡️ Security

Check `SECURITY.md` for details on protection measures like identifier escaping and destructive operation warnings.

## 📄 License
Licensed under [MIT License](LICENSE).
