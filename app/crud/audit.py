import json
from ..db.connection import Database
from ..models.audit import AuditLog
from ..models.enums import OperationType

from typing import Optional, List


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
        from datetime import datetime

        def serialize_datetimes(obj):
            if isinstance(obj, dict):
                return {k: serialize_datetimes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetimes(i) for i in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj

        # Process datetime objects
        old_data_serialized = serialize_datetimes(
            old_data) if old_data else None
        new_data_serialized = serialize_datetimes(
            new_data) if new_data else None

        # Create audit log entry
        audit_log = AuditLog(
            table_name=table_name,
            record_id=record_id,
            operation=operation.value,
            old_data=json.dumps(
                old_data_serialized) if old_data_serialized else None,
            new_data=json.dumps(
                new_data_serialized) if new_data_serialized else None
        )

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

    def get_audit_logs(self, table_name: Optional[str] = None, operation: Optional[str] = None, limit: int = 100) -> List[AuditLog]:
        where_clauses = []
        if table_name:
            where_clauses.append(f"table_name = '{table_name}'")
        if operation:
            where_clauses.append(f"operation = '{operation}'")
        where_stmt = " AND ".join(where_clauses) if where_clauses else None
        logs = self.db.select_data(
            table_name="audit_log",
            columns=[
                "log_id", "table_name", "record_id", "operation",
                "old_data", "new_data", "operated_at"
            ],
            where=where_stmt,
            order_by="operated_at DESC",
            limit=limit
        )
        return [
            AuditLog(
                log_id=row[0],
                table_name=row[1],
                record_id=row[2],
                operation=row[3],
                old_data=row[4],
                new_data=row[5],
                operated_at=row[6]
            )
            for row in logs
        ] if logs else []

    def rollback_most_recent(self, db) -> str:
        """
        Rollback the most recent operation (the one with max(operated_at) or max(audit_log_id)).
        Returns a message if rollback succeeded, raises otherwise.
        """
        logs = self.db.select_data(
            table_name="audit_log",
            columns=["log_id", "table_name", "record_id",
                     "operation", "old_data", "new_data", "operated_at"],
            order_by="operated_at DESC",
            limit=1
        )
        if not logs:
            raise Exception("No audit logs found.")

        r = logs[0]
        table_name = r[1]
        record_id = r[2]
        op = r[3]
        import json
        old_data = json.loads(r[4]) if r[4] else None
        new_data = json.loads(r[5]) if r[5] else None
        pk_field = f"{table_name}_id"

        if op == "UPDATE" or (hasattr(op, "value") and op.value == "UPDATE"):
            if not old_data:
                raise Exception("No old_data for rollback (update case).")
            db.update_data(table_name=table_name, data=old_data,
                           where=f"{pk_field} = {record_id}")
            return f"Rolled back last UPDATE for {table_name}({record_id})."
        elif op == "DELETE" or (hasattr(op, "value") and op.value == "DELETE"):
            if not old_data:
                raise Exception("No old_data for rollback (delete case).")
            db.insert_data(table_name=table_name, data=old_data)
            return f"Rolled back last DELETE: reinserted {table_name}({record_id})."
        elif op == "INSERT" or (hasattr(op, "value") and op.value == "INSERT"):
            db.delete_data(table_name=table_name,
                           where=f"{pk_field} = {record_id}")
            return f"Rolled back last INSERT: deleted {table_name}({record_id})."
        else:
            raise Exception(f"Unknown operation type: {op}")
