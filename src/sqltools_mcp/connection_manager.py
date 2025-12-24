"""Database connection manager for SQLTools MCP.

Manages database connections with support for runtime switching between databases.
Uses the lifespan pattern for MCP server integration.
"""

from dataclasses import dataclass
from typing import Any

from .config import DatabaseConfig
from .adapters import get_adapter
from .adapters.base import DatabaseAdapter, TableInfo, ColumnInfo, QueryResult


@dataclass
class DatabaseManager:
    """
    Manages database connections for the MCP server.
    
    Supports connecting to multiple database types and switching between them at runtime.
    """
    
    adapter: DatabaseAdapter | None = None
    config: DatabaseConfig | None = None
    connection_info: dict[str, Any] | None = None
    
    def connect(
        self,
        dbtype: str,
        host: str,
        port: int,
        username: str,
        password: str,
        dbname: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Connect to a database, disconnecting from any existing connection first.
        
        Args:
            dbtype: Database type (mysql, postgres, mssql, dm8, sqlite)
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            dbname: Database name (or file path for SQLite)
            **kwargs: Additional connection parameters
            
        Returns:
            dict with connection info
        """
        # Disconnect from existing connection if any
        if self.adapter and self.adapter.is_connected:
            self.disconnect()
        
        # Create new adapter and connect
        self.adapter = get_adapter(dbtype)
        self.connection_info = self.adapter.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            dbname=dbname,
            **kwargs
        )
        
        # Store config for reference
        self.config = DatabaseConfig(
            dbtype=dbtype,
            host=host,
            port=port,
            username=username,
            password=password,
            dbname=dbname
        )
        
        return self.connection_info
    
    def connect_from_config(self, config: DatabaseConfig) -> dict[str, Any]:
        """Connect using a DatabaseConfig object."""
        return self.connect(
            dbtype=config.dbtype,
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            dbname=config.dbname
        )
    
    def disconnect(self) -> None:
        """Disconnect from the current database."""
        if self.adapter:
            self.adapter.disconnect()
        self.adapter = None
        self.connection_info = None
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected to a database."""
        return self.adapter is not None and self.adapter.is_connected
    
    @property
    def current_db_type(self) -> str | None:
        """Get the current database type."""
        return self.adapter.db_type if self.adapter else None
    
    def execute_query(self, sql: str) -> QueryResult:
        """Execute a SQL query on the current connection."""
        if not self.adapter:
            return QueryResult(
                success=False,
                error="No database connection",
                message="请先使用 connect_database 连接数据库"
            )
        return self.adapter.execute_query(sql)
    
    def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """List all tables in the current database."""
        if not self.adapter:
            return []
        return self.adapter.list_tables(schema)
    
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """Get table structure."""
        if not self.adapter:
            return []
        return self.adapter.describe_table(table_name, schema)
