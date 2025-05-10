# services/repair_log_service.py
from ..db.connection import Database
from ..models.repair import RepairLog
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List


class RepairLogService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_log(self, order_id: int, staff_id: int, log_message: str) -> RepairLog:
        """
        Create a new repair log.
        Args:
            order_id (int): ID of the repair order.
            staff_id (int): ID of the staff member.
            log_message (str): Description of the repair log.
        Returns:
            RepairLog: The created repair log.
        """
        repair_log = RepairLog(
            order_id=order_id,
            staff_id=staff_id,
            log_message=log_message
        )
        insert_query = """
            INSERT INTO repair_log (order_id, staff_id, log_time, log_message)
            VALUES (?, ?, GETDATE(), ?)
        """
        self.db.execute_non_query(
            insert_query,
            (repair_log.order_id, repair_log.staff_id, repair_log.log_message)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        log_id_row = self.db.execute_query(select_id_query)
        repair_log.log_id = int(log_id_row[0][0]) if log_id_row else None
        self.audit_log_service.log_audit_event(
            table_name="repair_log",
            record_id=repair_log.log_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(repair_log)
        )
        return repair_log

    def get_repair_log_by_id(self, log_id: int) -> Optional[RepairLog]:
        """
        Get a repair log by ID.
        Args:
            log_id (int): ID of the repair log.
        Returns:
            Optional[RepairLog]: RepairLog object if found, otherwise None.
        """
        select_query = """
            SELECT log_id, order_id, staff_id, log_time, log_message
            FROM repair_log
            WHERE log_id = ?
        """
        rows = self.db.execute_query(select_query, (log_id,))
        if rows:
            return RepairLog(
                log_id=rows[0][0],
                order_id=rows[0][1],
                staff_id=rows[0][2],
                log_time=rows[0][3] if rows[0][3] else None,
                log_message=rows[0][4]
            )
        return None

    def get_repair_logs_by_order_id(self, order_id: int) -> List[RepairLog]:
        """
        Get all repair logs associated with a specific repair order.
        Args:
            order_id (int): ID of the repair order.
        Returns:
            List[RepairLog]: List of RepairLog objects associated with the order.
        """
        select_query = """
            SELECT log_id, order_id, staff_id, log_time, log_message
            FROM repair_log
            WHERE order_id = ?
        """
        rows = self.db.execute_query(select_query, (order_id,))
        return [RepairLog(
            log_id=row[0],
            order_id=row[1],
            staff_id=row[2],
            log_time=row[3] if row[3] else None,
            log_message=row[4]
        ) for row in rows] if rows else []

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
