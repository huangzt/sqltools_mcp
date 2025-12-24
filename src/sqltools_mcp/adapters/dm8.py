"""DM8 (达梦) database adapter using jaydebeapi JDBC driver."""

import os
from typing import Any
from decimal import Decimal
from datetime import datetime, date, timedelta

from .base import DatabaseAdapter, TableInfo, ColumnInfo, QueryResult

try:
    import jaydebeapi
    JAYDEBEAPI_AVAILABLE = True
except ImportError:
    JAYDEBEAPI_AVAILABLE = False


def find_dm_jdbc_driver() -> str | None:
    """Find DM8 JDBC driver path."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 正确的相对路径：从 adapters/ 向上到 src/sqltools_mcp/，再到项目根目录的 assets/
    # adapters -> sqltools_mcp -> src -> sqltools-mcp -> assets
    possible_paths = [
        # 从 adapters 目录向上找到项目根目录的 assets
        os.path.join(script_dir, "..", "..", "..", "assets", "DmJdbcDriver18.jar"),
        # 从 site-packages 安装位置查找
        os.path.join(script_dir, "..", "assets", "DmJdbcDriver18.jar"),
        # Linux/macOS system locations
        "/opt/dmdbms/drivers/jdbc/DmJdbcDriver18.jar",
        os.path.expanduser("~/dmdbms/drivers/jdbc/DmJdbcDriver18.jar"),
        # Windows locations
        "C:\\dmdbms\\drivers\\jdbc\\DmJdbcDriver18.jar",
        os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'dmdbms', 'drivers', 'jdbc', 'DmJdbcDriver18.jar'),
    ]
    
    # Check environment variable
    dm_home = os.environ.get('DM_HOME')
    if dm_home:
        possible_paths.insert(0, os.path.join(dm_home, "drivers", "jdbc", "DmJdbcDriver18.jar"))
    
    # Also check environment variable for explicit driver path
    dm_driver = os.environ.get('DM_JDBC_DRIVER')
    if dm_driver:
        possible_paths.insert(0, dm_driver)
    
    for path in possible_paths:
        normalized_path = os.path.normpath(path)
        if os.path.exists(normalized_path):
            return normalized_path
    
    return None


class DM8Adapter(DatabaseAdapter):
    """DM8 (达梦) database adapter."""
    
    def __init__(self):
        super().__init__()
        if not JAYDEBEAPI_AVAILABLE:
            raise ImportError("jaydebeapi is not installed. Run: pip install jaydebeapi JPype1")
        self._jdbc_driver_path = None
    
    @property
    def db_type(self) -> str:
        return "dm8"
    
    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        dbname: str,
        **kwargs
    ) -> dict[str, Any]:
        """Connect to DM8 database."""
        try:
            self._jdbc_driver_path = find_dm_jdbc_driver()
            if not self._jdbc_driver_path:
                raise FileNotFoundError(
                    "DM8 JDBC driver (DmJdbcDriver18.jar) not found. "
                    "Please place it in the assets directory or set DM_HOME environment variable."
                )
            
            jdbc_url = f"jdbc:dm://{host}:{port}"
            if dbname:
                jdbc_url += f"/{dbname}"
            
            self._connection = jaydebeapi.connect(
                "dm.jdbc.driver.DmDriver",
                jdbc_url,
                [username, password],
                self._jdbc_driver_path
            )
            self._connected = True
            
            # Get server info
            cursor = self._connection.cursor()
            cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
            version_row = cursor.fetchone()
            version = version_row[0] if version_row else "Unknown"
            cursor.execute("SELECT USER FROM DUAL")
            current_user = cursor.fetchone()[0]
            cursor.close()
            
            return {
                "success": True,
                "server_version": version,
                "current_user": current_user,
                "host": host,
                "port": port,
                "driver": "jaydebeapi (JDBC)",
            }
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"DM8 connection failed: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from DM8 database."""
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
        except Exception as e:
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
            if schema:
                cursor.execute("""
                    SELECT TABLE_NAME, TABLE_TYPE
                    FROM ALL_TABLES
                    WHERE OWNER = ?
                    ORDER BY TABLE_NAME
                """, (schema.upper(),))
            else:
                cursor.execute("""
                    SELECT TABLE_NAME, 'TABLE' AS TABLE_TYPE
                    FROM USER_TABLES
                    ORDER BY TABLE_NAME
                """)
            
            tables = []
            for row in cursor.fetchall():
                tables.append(TableInfo(
                    name=row[0],
                    schema=schema,
                    table_type=row[1] if len(row) > 1 else "TABLE"
                ))
            
            cursor.close()
            return tables
        except Exception:
            return []
    
    def describe_table(self, table_name: str, schema: str | None = None) -> list[ColumnInfo]:
        """Get table structure."""
        if not self._connected:
            return []
        
        try:
            cursor = self._connection.cursor()
            if schema:
                cursor.execute("""
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.NULLABLE,
                        CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'Y' ELSE 'N' END AS IS_PK,
                        c.DATA_DEFAULT
                    FROM ALL_TAB_COLUMNS c
                    LEFT JOIN (
                        SELECT cols.COLUMN_NAME
                        FROM ALL_CONSTRAINTS cons
                        JOIN ALL_CONS_COLUMNS cols ON cons.CONSTRAINT_NAME = cols.CONSTRAINT_NAME
                        WHERE cons.CONSTRAINT_TYPE = 'P'
                        AND cons.OWNER = ?
                        AND cons.TABLE_NAME = ?
                    ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                    WHERE c.OWNER = ? AND c.TABLE_NAME = ?
                    ORDER BY c.COLUMN_ID
                """, (schema.upper(), table_name.upper(), schema.upper(), table_name.upper()))
            else:
                cursor.execute("""
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.NULLABLE,
                        CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'Y' ELSE 'N' END AS IS_PK,
                        c.DATA_DEFAULT
                    FROM USER_TAB_COLUMNS c
                    LEFT JOIN (
                        SELECT cols.COLUMN_NAME
                        FROM USER_CONSTRAINTS cons
                        JOIN USER_CONS_COLUMNS cols ON cons.CONSTRAINT_NAME = cols.CONSTRAINT_NAME
                        WHERE cons.CONSTRAINT_TYPE = 'P'
                        AND cons.TABLE_NAME = ?
                    ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                    WHERE c.TABLE_NAME = ?
                    ORDER BY c.COLUMN_ID
                """, (table_name.upper(), table_name.upper()))
            
            columns = []
            for row in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == 'Y',
                    is_primary_key=row[3] == 'Y',
                    default_value=row[4]
                ))
            
            cursor.close()
            return columns
        except Exception:
            return []
