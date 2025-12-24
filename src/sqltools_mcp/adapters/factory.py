"""Database adapter factory.

Creates the appropriate database adapter based on database type.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import DatabaseAdapter


def get_adapter(dbtype: str) -> "DatabaseAdapter":
    """
    Get a database adapter instance for the specified database type.
    
    Args:
        dbtype: Database type (mysql, postgres, mssql, dm8, sqlite)
        
    Returns:
        DatabaseAdapter instance
        
    Raises:
        ValueError: If database type is not supported
    """
    dbtype = dbtype.lower()
    
    if dbtype == "mysql":
        from .mysql import MySQLAdapter
        return MySQLAdapter()
    elif dbtype == "postgres" or dbtype == "postgresql":
        from .postgres import PostgresAdapter
        return PostgresAdapter()
    elif dbtype == "mssql" or dbtype == "sqlserver":
        from .mssql import MSSQLAdapter
        return MSSQLAdapter()
    elif dbtype == "dm8" or dbtype == "dameng":
        from .dm8 import DM8Adapter
        return DM8Adapter()
    elif dbtype == "sqlite":
        from .sqlite import SQLiteAdapter
        return SQLiteAdapter()
    else:
        supported = ["mysql", "postgres", "mssql", "dm8", "sqlite"]
        raise ValueError(f"Unsupported database type: {dbtype}. Supported types: {supported}")
