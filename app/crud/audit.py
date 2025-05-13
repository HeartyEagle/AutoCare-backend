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
        
        from datetime import datetime

        # Get the current date and time in the format SQL expects
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        # Prepare the audit log data dictionary
        audit_log_dict = audit_log.asdict()

        # Make sure 'operated_at' is set correctly
        audit_log_dict["operated_at"] = formatted_datetime
        print(audit_log_dict)
        
        # Insert the audit log into the database
        self.db.insert_data(table_name="audit_log", data=audit_log_dict)
        
