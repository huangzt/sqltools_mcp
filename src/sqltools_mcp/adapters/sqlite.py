"""SQLite database adapter using built-in sqlite3 module."""

import os
import sqlite3
from typing import Any
from decimal import Decimal
from datetime import datetime, date, timedelta

from .base import DatabaseAdapter, TableInfo, ColumnInfo, QueryResult


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""
    
    def __init__(self):
        super().__init__()
        self._db_path = None
    
    @property
    def db_type(self) -> str:
        return "sqlite"
    
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
        Connect to SQLite database.
        
        For SQLite, 'dbname' is the file path to the database.
        'host', 'port', 'username', 'password' are ignored.
        """
        try:
            # dbname is the file path for SQLite
            db_path = dbname
            
            # Check if file exists (unless it's :memory:)
            if db_path != ":memory:" and not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            self._db_path = os.path.abspath(db_path) if db_path != ":memory:" else db_path
            self._connection = sqlite3.connect(self._db_path)
            self._connection.row_factory = sqlite3.Row
            self._connected = True
            
            # Get SQLite version and file info
            cursor = self._connection.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            file_size = None
            if self._db_path != ":memory:":
                file_size = os.path.getsize(self._db_path)
            
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            cursor.close()
            
            return {
                "success": True,
                "sqlite_version": version,
                "database_path": self._db_path,
                "file_size_bytes": file_size,
                "table_count": table_count,
            }
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"SQLite connection failed: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from SQLite database."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        self._connected = False
        self._db_path = None
    
    def execute_query(self, sql: str) -> QueryResult:
        """Execute a SQL query."""
        if not self._connected or not self._connection:
            return QueryResult(
                success=False,
                error="Not connected to database",
                message="请先连接数据库"
            )
        
        try:
            cursor = self._connection.cursor()
            cursor.execute(sql)
            
            # Check if it's a SELECT query
            sql_upper = sql.strip().upper()
            is_select = (
                sql_upper.startswith("SELECT") or
                sql_upper.startswith("PRAGMA") or
                sql_upper.startswith("EXPLAIN")
            )
            
            if is_select and cursor.description:
                columns = [desc[0] for desc in cursor.description]
                raw_rows = cursor.fetchall()
                rows = []
                for row in raw_rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Handle special types
                        if isinstance(value, Decimal):
                            value = float(value)
                        elif isinstance(value, (datetime, date)):
                            value = value.isoformat()
                        elif isinstance(value, timedelta):
                            value = str(value)
                        elif isinstance(value, bytes):
                            value = value.decode('utf-8', errors='replace')
                        row_dict[col] = value
                    rows.append(row_dict)
                
                cursor.close()
                return QueryResult(
                    success=True,
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    message=f"查询成功，返回 {len(rows)} 行"
                )
            else:
                self._connection.commit()
                affected = cursor.rowcount
                cursor.close()
                return QueryResult(
                    success=True,
                    affected_rows=affected,
                    message=f"执行成功，影响 {affected} 行"
                )
        except sqlite3.Error as e:
            return QueryResult(
                success=False,
                error=str(e),
                message="SQL 执行失败"
            )
    
    def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """List all tables in the database."""
        if not self._connected:
            return []
        
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT name, type
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = []
            for row in cursor.fetchall():
                # Get row count for each table
                table_name = row[0]
                try:
                    # Safe identifier escaping
                    escaped_name = table_name.replace('"', '""')
                    cursor.execute(f'SELECT COUNT(*) FROM "{escaped_name}"')
                    row_count = cursor.fetchone()[0]
                except sqlite3.Error:
                    row_count = None
                
                tables.append(TableInfo(
                    name=table_name,
                    table_type=row[1].upper(),
                    row_count=row_count
                ))
            
            cursor.close()
            return tables
        except sqlite3.Error:
            return []
    
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """Get table structure."""
        if not self._connected:
            return []
        
        try:
            cursor = self._connection.cursor()
            # Safe identifier escaping
            escaped_name = table_name.replace('"', '""')
            cursor.execute(f'PRAGMA table_info("{escaped_name}")')
            
            columns = []
            for row in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=row[1],  # name
                    data_type=row[2],  # type
                    nullable=not row[3],  # notnull (inverted)
                    is_primary_key=bool(row[5]),  # pk
                    default_value=row[4]  # dflt_value
                ))
            
            cursor.close()
            return columns
        except sqlite3.Error:
            return []
