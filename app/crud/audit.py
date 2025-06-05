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
            operation=operation,
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
                "audit_log_id", "table_name", "record_id", "operation",
                "old_data", "new_data", "operated_at"
            ],
            where=where_stmt,
            order_by="operated_at DESC",
            limit=limit
        )
        return [
            AuditLog(
                audit_log_id=row[0],
                table_name=row[1],
                record_id=row[2],
                operation=row[3],
                old_data=row[4],
                new_data=row[5],
                operated_at=row[6]
            )
            for row in logs
        ] if logs else []

    def rollback_last_operation(
        self,
        db: Database,
        table_name: str,
        record_id: int
    ) -> Optional[str]:
        """
        Rollback the last audit log operation for the given table/record_id.
        Returns a human message on success, raises on failure.
        """
        # Fetch the last audit log entry for this record
        logs = self.get_audit_logs(table_name=table_name, limit=100)
        for log in logs:
            if log.record_id == record_id:
                op = log.operation
                old_data = json.loads(log.old_data) if log.old_data else None
                new_data = json.loads(log.new_data) if log.new_data else None
                if op == "UPDATE" or (hasattr(op, "value") and op.value == "UPDATE"):
                    # Restore old_data via UPDATE
                    if not old_data:
                        raise Exception(
                            "No old_data for rollback (update case).")
                    db.update_data(table_name=table_name, data=old_data,
                                   where=f"{table_name}_id = {record_id}")
                    return "Rolled back last UPDATE to previous state."
                elif op == "DELETE" or (hasattr(op, "value") and op.value == "DELETE"):
                    # Restore old_data via INSERT
                    if not old_data:
                        raise Exception(
                            "No old_data for rollback (delete case).")
                    db.insert_data(table_name=table_name, data=old_data)
                    return "Rolled back last DELETE: record re-inserted."
                elif op == "INSERT" or (hasattr(op, "value") and op.value == "INSERT"):
                    # Remove the just-inserted record
                    db.delete_data(table_name=table_name,
                                   where=f"{table_name}_id = {record_id}")
                    return "Rolled back last INSERT: record deleted."
                else:
                    raise Exception(f"Unknown operation type: {op}")
        raise Exception("No audit log found for this record to rollback.")
