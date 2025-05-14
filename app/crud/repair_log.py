from ..db.connection import Database
from ..models.repair import RepairLog
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class RepairLogService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_log(self, order_id: int, staff_id: int, log_message: str) -> RepairLog:
        """
        Create a new repair log.
        """
        now = str(datetime.now())
        repair_log = RepairLog(
            order_id=order_id,
            staff_id=staff_id,
            log_time=now,
            log_message=log_message
        )

        # 使用 insert_data 统一插入
        self.db.insert_data(
            table_name="repair_log",
            data={
                "order_id": repair_log.order_id,
                "staff_id": repair_log.staff_id,
                "log_time":   repair_log.log_time,
                "log_message": repair_log.log_message,
            }
        )

        # 获取自增主键
        row = self.db.execute_query("SELECT LAST_INSERT_ID()")
        repair_log.log_id = int(row[0][0]) if row else None

        # 审计日志
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
        """
        rows = self.db.select_data(
            table_name="repair_log",
            columns=["log_id", "order_id", "staff_id", "log_time", "log_message"],
            where=f"log_id = {log_id}",
        )
        if not rows:
            return None

        r = rows[0]
        return RepairLog(
            log_id=r[0],
            order_id=r[1],
            staff_id=r[2],
            log_time=r[3],
            log_message=r[4]
        )

    def get_repair_logs_by_order_id(self, order_id: int) -> List[RepairLog]:
        """
        Get all repair logs associated with a specific repair order.
        """
        rows = self.db.select_data(
            table_name="repair_log",
            columns=["log_id", "order_id", "staff_id", "log_time", "log_message"],
            where=f"order_id = {order_id}",
            order_by="log_time ASC"
        )
        return [
            RepairLog(
                log_id=r[0],
                order_id=r[1],
                staff_id=r[2],
                log_time=r[3],
                log_message=r[4]
            )
            for r in rows
        ]

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        将 dataclass 对象转换为 dict，用于审计日志。
        """
        if not obj:
            return {}
        return {
            key: value
            for key, value in vars(obj).items()
            if not key.startswith("_")
        }
