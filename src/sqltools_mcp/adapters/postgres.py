"""PostgreSQL database adapter using psycopg2."""

from typing import Any
from decimal import Decimal
from datetime import datetime, date, timedelta

from .base import DatabaseAdapter, TableInfo, ColumnInfo, QueryResult

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""
    
    def __init__(self):
        super().__init__()
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is not installed. Run: pip install psycopg2-binary")
    
    @property
    def db_type(self) -> str:
        return "postgres"
    
    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        dbname: str,
        **kwargs
    ) -> dict[str, Any]:
        """Connect to PostgreSQL database."""
        try:
            self._connection = psycopg2.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                dbname=dbname,
                connect_timeout=10
            )
            self._connected = True
            
            # Get server info
            cursor = self._connection.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT current_database()")
            current_db = cursor.fetchone()[0]
            cursor.execute("SELECT current_user")
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
        except psycopg2.Error as e:
            self._connected = False
            raise ConnectionError(f"PostgreSQL connection failed: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from PostgreSQL database."""
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
                sql_upper.startswith("WITH") or
                sql_upper.startswith("SHOW") or
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
        except psycopg2.Error as e:
            self._connection.rollback()
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
            schema_filter = schema if schema else 'public'
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type,
                    (SELECT reltuples::bigint FROM pg_class WHERE relname = table_name) as row_count
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
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
        except psycopg2.Error:
            return []
    
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """Get table structure."""
        if not self._connected:
            return []
        
        try:
            cursor = self._connection.cursor()
            schema_filter = schema if schema else 'public'
            cursor.execute("""
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                    c.column_default
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT ku.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage ku
                        ON tc.constraint_name = ku.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                ) pk ON c.column_name = pk.column_name
                WHERE c.table_schema = %s AND c.table_name = %s
                ORDER BY c.ordinal_position
            """, (schema_filter, table_name, schema_filter, table_name))
            
            columns = []
            for row in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == 'YES',
                    is_primary_key=row[3],
                    default_value=row[4]
                ))
            
            cursor.close()
            return columns
        except psycopg2.Error:
            return []
