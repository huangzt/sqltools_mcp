"""SQLTools MCP Server.

A multi-database MCP server supporting MySQL, PostgreSQL, SQL Server, DM8, and SQLite.
Provides tools for database connection, SQL execution, table listing, and schema inspection.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

from .config import DatabaseConfig, SUPPORTED_DBTYPES
from .connection_manager import DatabaseManager


@dataclass
class AppContext:
    """Application context with database manager."""
    db: DatabaseManager


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage application lifecycle.
    
    On startup: Create database manager and optionally connect using environment variables.
    On shutdown: Disconnect from database.
    """
    db_manager = DatabaseManager()
    
    # Try to connect using environment variables on startup
    try:
        config = DatabaseConfig.from_env()
        # Only auto-connect if we have the minimum required info
        if config.dbname or config.dbtype == "sqlite":
            if config.dbtype != "sqlite" and (config.username and config.password):
                db_manager.connect_from_config(config)
            elif config.dbtype == "sqlite" and config.dbname:
                db_manager.connect_from_config(config)
    except Exception:
        # If auto-connect fails, just continue - user can connect manually
        pass
    
    try:
        yield AppContext(db=db_manager)
    finally:
        # Cleanup on shutdown
        db_manager.disconnect()


# Create MCP server with lifespan
mcp = FastMCP(
    "SQLTools MCP",
    lifespan=app_lifespan,
    json_response=True
)


@mcp.tool(annotations={
    "readOnlyHint": False,
    "idempotentHint": False
})
def connect_database(
    ctx: Context[ServerSession, AppContext],
    dbtype: Annotated[str, "Database type: mysql, postgres, mssql, dm8, sqlite"],
    host: Annotated[str, "Database host address, can be ignored for SQLite"] = "localhost",
    port: Annotated[int, "Database port, automatically set based on dbtype if 0"] = 0,
    username: Annotated[str, "Database username, can be ignored for SQLite"] = "",
    password: Annotated[str, "Database password, can be ignored for SQLite"] = "",
    dbname: Annotated[str, "Database name, or file path for SQLite"] = "",
) -> dict:
    """
    Connect to a specified database. Disconnects existing connections first.
    
    Supported types: mysql, postgres, mssql, dm8, sqlite
    
    For SQLite, 'dbname' should be the absolute file path.
    For others, provide host, port, username, and password.
    """
    dbtype = dbtype.lower()
    
    if dbtype not in SUPPORTED_DBTYPES:
        return {
            "success": False,
            "error": f"Unsupported database type: {dbtype}",
            "supported_types": SUPPORTED_DBTYPES
        }
    
    # Set default port if not specified
    if port == 0:
        default_ports = {
            "mysql": 3306,
            "postgres": 5432,
            "mssql": 1433,
            "dm8": 5236,
            "sqlite": 0,
        }
        port = default_ports.get(dbtype, 0)
    
    db_manager = ctx.request_context.lifespan_context.db
    
    try:
        result = db_manager.connect(
            dbtype=dbtype,
            host=host,
            port=port,
            username=username,
            password=password,
            dbname=dbname
        )
        return {
            "success": True,
            "message": f"Successfully connected to {dbtype} database",
            "connection_info": result
        }
    except Exception as e:
        suggestions = [
            "Verify the host address is correct",
            "Check if the port is accessible and not blocked by a firewall",
            "Ensure username and password are accurate",
            "Confirm the database service is running on the target host"
        ]
        if dbtype == "sqlite":
            suggestions = ["Check if the database file path exists", "Verify file permissions"]
            
        return {
            "success": False,
            "error": str(e),
            "message": "Database connection failed",
            "suggestions": suggestions
        }


