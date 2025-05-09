import pyodbc
from contextlib import contextmanager


class Database:
    def __init__(self):
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
        if not self.conn:
            self.conn = pyodbc.connect(self.conn_str)
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    @contextmanager
    def get_cursor(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
