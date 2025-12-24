"""SQL Server (MSSQL) database adapter using pymssql."""

from typing import Any
from decimal import Decimal
from datetime import datetime, date, timedelta

from .base import DatabaseAdapter, TableInfo, ColumnInfo, QueryResult

try:
    import pymssql
    PYMSSQL_AVAILABLE = True
except ImportError:
    PYMSSQL_AVAILABLE = False


class MSSQLAdapter(DatabaseAdapter):
    """SQL Server database adapter."""
    
    def __init__(self):
        super().__init__()
        if not PYMSSQL_AVAILABLE:
            raise ImportError("pymssql is not installed. Run: pip install pymssql")
    
    @property
    def db_type(self) -> str:
        return "mssql"
    
    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        dbname: str,
        **kwargs
    ) -> dict[str, Any]:
        """Connect to SQL Server database."""
        try:
            self._connection = pymssql.connect(
                server=host,
                port=port,
                user=username,
                password=password,
                database=dbname,
                login_timeout=10
            )
            self._connected = True
            
            # Get server info
            cursor = self._connection.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT DB_NAME()")
            current_db = cursor.fetchone()[0]
            cursor.execute("SELECT SYSTEM_USER")
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
        except pymssql.Error as e:
            self._connected = False
            raise ConnectionError(f"SQL Server connection failed: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from SQL Server database."""
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
            cursor = self._connection.cursor(as_dict=True)
            cursor.execute(sql)
            
            # Check if it's a SELECT query
            sql_upper = sql.strip().upper()
            is_select = (
                sql_upper.startswith("SELECT") or
                sql_upper.startswith("EXEC") or
                sql_upper.startswith("SP_") or
                sql_upper.startswith("WITH")
            )
            
            if is_select:
                raw_rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = []
                for row in raw_rows:
                    row_dict = {}
                    for col in row:
                        value = row[col]
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
        except pymssql.Error as e:
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
            schema_filter = schema if schema else 'dbo'
            cursor.execute("""
                SELECT 
                    t.TABLE_NAME,
                    t.TABLE_TYPE,
                    p.rows
                FROM INFORMATION_SCHEMA.TABLES t
                LEFT JOIN sys.partitions p ON p.object_id = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME) AND p.index_id IN (0, 1)
                WHERE t.TABLE_SCHEMA = %s
                ORDER BY t.TABLE_NAME
            """, (schema_filter,))
            
            tables = []
            for row in cursor.fetchall():
                tables.append(TableInfo(
                    name=row[0],
                    schema=schema_filter,
                    table_type=row[1] if row[1] else "TABLE",
                    row_count=row[2] if row[2] else None
                ))
            
            cursor.close()
            return tables
        except pymssql.Error:
            return []
    
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """Get table structure."""
        if not self._connected:
            return []
        
        try:
            cursor = self._connection.cursor()
            schema_filter = schema if schema else 'dbo'
            cursor.execute("""
                SELECT 
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.IS_NULLABLE,
                    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PRIMARY_KEY,
                    c.COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN (
                    SELECT ku.COLUMN_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                    WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                    AND tc.TABLE_SCHEMA = %s
                    AND tc.TABLE_NAME = %s
                ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE c.TABLE_SCHEMA = %s AND c.TABLE_NAME = %s
                ORDER BY c.ORDINAL_POSITION
            """, (schema_filter, table_name, schema_filter, table_name))
            
            columns = []
            for row in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == 'YES',
                    is_primary_key=bool(row[3]),
                    default_value=row[4]
                ))
            
            cursor.close()
            return columns
        except pymssql.Error:
            return []
