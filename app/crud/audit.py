import json
from ..db.connection import Database
from ..models.audit import AuditLog
from ..models.enums import OperationType


class AuditLogService:
    def __init__(self, db: Database):
        self.db = db

    def log_audit_event(self, table_name: str, record_id: int, operation: OperationType, old_data: dict = None, new_data: dict = None):
        """
        Log an audit event for a database operation.
        Args:
            table_name (str): Name of the table affected.
            record_id (int): ID of the record affected.
            operation (OperationType): Type of operation (INSERT, UPDATE, DELETE).
            old_data (dict, optional): Data before the operation.
            new_data (dict, optional): Data after the operation.
        """
        audit_log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            old_data=json.dumps(old_data) if old_data else None,
            new_data=json.dumps(new_data) if new_data else None
        )
        # SQL query to insert audit log
        insert_query = """
            INSERT INTO audit_log (table_name, record_id, operation, old_data, new_data, operated_at)
            VALUES (?, ?, ?, ?, ?, GETDATE())
        """
        self.db.execute_non_query(
            insert_query,
            (audit_log.table_name, audit_log.record_id, audit_log.operation.value,
             audit_log.old_data, audit_log.new_data)
        )
        
