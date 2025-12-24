"""MySQL database adapter using PyMySQL."""

from typing import Any
from decimal import Decimal
from datetime import datetime, date, timedelta

from .base import DatabaseAdapter, TableInfo, ColumnInfo, QueryResult

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter."""
    
    def __init__(self):
        super().__init__()
        if not PYMYSQL_AVAILABLE:
            raise ImportError("pymysql is not installed. Run: pip install pymysql")
    
    @property
    def db_type(self) -> str:
        return "mysql"
    
    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        dbname: str,
        **kwargs
    ) -> dict[str, Any]:
        """Connect to MySQL database."""
        try:
            self._connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=dbname,
                connect_timeout=10,
                charset='utf8mb4'
            )
            self._connected = True
            
            # Get server info
            cursor = self._connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            cursor.execute("SELECT USER()")
            current_user = cursor.fetchone()[0]
            cursor.close()
            
            return {
                "success": True,
                "server_version": version,
                "current_database": current_db,
                "current_user": current_user,
                "host": host,
                "port": port,
            }
        except pymysql.Error as e:
            self._connected = False
            raise ConnectionError(f"MySQL connection failed: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from MySQL database."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        self._connected = False
    
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
                sql_upper.startswith("SHOW") or
                sql_upper.startswith("DESCRIBE") or
                sql_upper.startswith("EXPLAIN")
            )
            
            if is_select:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
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
        except pymysql.Error as e:
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
                SELECT TABLE_NAME, TABLE_TYPE, TABLE_ROWS
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME
            """)
            
            tables = []
            for row in cursor.fetchall():
                tables.append(TableInfo(
                    name=row[0],
                    table_type=row[1] if row[1] else "TABLE",
                    row_count=row[2] if row[2] else None
                ))
            
            cursor.close()
            return tables
        except pymysql.Error:
            return []
    
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """Get table structure."""
        if not self._connected:
            return []
        
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    COLUMN_DEFAULT,
                    EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == 'YES',
                    is_primary_key=row[3] == 'PRI',
                    default_value=row[4],
                    extra=row[5]
                ))
            
            cursor.close()
            return columns
        except pymysql.Error:
            return []
