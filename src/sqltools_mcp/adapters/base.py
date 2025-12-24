"""Base database adapter interface.

Defines the abstract interface that all database adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass


@dataclass
class TableInfo:
    """Table information."""
    name: str
    schema: str | None = None
    table_type: str = "TABLE"
    row_count: int | None = None


@dataclass
class ColumnInfo:
    """Column information."""
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    default_value: str | None = None
    extra: str | None = None


@dataclass
class QueryResult:
    """Query execution result."""
    success: bool
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    row_count: int = 0
    affected_rows: int | None = None
    message: str = ""
    error: str | None = None


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""
    
    def __init__(self):
        self._connection = None
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected
    
    @abstractmethod
    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        dbname: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Connect to the database.
        
        Returns:
            dict with connection info (version, current_user, etc.)
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the database."""
        pass
    
    @abstractmethod
    def execute_query(self, sql: str) -> QueryResult:
        """
        Execute a SQL query.
        
        Args:
            sql: SQL statement to execute
            
        Returns:
            QueryResult with execution results
        """
        pass
    
    @abstractmethod
    def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """
        List all tables in the database.
        
        Args:
            schema: Optional schema name to filter tables
            
        Returns:
            List of TableInfo objects
        """
        pass
    
    @abstractmethod
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """
        Get table structure/schema.
        
        Args:
            table_name: Name of the table
            schema: Optional schema name
            
        Returns:
            List of ColumnInfo objects
        """
        pass
    
    @property
    @abstractmethod
    def db_type(self) -> str:
        """Return the database type identifier."""
        pass
