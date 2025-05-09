# services/repair_assignment_service.py
from db.connection import Database
from models.repair import RepairAssignment
from models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any


class RepairAssignmentService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_assignment(self, order_id: int, staff_id: int, time_worked: Optional[float] = None) -> RepairAssignment:
        """
        Create a new repair assignment.
        Args:
            order_id (int): ID of the repair order.
            staff_id (int): ID of the staff member.
            time_worked (Optional[float]): Time worked on the assignment.
        Returns:
            RepairAssignment: The created repair assignment.
        """
        assignment = RepairAssignment(
            order_id=order_id,
            staff_id=staff_id,
            time_worked=time_worked
        )
        insert_query = """
            INSERT INTO repair_assignment (order_id, staff_id, time_worked)
            VALUES (?, ?, ?)
        """
        self.db.execute_non_query(
            insert_query,
            (assignment.order_id, assignment.staff_id, assignment.time_worked)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        assignment_id_row = self.db.execute_query(select_id_query)
        assignment.assignment_id = int(
            assignment_id_row[0][0]) if assignment_id_row else None
        self.audit_log_service.log_audit_event(
            table_name="repair_assignment",
            record_id=assignment.assignment_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(assignment)
        )
        return assignment

    def get_repair_assignment_by_id(self, order_id: int, staff_id: int) -> Optional[RepairAssignment]:
        """
        Get a repair assignment by order ID and staff ID.
        Args:
            order_id (int): ID of the repair order.
            staff_id (int): ID of the staff member.
        Returns:
            Optional[RepairAssignment]: RepairAssignment object if found, otherwise None.
        """
        select_query = """
            SELECT assignment_id, order_id, staff_id, time_worked
            FROM repair_assignment
            WHERE order_id = ? AND staff_id = ?
        """
        rows = self.db.execute_query(select_query, (order_id, staff_id))
        if rows:
            return RepairAssignment(
                assignment_id=rows[0][0],
                order_id=rows[0][1],
                staff_id=rows[0][2],
                time_worked=rows[0][3] if rows[0][3] else None
            )
        return None

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
