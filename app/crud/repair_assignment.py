from ..db.connection import Database
from ..models.repair import RepairAssignment
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any
from datetime import datetime


class RepairAssignmentService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_assignment(
        self,
        order_id: int,
        staff_id: int,
        time_worked: Optional[float] = None
    ) -> RepairAssignment:
        """
        Create a new repair assignment.
        """
        assignment = RepairAssignment(
            order_id=order_id,
            staff_id=staff_id,
            time_worked=time_worked
        )

        # 使用 insert_data 统一插入
        self.db.insert_data(
            table_name="repair_assignment",
            data={
                "order_id":    assignment.order_id,
                "staff_id":    assignment.staff_id,
                "time_worked": assignment.time_worked
            }
        )

        # 获取自增主键
        row = self.db.execute_query("SELECT LAST_INSERT_ID()")
        assignment.assignment_id = int(row[0][0]) if row else None

        # 审计日志
        self.audit_log_service.log_audit_event(
            table_name="repair_assignment",
            record_id=assignment.assignment_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(assignment)
        )
        return assignment

    def get_repair_assignment_by_id(
        self,
        order_id: int,
        staff_id: int
    ) -> Optional[RepairAssignment]:
        """
        Get a repair assignment by composite key (order_id, staff_id).
        """
        rows = self.db.select_data(
            table_name="repair_assignment",
            columns=["assignment_id", "order_id", "staff_id", "time_worked"],
            where="order_id = ? AND staff_id = ?",
            where_params=(order_id, staff_id)
        )
        if not rows:
            return None

        r = rows[0]
        return RepairAssignment(
            assignment_id=r[0],
            order_id=r[1],
            staff_id=r[2],
            time_worked=r[3]
        )

    def update_repair_assignment_time(
        self,
        assignment_id: int,
        time_worked: float
    ) -> Optional[RepairAssignment]:
        """
        Update time_worked for a repair assignment.
        """
        # 先取旧值
        rows = self.db.select_data(
            table_name="repair_assignment",
            columns=["assignment_id", "order_id", "staff_id", "time_worked"],
            where="assignment_id = ?",
            where_params=(assignment_id,)
        )
        if not rows:
            return None
        old_row = rows[0]
        old = {
            "assignment_id": old_row[0],
            "order_id":      old_row[1],
            "staff_id":      old_row[2],
            "time_worked":   old_row[3]
        }

        # 更新
        self.db.update_data(
            table_name="repair_assignment",
            data={"time_worked": time_worked},
            where="assignment_id = ?",
            where_params=(assignment_id,)
        )

        # 构造新的对象
        updated = RepairAssignment(
            assignment_id=assignment_id,
            order_id=old_row[1],
            staff_id=old_row[2],
            time_worked=time_worked
        )

        self.audit_log_service.log_audit_event(
            table_name="repair_assignment",
            record_id=assignment_id,
            operation=OperationType.UPDATE,
            old_data=old,
            new_data=self._object_to_dict(updated)
        )
        return updated

    def delete_repair_assignment(self, assignment_id: int) -> bool:
        """
        Delete a repair assignment by its ID.
        Returns True if a row was deleted.
        """
        # 先获取旧数据用于审计
        rows = self.db.select_data(
            table_name="repair_assignment",
            columns=["assignment_id", "order_id", "staff_id", "time_worked"],
            where="assignment_id = ?",
            where_params=(assignment_id,)
        )
        if not rows:
            return False
        old_row = rows[0]
        old = {
            "assignment_id": old_row[0],
            "order_id":      old_row[1],
            "staff_id":      old_row[2],
            "time_worked":   old_row[3]
        }

        # 删除
        deleted = self.db.delete_data(
            table_name="repair_assignment",
            where="assignment_id = ?",
            where_params=(assignment_id,)
        )
        if deleted:
            self.audit_log_service.log_audit_event(
                table_name="repair_assignment",
                record_id=assignment_id,
                operation=OperationType.DELETE,
                old_data=old
            )
            return True
        return False

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {
            k: v
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }
