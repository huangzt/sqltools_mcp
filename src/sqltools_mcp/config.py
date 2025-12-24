"""Configuration module for SQLTools MCP server.

Reads database connection parameters from environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    
    dbtype: str
    host: str
    port: int
    username: str
    password: str
    dbname: str
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables."""
        dbtype = os.getenv("DB_TYPE", "sqlite").lower()
        
        # Default ports for each database type
        default_ports = {
            "mysql": 3306,
            "postgres": 5432,
            "mssql": 1433,
            "dm8": 5236,
            "sqlite": 0,
        }
        
        port_str = os.getenv("DB_PORT", "")
        if port_str:
            port = int(port_str)
        else:
            port = default_ports.get(dbtype, 0)
        
        return cls(
            dbtype=dbtype,
            host=os.getenv("DB_HOST", "localhost"),
            port=port,
            username=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
            dbname=os.getenv("DB_NAME", ""),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excluding password for safety)."""
        return {
            "dbtype": self.dbtype,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "dbname": self.dbname,
        }


# Supported database types
SUPPORTED_DBTYPES = ["mysql", "postgres", "mssql", "dm8", "sqlite"]
