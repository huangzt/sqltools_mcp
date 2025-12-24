# SQLTools MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0.0-orange.svg)](https://modelcontextprotocol.io)

[English] | [[中文](README.md)]

A powerful multi-database tool service built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io). It allows AI assistants (like Claude Desktop) to directly connect to, query, and analyze various types of databases.

## ✨ Key Features

- 🔌 **Extensive Database Support**:
  - **MySQL**: via `pymysql`
  - **PostgreSQL**: via `psycopg2-binary`
  - **SQL Server (MSSQL)**: via `pymssql`
  - **Dameng (DM8)**: via `jaydebeapi` (JDBC Driver)
  - **SQLite**: Built-in support, no extra driver needed
- 🔄 **Dynamic Connection Switching**: Switch between different database instances anytime within the same session.
- 🌍 **Smart Configuration**: Supports environment variables for pre-set default connections (Plug & Play).
- 🛡️ **Enhanced Security**:
  - **SQL Injection Protection**: Hardened identifier quoting for SQLite and other adapters.
  - **Risk Operation Checks**: Preliminary prompts for potentially destructive operations like `DROP`, `TRUNCATE`, and `DELETE`.
- 📊 **Performance Optimization**:
  - **Pagination Support**: Tools like `list_tables` support pagination (`limit`/`offset`) to prevent blocking on large schemas.
  - **Intelligent Suggestions**: Provides specific fixing suggestions when connection fails.
- 📝 **MCP Compliant**: Full implementation of tool Annotations, including `readOnlyHint`, `destructiveHint`, etc.

## 📦 Quick Start

Management via `uv` is recommended, though standard `pip` is also supported.

### 1. Clone and Install
```bash
git clone https://github.com/huangzt/sqltools_mcp
cd sqltools-mcp
pip install -e .
```

### 2. Install Database Drivers
Install the dependencies corresponding to the database types you need:
```bash
# MySQL
pip install pymysql

# PostgreSQL
pip install psycopg2-binary

# SQL Server (MSSQL)
pip install pymssql

# Dameng DM8 (Requires Java Environment)
pip install jaydebeapi JPype1
```

## ⚙️ Configuration Guide

### Environment Variables
You can set the following environment variables when starting the MCP service for auto-connection:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_TYPE` | Database type (mysql, postgres, mssql, dm8, sqlite) | `sqlite` |
| `DB_HOST` | Database host address | `localhost` |
| `DB_PORT` | Port number (0 uses protocol default) | `0` |
| `DB_USER` | Database username | - |
| `DB_PASSWORD` | Database password | - |
| `DB_NAME` | Database name (Absolute file path for SQLite) | - |

### Integration with Claude Desktop

Edit your `claude_desktop_config.json` file:

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

## 🛠️ Available Tools

All tool interfaces are standardized in **English** for better AI model comprehension.

### 1. `connect_database`
Connect or switch to a target database.
- **Parameters**: `dbtype`, `host`, `port`, `username`, `password`, `dbname`.
- **Features**: Automatically disconnects old connections and verifies the new connection's availability.

### 2. `execute_sql`
Execute SQL queries.
- **Parameters**: `query` (required), `timeout`.
- **Features**: Supports SELECT and DML statements; automatically handles data type conversions (e.g., Decimal to float, datetime to ISO string).

### 3. `list_tables`
List all tables in the database.
- **Parameters**: `schema`, `limit` (default 100), `offset` (default 0).
- **Features**: Supports pagination, returns table types and row count estimates.

### 4. `describe_table`
Inspect the structure of a specific table.
- **Parameters**: `table_name` (required), `schema`.
- **Features**: Returns detailed column info: name, type, nullability, primary key flags, default values, etc.

### 5. `get_connection_status`
Check the current connection status.
- **Features**: Returns the current connection protocol and basic config (excluding password).

## 🗄️ Adapter-Specific Notes

### Dameng DM8
- **Driver**: Automatically searches for `assets/DmJdbcDriver18.jar` or environment variable `DM_HOME`.
- **Note**: Ensure JRE/JDK 8+ is installed in the system.

### SQLite
- **Path**: The `dbname` parameter must be the **absolute path** to the file.
- **Security**: Handles double-quote escaping to prevent injection via table names.

### SQL Server
- Supports SQL Server authentication.

## 🔧 Development & Testing

### Using MCP Inspector
```bash
npx @modelcontextprotocol/inspector python -m sqltools_mcp.server
```

### Running Unit Tests
```bash
pytest tests/
```

## 📄 License
Licensed under [MIT License](LICENSE).
