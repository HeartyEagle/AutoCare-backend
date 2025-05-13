import pyodbc
from contextlib import contextmanager
from typing import Tuple, List, Any
import logging

# Set up logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    server: str = None
    database: str = None
    port: int = None
    username: str = None
    password: str = None
    driver: str = None
    conn: pyodbc.Connection = None
    driver_initialized: bool = False
    database_connected: bool = False
    
    driver_not_initialized = Exception("Driver not initialized.")
    database_not_connected = Exception("Database not connected.")
    
    def __init__(self, server: str, database: str, port: int, username: str, password: str) -> None:
        self.server   = server
        self.database = database
        self.port     = port
        self.username = username 
        self.password = password
        
    def _normalize_string(self, value: Any) -> Any:
        """
        检测并规范化字符串，移除宽字符中的 \x00 字节。
        Args:
            value: 输入值，可能是字符串或其他类型。
        Returns:
            规范化后的值（如果是字符串，则移除 \x00；其他类型保持不变）。
        """
        if isinstance(value, str) and '\x00' in value:
            normalized = value.replace('\x00', '')
            logger.debug(f"Normalized string: {value!r} -> {normalized!r}")
            return normalized
        return value
        
    def set_driver(self, driver: str) -> None:
        self.driver             = driver
        self.driver_initialized = True
        self.database_connected = False
        
    def connect(self) -> None:
        conn_str = f'''
        DRIVER={{{self.driver}}};SERVER={self.server};PORT={self.port};DATABASE={self.database};UID={self.username};PWD={self.password};CHARSET=utf8mb4;OPTION=3
        '''
        try:
            self.conn               = pyodbc.connect(conn_str)
            self.database_connected = True
        except Exception as e:
            raise Exception("Connection failed!", e)
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
        self.database_connected = False
        
    def _validation(self) -> None:
        if not self.driver_initialized:
            raise self.driver_not_initialized
        if not self.database_connected:
            raise self.database_not_connected
        
    def get_version(self) -> str:
        self._validation()
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            record = cursor.fetchone()
        return record[0]
    
    def create_table(
        self,
        table_name: str,
        columns: dict,
        foreign_keys: list = None,
        primary_key: list = None,
        if_not_exists: bool = True
    ) -> None:
        self._validation()
        column_defs = [f"{col} {dtype}" for col, dtype in columns.items()]
        
        if primary_key:
            pk = ", ".join(primary_key)
            column_defs.append(f"PRIMARY KEY ({pk})")
        
        if foreign_keys:
            column_defs.extend(foreign_keys)
        
        col_sql = ",\n  ".join(column_defs)
        query = f"CREATE TABLE {'IF NOT EXISTS ' if if_not_exists else ''}{table_name} (\n  {col_sql}\n);"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                self.conn.commit()
        except Exception as e:
            raise Exception(f"Table creation failed: {e}\nQuery: {query}")

    def insert_data(
        self,
        table_name: str,
        data: list[dict] | dict,
        on_duplicate_update: bool = False,
        ignore_conflict: bool = False,
    ) -> None:
        self._validation()

        data = {key: data[key] for key in data.keys() if data[key] is not None}
        if isinstance(data, dict):
            data = [data]
        if not data:
            return

        columns = list(data[0].keys())
        column_names = ", ".join(columns)

        values_list = []
        for row in data:
            values = [self._format_value(row[col]) for col in columns]
            values_list.append(f"({', '.join(values)})")
        values_sql = ", ".join(values_list)

        if on_duplicate_update:
            update_clause = ", ".join([f"{col}=VALUES({col})" for col in columns])
            query = f"INSERT INTO {table_name} ({column_names}) VALUES {values_sql} ON DUPLICATE KEY UPDATE {update_clause}"
        elif ignore_conflict:
            query = f"INSERT IGNORE INTO {table_name} ({column_names}) VALUES {values_sql}"
        else:
            query = f"INSERT INTO {table_name} ({column_names}) VALUES {values_sql}"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Data insertion failed: {e}\nQuery: {query}")

    def select_data(
        self,
        table_name: str,
        columns: list = None,
        where: str = None,
        where_params: tuple = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
        distinct: bool = False,
        group_by: str = None,
        having: str = None,
        joins: list[str] = None,
        as_dict: bool = False
    ):
        from contextlib import closing
        self._validation()
        columns_sql = ", ".join(columns) if columns else "*"
        select_clause = f"SELECT {'DISTINCT ' if distinct else ''}{columns_sql}"
        query = f"{select_clause} FROM {table_name}"
        
        print(where, where_params)

        if joins:
            for join in joins:
                query += f" {join}"
        if where and where_params:
            query += f" WHERE {self._format_where_clause(where, where_params)}"
        elif where:
            query += f" WHERE {where}"
        if group_by:
            query += f" GROUP BY {group_by}"
        if having:
            query += f" HAVING {having}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit is not None:
            query += f" LIMIT {limit}" + (f" OFFSET {offset}" if offset is not None else "")

        print(f"Executing query: {query}")  # Debug
        try:
            # 每次使用新的游标，并确保关闭
            with closing(self.conn.cursor()) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

            normalized = []
            for row in results:
                if as_dict:
                    # 如果 as_dict，需要转换字典形式，可根据需要自行实现
                    normalized.append({k: self._normalize_string(v) for k, v in row.items()})
                else:
                    normalized.append(tuple(self._normalize_string(v) for v in row))
            return normalized
        except Exception as e:
            raise Exception(f"Data selection failed: {e}Query: {query}")

    def drop_table(
        self,
        table_names: str | list,
        if_exists: bool = True,
        cascade: bool = False,
        dry_run: bool = False,
        confirm: bool = True
    ) -> None:
        self._validation()
        names = [table_names] if isinstance(table_names, str) else table_names
        for name in names:
            query = f"DROP TABLE {'IF EXISTS ' if if_exists else ''}{name}" + (" CASCADE" if cascade else "")
            if dry_run:
                print(f"[DRY RUN] Would execute: {query}")
                continue
            if confirm:
                ans = input(f"⚠️ Drop table '{name}'? Type 'yes' to confirm: ")
                if ans.lower() != 'yes':
                    print(f"Skipping {name}")
                    continue
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(query)
                    self.conn.commit()
                print(f"Dropped table: {name}")
            except Exception as e:
                raise Exception(f"Failed to drop table {name}: {e}")

    def update_data(
        self,
        table_name: str,
        data: dict[str, Any],
        where: str,
        where_params: Tuple[Any, ...] = ()
    ) -> int:
        self._validation()
        cols = data.keys()
        set_clause = ", ".join(f"{c} = " + self._format_value(data[c]) for c in cols)
        where_clause = self._format_where_clause(where, where_params) if where_params else where
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                affected = cursor.rowcount
                self.conn.commit()
            logger.info(f"UPDATE 成功: {query}, affected={affected}")
            return affected
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Update failed: {e}\nQuery: {query}")

    def delete_data(
        self,
        table_name: str,
        where: str,
        where_params: Tuple[Any, ...] = ()
    ) -> int:
        self._validation()
        where_clause = self._format_where_clause(where, where_params) if where_params else where
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                affected = cursor.rowcount
                self.conn.commit()
            logger.info(f"DELETE 成功: {query}, affected={affected}")
            return affected
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Delete failed: {e}\nQuery: {query}")

    def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        self._validation()
        formatted = self._format_query(query, params) if params else query
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(formatted)
                if formatted.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                else:
                    self.conn.commit()
                    return []
        except pyodbc.Error as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}\nQuery: {formatted}")
            raise

    def execute_non_query(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        self._validation()
        formatted = self._format_query(query, params) if params else query
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(formatted)
                self.conn.commit()
            logger.info(f"Non-query executed successfully: {formatted}")
        except pyodbc.Error as e:
            self.conn.rollback()
            logger.error(f"Non-query execution failed: {e}\nQuery: {formatted}")
            raise

    def init_db(self):
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            self.execute_query(create_users_table)
            logger.info("Database schema initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

    def _format_value(self, value: Any) -> str:
        if isinstance(value, str):
            return f"'{value}'"
        return "NULL" if value is None else str(value)

    def _format_where_clause(self, where: str, params: Tuple[Any, ...]) -> str:
        parts = where.split("?")
        if len(parts) != len(params) + 1:
            raise ValueError("Number of placeholders does not match number of parameters.")
        return ''.join(p + (f"'{v}'" if isinstance(v, str) else "NULL" if v is None else str(v)) for p, v in zip(parts, params + ('',)))

    def _format_query(self, query: str, params: Tuple[Any, ...]) -> str:
        return self._format_where_clause(query, params)
