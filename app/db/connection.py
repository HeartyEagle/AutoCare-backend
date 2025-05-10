import pyodbc
from contextlib import contextmanager
from typing import Tuple, List, Any
import logging

# Set up logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        """
        Initialize the Database class with connection string for MySQL using pyodbc.
        """
        self.conn_str = (
            "DRIVER={MySQL ODBC 9.2 ANSI Driver};"
            "SERVER=localhost;"
            "PORT=3308;"
            "DATABASE=autocare_db;"
            "UID=macrohard;"
            "PWD=M@cr0h@rd!2025$;"
        )
        self.conn = None

    def connect(self):
        """
        Establish a connection to the database if not already connected.
        Returns:
            pyodbc.Connection: The database connection object.
        Raises:
            Exception: If connection fails.
        """
        if not self.conn:
            try:
                self.conn = pyodbc.connect(self.conn_str)
                logger.info("Database connection established.")
            except pyodbc.Error as e:
                logger.error(f"Failed to connect to database: {str(e)}")
                raise Exception(f"Database connection failed: {str(e)}")
        return self.conn

    def close(self):
        """
        Close the database connection if it exists.
        """
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed.")
            except pyodbc.Error as e:
                logger.error(f"Error closing database connection: {str(e)}")
            finally:
                self.conn = None

    @contextmanager
    def get_cursor(self):
        """
        Context manager to provide a cursor for database operations.
        Automatically closes the cursor when done.
        Yields:
            pyodbc.Cursor: The database cursor object.
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        except pyodbc.Error as e:
            logger.error(f"Cursor operation failed: {str(e)}")
            raise
        finally:
            cursor.close()

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
