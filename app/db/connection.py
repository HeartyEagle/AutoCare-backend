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
    cursor: pyodbc.Cursor = None
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
        
    def set_driver(self, driver: str) -> None:
        self.driver             = driver
        self.database_connected = False
        
    def connect(self) -> None:
        conn_str = f'''
        DRIVER={{{self.driver}}};SERVER={self.server};PORT={self.port};DATABASE={self.database};UID={self.username};PWD={self.password};CHARSET=utf8mb4;OPTION=3
        '''
        try:
            conn                    = pyodbc.connect(conn_str)
            cursor                  = conn.cursor()
            self.cursor             = cursor
            self.database_connected = True
            self.conn               = conn
        except Exception as e:
            raise Exception("Connection failed!", e)
    
    def close(self) -> None:
        self.conn.close()
        self.database_connected = False
        
    def _validation(self) -> bool:
        if not self.driver_initialized:
            raise self.driver_not_initialized
        if not self.database_connected:
            raise self.database_not_connected
        
    def get_version(self) -> str:
        self._validation()
        self.cursor.execute("SELECT VERSION();")
        records = self.cursor.fetchall()
        return records[0][0]
    
    def create_table(
        self,
        table_name: str,
        columns: dict,
        foreign_keys: list = None,
        primary_key: list = None,
        if_not_exists: bool = True
    ) -> None:
        column_defs = [f"{col} {dtype}" for col, dtype in columns.items()]
        
        if primary_key:
            pk = ", ".join(primary_key)
            column_defs.append(f"PRIMARY KEY ({pk})")
        
        if foreign_keys:
            column_defs.extend(foreign_keys)
        
        col_sql = ",\n  ".join(column_defs)
        query = f"CREATE TABLE {'IF NOT EXISTS ' if if_not_exists else ''}{table_name} (\n  {col_sql}\n);"

        try:
            self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            raise Exception(f"Table creation failed: {e}\nQuery: {query}")

    def insert_data(
        self,
        table_name: str,
        data: list[dict] | dict,
        on_duplicate_update: bool = False,
        ignore_conflict: bool = True,
    ) -> None:
        
        self._validation()

        if isinstance(data, dict):
            data = [data]

        if not data:
            return

        columns = list(data[0].keys())
        placeholders = ", ".join(["%s"] * len(columns))
        column_names = ", ".join(columns)

        if on_duplicate_update:
            update_clause = ", ".join([f"{col}=VALUES({col})" for col in columns])
            query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"
        elif ignore_conflict:
            query = f"INSERT IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})"
        else:
            query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

        try:
            values = [tuple(row[col] for col in columns) for row in data]
            self.cursor.executemany(query, values)
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

        self._validation()

        columns_sql = ", ".join(columns) if columns else "*"
        select_clause = f"SELECT {'DISTINCT ' if distinct else ''}{columns_sql}"
        query = f"{select_clause} FROM {table_name}"

        if joins:
            for join in joins:
                query += f" {join}"

        if where:
            query += f" WHERE {where}"

        if group_by:
            query += f" GROUP BY {group_by}"

        if having:
            query += f" HAVING {having}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit is not None:
            query += f" LIMIT {limit}"
            if offset is not None:
                query += f" OFFSET {offset}"

        try:
            if as_dict:
                import pymysql
                if isinstance(self.cursor, pymysql.cursors.Cursor):
                    self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

            self.cursor.execute(query, where_params or ())
            return self.cursor.fetchall()
        except Exception as e:
            raise Exception(f"Data selection failed: {e}\nQuery: {query}")

    def drop_table(
        self,
        table_names: str | list,
        if_exists: bool = True,
        cascade: bool = False,
        dry_run: bool = False,
        confirm: bool = True
    ) -> None:
        self._validation()

        if isinstance(table_names, str):
            table_names = [table_names]

        for table_name in table_names:
            query = f"DROP TABLE {'IF EXISTS ' if if_exists else ''}{table_name}"
            if cascade:
                query += " CASCADE"

            if dry_run:
                print(f"[DRY RUN] Would execute: {query}")
                continue

            if confirm:
                user_input = input(f"⚠️ Are you sure you want to drop table '{table_name}'? Type 'yes' to confirm: ")
                if user_input.lower() != "yes":
                    print(f"Skipping table '{table_name}'")
                    continue

            try:
                self.cursor.execute(query)
                self.conn.commit()
                print(f"Dropped table: {table_name}")
            except Exception as e:
                raise Exception(f"Failed to drop table {table_name}: {e}")
            
        def update_data(
            self,
            table_name: str,
            data: dict[str, Any],
            where: str,
            where_params: Tuple[Any, ...] = ()
        ) -> int:
            
            self._validation()

            columns = list(data.keys())
            set_clause = ", ".join(f"{col} = ?" for col in columns)

            params = tuple(data[col] for col in columns) + where_params

            query = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                affected = cursor.rowcount
                self.conn.commit()
            logger.info(f"UPDATE 成功: {query} -- params={params}, affected={affected}")
            return affected

        def delete_data(
            self,
            table_name: str,
            where: str,
            where_params: Tuple[Any, ...] = ()
        ) -> int:
            self._validation()

            query = f"DELETE FROM {table_name} WHERE {where}"
            with self.get_cursor() as cursor:
                cursor.execute(query, where_params)
                affected = cursor.rowcount
                self.conn.commit()
            logger.info(f"DELETE 成功: {query} -- params={where_params}, affected={affected}")
            return affected
 

    def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        """
        Execute a SQL query with optional parameters and return results.
        Args:
            query (str): The SQL query to execute.
            params (Tuple[Any, ...]): Parameters for the query to prevent SQL injection.
        Returns:
            List[Any]: List of rows for SELECT queries; empty list for other queries.
        Raises:
            Exception: If query execution fails.
        """
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                if query.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    return rows
                else:
                    self.conn.commit()
                    return []
            except pyodbc.Error as e:
                self.conn.rollback()
                logger.error(
                    f"Query execution failed: {str(e)}\nQuery: {query}\nParams: {params}")
                raise Exception(f"Query execution failed: {str(e)}")

    def execute_non_query(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        """
        Execute a SQL statement that does not return results (e.g., INSERT, UPDATE, DELETE).
        Args:
            query (str): The SQL statement to execute.
            params (Tuple[Any, ...]): Parameters for the statement to prevent SQL injection.
        Raises:
            Exception: If statement execution fails.
        """
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params)
                self.conn.commit()
                logger.info(f"Non-query executed successfully: {query}")
            except pyodbc.Error as e:
                self.conn.rollback()
                logger.error(
                    f"Non-query execution failed: {str(e)}\nQuery: {query}\nParams: {params}")
                raise Exception(f"Non-query execution failed: {str(e)}")

    def init_db(self):
        """
        Initialize the database by creating necessary tables if they don't exist.
        This method can be called during startup to ensure the schema is ready.
        Modify the table structure based on your application needs.
        """
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
            logger.error(f"Failed to initialize database schema: {str(e)}")
            raise
