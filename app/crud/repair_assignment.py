from ..db.connection import Database
from ..models.repair import RepairAssignment
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class RepairAssignmentService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_assignment(
        self,
        order_id: int,
        staff_id: int,
        status: str,
        time_worked: Optional[float] = None
    ) -> RepairAssignment:
        """
        Create a new repair assignment.
        """
        assignment = RepairAssignment(
            order_id=order_id,
            staff_id=staff_id,
            status=status,
            time_worked=time_worked
        )

        # 使用 insert_data 统一插入
        self.db.insert_data(
            table_name="repair_assignment",
            data={
                "order_id":    assignment.order_id,
                "staff_id":    assignment.staff_id,
                "status":      assignment.status,
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

    def update_assignment_status(self, assignment_id: int, staff_id: int, new_status: str) -> Optional[RepairAssignment]:
        """
        Update the status of an assignment (accept or reject).
        If rejected, trigger reassignment.
        Args:
            assignment_id: ID of the assignment to update.
            staff_id: ID of the staff member responding to the assignment.
            new_status: New status ("accepted" or "rejected").
        Returns:
            Updated RepairAssignment object or None if update fails.
        """
        # Validate assignment exists and belongs to the staff
        assignment = self.get_repair_assignment_by_id(assignment_id)
        if not assignment or assignment.staff_id != staff_id:
            return None

        if assignment.status != "pending":
            return None  # Cannot update if not pending

        if new_status not in ["accepted", "rejected"]:
            return None  # Invalid status

        # Update the status in the database
        self.db.update_data(
            table_name="repair_assignment",
            data={"status": new_status},
            where=f"assignment_id = {assignment_id}"
        )

        assignment.status = new_status

        # Log the action
        self.audit_log_service.log_audit_event(
            table_name="repair_assignment",
            record_id=assignment_id,
            operation=OperationType.UPDATE,
            old_data={"status": "pending"},
            new_data={"status": new_status}
        )

        # # If rejected, trigger reassignment
        # if new_status == "rejected":
        #     new_assignment = self.reassign_order(
        #         assignment.order_id, exclude_staff_id=staff_id)
        #     if new_assignment:
        #         self.audit_log_service.log_audit_event(
        #             table_name="repair_assignment",
        #             record_id=new_assignment.assignment_id,
        #             operation=OperationType.INSERT,
        #             new_data=self._object_to_dict(new_assignment)
        #         )

        return assignment

    def get_eligible_staff(self, required_staff_type: str, exclude_staff_id: Optional[int] = None) -> List[Any]:
        """
        Retrieve a list of eligible staff members for a given staff type, optionally excluding a specific staff.

        Args:
            required_staff_type (str): The type of staff required for the repair order (e.g., 'mechanic', 'technician').
            exclude_staff_id (Optional[int]): ID of a staff member to exclude from the list (e.g., for reassignment).

        Returns:
            List[Any]: A list of staff objects or dictionaries representing eligible staff members.

        Raises:
            RuntimeError: If there is an error fetching staff data from the database.
        """
        try:
            # Build the WHERE clause for the database query
            where_clause = f"jobtype = '{required_staff_type}'"
            if exclude_staff_id is not None:
                where_clause += f" AND staff_id != {exclude_staff_id}"

            # Query the database for eligible staff
            # Adjust column names and table name based on your schema
            staff_rows = self.db.select_data(
                table_name="staff",
                columns=["staff_id", "jobtype", "hourly_rate"],
                where=where_clause
            )

            if not staff_rows:
                return []

            # Convert rows to a list of staff objects or dictionaries
            # Assuming staff_rows is a list of tuples with (staff_id, name, job_type, is_available)
            eligible_staff = [
                {
                    "staff_id": row[0],
                    "jobtype": row[1],
                    "hourly_rate": row[2]
                }
                for row in staff_rows
            ]

            return eligible_staff

        except Exception as e:
            raise RuntimeError(f"Error fetching eligible staff: {str(e)}")

    def get_repair_assignment_by_id(
        self,
        assignment_id: int
    ) -> Optional[RepairAssignment]:
        """
        Get a repair assignment by composite key (order_id, staff_id).
        """
        rows = self.db.select_data(
            table_name="repair_assignment",
            columns=["assignment_id", "order_id",
                     "staff_id", "status", "time_worked"],
            where=f"assignment_id = {assignment_id}",
        )
        if not rows:
            return None

        r = rows[0]
        return RepairAssignment(
            assignment_id=r[0],
            order_id=r[1],
            staff_id=r[2],
            status=r[3] if r[3] else "pending",
            time_worked=r[4] if r[4] else None
        )

    def get_assignments_by_staff_id(self, staff_id: int) -> List[RepairAssignment]:
        """
        Get all repair assignments for a specific staff member.

        Args:
            staff_id (int): ID of the staff member whose assignments to retrieve.

        Returns:
            List[RepairAssignment]: List of repair assignment objects for the staff member.
        """
        rows = self.db.select_data(
            table_name="repair_assignment",
            columns=["assignment_id", "order_id",
                     "staff_id", "status", "time_worked"],
            where=f"staff_id = {staff_id}"
        )
        return [
            RepairAssignment(
                assignment_id=row[0],
                order_id=row[1],
                staff_id=row[2],
                status=row[3] if row[3] else "pending",
                time_worked=row[4] if row[4] else None
            )
            for row in rows
        ] if rows else []

    def get_assignments_by_order_id(self, order_id: int) -> List[RepairAssignment]:
        """
        Get all repair assignments for a specific repair order.

        Args:
            order_id (int): ID of the repair order whose assignments to retrieve.

        Returns:
            List[RepairAssignment]: List of repair assignment objects for the repair order.
        """
        rows = self.db.select_data(
            table_name="repair_assignment",
            columns=["assignment_id", "order_id",
                     "staff_id", "status", "time_worked"],
            where=f"order_id = {order_id}"
        )
        return [
            RepairAssignment(
                assignment_id=row[0],
                order_id=row[1],
                staff_id=row[2],
                status=row[3] if row[3] else "pending",
                time_worked=row[4] if row[4] else None
            )
            for row in rows
        ] if rows else []

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
            columns=["assignment_id", "order_id",
                     "staff_id", "status", "time_worked"],
            where=f"assignment_id = {assignment_id}",
        )
        if not rows:
            return None
        old_row = rows[0]
        old = {
            "assignment_id": old_row[0],
            "order_id":      old_row[1],
            "staff_id":      old_row[2],
            "status":        old_row[3],
            "time_worked":   old_row[4]
        }

        # 更新
        self.db.update_data(
            table_name="repair_assignment",
            data={"time_worked": time_worked},
            where=f"assignment_id = {assignment_id}",
        )

        # 构造新的对象
        updated = RepairAssignment(
            assignment_id=assignment_id,
            order_id=old_row[1],
            staff_id=old_row[2],
            status=old_row[3],
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
            columns=["assignment_id", "order_id",
                     "staff_id", "status", "time_worked"],
            where=f"assignment_id = {assignment_id}",
        )
        if not rows:
            return False
        old_row = rows[0]
        old = {
            "assignment_id": old_row[0],
            "order_id":      old_row[1],
            "staff_id":      old_row[2],
            "status":        old_row[3],
            "time_worked":   old_row[4]
        }

        # 删除
        deleted = self.db.delete_data(
            table_name="repair_assignment",
            where=f"assignment_id = {assignment_id}",
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