@mcp.tool(annotations={
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False
})
def execute_sql(
    ctx: Context[ServerSession, AppContext],
    query: Annotated[str, "The SQL query to execute"],
    timeout: Annotated[int, "Query timeout in seconds"] = 30,
) -> dict:
    """
    Execute a SQL statement on the current connection.
    
    Supports SELECT queries and DML (INSERT/UPDATE/DELETE).
    Ensure you are connected using connect_database first.
    Be cautious with destructive operations like DROP/DELETE/TRUNCATE.
    """
    # Simple risk check
    dangerous_keywords = ['DROP', 'TRUNCATE', 'DELETE']
    sql_upper = query.strip().upper()
    is_dangerous = any(keyword in sql_upper for keyword in dangerous_keywords)
    
    if is_dangerous and 'WHERE' not in sql_upper and 'DELETE' in sql_upper:
       # Potential warning logic could go here
       pass

    db_manager = ctx.request_context.lifespan_context.db
    
    if not db_manager.is_connected:
        return {
            "success": False,
            "error": "Database not connected",
            "message": "Please connect to a database using connect_database first",
            "suggestions": ["Use connect_database tool to establish a connection"]
        }
    
    try:
        result = db_manager.execute_query(query)
        
        return {
            "success": result.success,
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "affected_rows": result.affected_rows,
            "message": result.message,
            "error": result.error
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred during SQL execution"
        }


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True
})
def list_tables(
    ctx: Context[ServerSession, AppContext],
    schema: Annotated[str | None, "Schema name (optional)"] = None,
    limit: Annotated[int, "Maximum number of tables to return"] = 100,
    offset: Annotated[int, "Number of tables to skip"] = 0,
) -> dict:
    """
    List all tables in the current database.
    
    Returns table names, types, and row count estimates.
    Supports pagination, defaults to the first 100 tables.
    Ensure you are connected using connect_database first.
    """
    db_manager = ctx.request_context.lifespan_context.db
    
    if not db_manager.is_connected:
        return {
            "success": False,
            "error": "Database not connected",
            "message": "Please connect to a database using connect_database first",
            "suggestions": ["Use connect_database tool to establish a connection"]
        }
    
    try:
        tables = db_manager.list_tables(schema)
        total_count = len(tables)
        
        start = max(0, offset)
        end = min(total_count, start + limit)
        paged_tables = tables[start:end]
        
        return {
            "success": True,
            "tables": [
                {
                    "name": t.name,
                    "schema": t.schema,
                    "type": t.table_type,
                    "row_count": t.row_count
                }
                for t in paged_tables
            ],
            "table_count": len(paged_tables),
            "total_count": total_count,
            "offset": start,
            "limit": limit,
            "message": f"Found {total_count} tables, showing {start+1}-{end}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list tables"
        }


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True
})
def describe_table(
    ctx: Context[ServerSession, AppContext],
    table_name: Annotated[str, "The name of the table"],
    schema: Annotated[str | None, "Schema name (optional)"] = None,
) -> dict:
    """
    Inspect the schema of a specific table.
    
    Returns column names, data types, nullability, keys, and default values.
    Ensure you are connected using connect_database first.
    """
    db_manager = ctx.request_context.lifespan_context.db
    
    if not db_manager.is_connected:
        return {
            "success": False,
            "error": "Database not connected",
            "message": "Please connect to a database using connect_database first",
            "suggestions": ["Use connect_database tool to establish a connection"]
        }
    
    try:
        columns = db_manager.describe_table(table_name, schema)
        
        if not columns:
            return {
                "success": False,
                "error": f"Table '{table_name}' not found or schema unavailable",
                "message": "Failed to get table schema",
                "suggestions": ["Check if the table name is correct", "Verify the schema", "Try list_tables to see available tables"]
            }
        
        return {
            "success": True,
            "table_name": table_name,
            "schema": schema,
            "columns": [
                {
                    "name": c.name,
                    "type": c.data_type,
                    "nullable": c.nullable,
                    "primary_key": c.is_primary_key,
                    "default": c.default_value,
                    "extra": c.extra
                }
                for c in columns
            ],
            "column_count": len(columns),
            "message": f"Table '{table_name}' has {len(columns)} columns"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Error occurred while describing table '{table_name}'"
        }


@mcp.tool(annotations={
    "readOnlyHint": True,
    "idempotentHint": True
})
def get_connection_status(
    ctx: Context[ServerSession, AppContext],
) -> dict:
    """
    Retrieve current database connection status.
    
    Returns connection status, database type, and configuration info.
    """
    db_manager = ctx.request_context.lifespan_context.db
    
    if not db_manager.is_connected:
        return {
            "connected": False,
            "message": "Not connected to any database"
        }
    
    return {
        "connected": True,
        "db_type": db_manager.current_db_type,
        "connection_info": db_manager.config.to_dict() if db_manager.config else None,
        "message": f"Connected to {db_manager.current_db_type} database"
    }


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
