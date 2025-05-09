# services/repair_order_service.py
from db.connection import Database
from models.repair import RepairOrder
from models.enums import RepairStatus, StaffJobType, OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any
from datetime import datetime


class RepairOrderService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_order(
            self, vehicle_id: int, customer_id: int, request_id: int,
            required_staff_type: StaffJobType, status: RepairStatus, remarks: Optional[str] = None
    ) -> RepairOrder:
        """
        Create a new repair order.
        Args:
            vehicle_id (int): ID of the vehicle.
            customer_id (int): ID of the customer.
            request_id (int): ID of the repair request.
            required_staff_type (StaffJobType): Required staff job type for the repair.
            status (RepairStatus): Status of the repair order.
            remarks (Optional[str]): Additional remarks.
        Returns:
            RepairOrder: The created repair order.
        """
        repair_order = RepairOrder(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            request_id=request_id,
            required_staff_type=required_staff_type,
            status=status,
            remarks=remarks
        )
        insert_query = """
            INSERT INTO repair_order (vehicle_id, customer_id, request_id, required_staff_type, status, order_time, remarks)
            VALUES (?, ?, ?, ?, ?, GETDATE(), ?)
        """
        self.db.execute_non_query(
            insert_query,
            (repair_order.vehicle_id, repair_order.customer_id, repair_order.request_id,
             repair_order.required_staff_type.value if repair_order.required_staff_type else None,
             repair_order.status.value if repair_order.status else None, repair_order.remarks)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        order_id_row = self.db.execute_query(select_id_query)
        repair_order.order_id = int(
            order_id_row[0][0]) if order_id_row else None
        self.audit_log_service.log_audit_event(
            table_name="repair_order",
            record_id=repair_order.order_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(repair_order)
        )
        return repair_order

    def get_repair_order_by_id(self, order_id: int) -> Optional[RepairOrder]:
        """
        Get a repair order by ID.
        Args:
            order_id (int): ID of the repair order.
        Returns:
            Optional[RepairOrder]: RepairOrder object if found, otherwise None.
        """
        select_query = """
            SELECT order_id, vehicle_id, customer_id, request_id, required_staff_type, status, order_time, finish_time, remarks
            FROM repair_order
            WHERE order_id = ?
        """
        rows = self.db.execute_query(select_query, (order_id,))
        if rows:
            return RepairOrder(
                order_id=rows[0][0],
                vehicle_id=rows[0][1],
                customer_id=rows[0][2],
                request_id=rows[0][3],
                required_staff_type=StaffJobType(
                    rows[0][4]) if rows[0][4] else None,
                status=RepairStatus(rows[0][5]) if rows[0][5] else None,
                order_time=rows[0][6] if rows[0][6] else None,
                finish_time=rows[0][7] if rows[0][7] else None,
                remarks=rows[0][8] if rows[0][8] else None
            )
        return None

    def update_repair_order_status(self, order_id: int, status: RepairStatus) -> Optional[RepairOrder]:
        """
        Update the status of a repair order.
        Args:
            order_id (int): ID of the repair order.
            status (RepairStatus): New status of the repair order.
        Returns:
            Optional[RepairOrder]: The updated repair order if found, otherwise None.
        """
        repair_order = self.get_repair_order_by_id(order_id)
        if repair_order:
            old_data = self._object_to_dict(repair_order)
            repair_order.status = status
            update_query = """
                UPDATE repair_order
                SET status = ?
                WHERE order_id = ?
            """
            self.db.execute_non_query(update_query, (status.value, order_id))
            self.audit_log_service.log_audit_event(
                table_name="repair_order",
                record_id=order_id,
                operation=OperationType.UPDATE,
                old_data=old_data,
                new_data=self._object_to_dict(repair_order)
            )
        return repair_order

    def update_repair_order_finish_time(self, order_id: int, finish_time: datetime) -> Optional[RepairOrder]:
        """
        Update the finish time of a repair order.
        Args:
            order_id (int): ID of the repair order.
            finish_time (datetime): New finish time of the repair order.
        Returns:
            Optional[RepairOrder]: The updated repair order if found, otherwise None.
        """
        repair_order = self.get_repair_order_by_id(order_id)
        if repair_order:
            old_data = self._object_to_dict(repair_order)
            repair_order.finish_time = finish_time
            update_query = """
                UPDATE repair_order
                SET finish_time = ?
                WHERE order_id = ?
            """
            self.db.execute_non_query(update_query, (finish_time, order_id))
            self.audit_log_service.log_audit_event(
                table_name="repair_order",
                record_id=order_id,
                operation=OperationType.UPDATE,
                old_data=old_data,
                new_data=self._object_to_dict(repair_order)
            )
        return repair_order

    def delete_repair_order(self, order_id: int) -> Optional[RepairOrder]:
        """
        Delete a repair order by ID.
        Args:
            order_id (int): ID of the repair order.
        Returns:
            Optional[RepairOrder]: The deleted repair order if found, otherwise None.
        """
        repair_order = self.get_repair_order_by_id(order_id)
        if repair_order:
            delete_query = "DELETE FROM repair_order WHERE order_id = ?"
            self.db.execute_non_query(delete_query, (order_id,))
            self.audit_log_service.log_audit_event(
                table_name="repair_order",
                record_id=order_id,
                operation=OperationType.DELETE,
                old_data=self._object_to_dict(repair_order)
            )
        return repair_order

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        result = {}
        for key, value in vars(obj).items():
            if not key.startswith("_"):
                if isinstance(value, (RepairStatus, StaffJobType)):
                    result[key] = value.value if value else None
                else:
                    result[key] = value
        return result
