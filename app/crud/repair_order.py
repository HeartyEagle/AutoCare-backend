from ..db.connection import Database
from ..models.repair import RepairOrder
from ..models.enums import RepairStatus, StaffJobType, OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class RepairOrderService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_order(
        self,
        vehicle_id: int,
        customer_id: int,
        request_id: int,
        required_staff_type: StaffJobType,
        status: RepairStatus,
        remarks: Optional[str] = None
    ) -> RepairOrder:
        """
        Create a new repair order.
        """
        now = datetime.now()
        repair_order = RepairOrder(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            request_id=request_id,
            required_staff_type=required_staff_type,
            status=status,
            order_time=str(now),
            remarks=remarks
        )

        # 插入
        self.db.insert_data(
            table_name="repair_order",
            data={
                "vehicle_id": vehicle_id,
                "customer_id": customer_id,
                "request_id": request_id,
                "required_staff_type": required_staff_type.value,
                "status": status.value,
                "order_time": str(now),
                "remarks": remarks,
            }
        )

        # 拉取自增主键
        row = self.db.execute_query("SELECT LAST_INSERT_ID()")
        repair_order.order_id = int(row[0][0]) if row else None

        # 审计
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
        """
        rows = self.db.select_data(
            table_name="repair_order",
            columns=[
                "order_id", "vehicle_id", "customer_id",
                "request_id", "required_staff_type",
                "status", "order_time", "finish_time", "remarks"
            ],
            where=f"order_id = {order_id}",
        )
        if not rows:
            return None
        r = rows[0]
        return RepairOrder(
            order_id=r[0],
            vehicle_id=r[1],
            customer_id=r[2],
            request_id=r[3],
            required_staff_type=StaffJobType(
                r[4]) if r[4] is not None else None,
            status=RepairStatus(r[5]) if r[5] is not None else None,
            order_time=r[6],
            finish_time=r[7],
            remarks=r[8]
        )

    def get_repair_orders_by_customer_id(self, customer_id: int) -> List[RepairOrder]:
        """
        Get all repair orders for a specific customer.
        """
        rows = self.db.select_data(
            table_name="repair_order",  # 注意：取决于表名，若为 repair_order 则改回
            columns=[
                "order_id", "vehicle_id", "customer_id",
                "request_id", "required_staff_type",
                "status", "order_time", "finish_time", "remarks"
            ],
            where=f"customer_id = {customer_id}",
        )
        return [
            RepairOrder(
                order_id=r[0],
                vehicle_id=r[1],
                customer_id=r[2],
                request_id=r[3],
                required_staff_type=StaffJobType(
                    r[4]) if r[4] is not None else None,
                status=RepairStatus(r[5]) if r[5] is not None else None,
                order_time=r[6],
                finish_time=r[7],
                remarks=r[8]
            )
            for r in rows
        ]

    def get_repair_orders_by_staff_id(self, staff_id: int) -> List[Dict[str, Any]]:
        """
        Get all repair orders assigned to a staff member, including worked hours.
        """
        rows = self.db.select_data(
            table_name="repair_order ro",
            columns=[
                "ro.order_id", "ro.vehicle_id", "ro.customer_id", "ro.request_id",
                "ro.required_staff_type", "ro.status", "ro.order_time",
                "ro.finish_time", "ro.remarks", "ra.time_worked"
            ],
            joins=["INNER JOIN repair_assignment ra ON ro.order_id = ra.order_id"],
            where=f"ra.staff_id = {staff_id}"
        )
        return [
            {
                "order_id": r[0],
                "vehicle_id": r[1],
                "customer_id": r[2],
                "request_id": r[3],
                "required_staff_type": StaffJobType(r[4]).value if r[4] else None,
                "status": RepairStatus(r[5]).value if r[5] else None,
                "order_time": r[6],
                "finish_time": r[7],
                "remarks": r[8],
                "time_worked": r[9] or 0.0
            }
            for r in rows
        ]

    def get_all_repair_orders(self) -> List[RepairOrder]:
        """
        Get all repair orders in the system.
        """
        rows = self.db.select_data(
            table_name="repair_order",
            columns=[
                "order_id", "vehicle_id", "customer_id", "request_id",
                "required_staff_type", "status",
                "order_time", "finish_time", "remarks"
            ]
        )
        return [
            RepairOrder(
                order_id=r[0],
                vehicle_id=r[1],
                customer_id=r[2],
                request_id=r[3],
                required_staff_type=StaffJobType(
                    r[4]) if r[4] is not None else None,
                status=RepairStatus(r[5]) if r[5] is not None else None,
                order_time=r[6],
                finish_time=r[7],
                remarks=r[8]
            )
            for r in rows
        ]

    def update_repair_order_status(self, order_id: int, status: RepairStatus) -> Optional[RepairOrder]:
        """
        Update the status of a repair order.
        """
        order = self.get_repair_order_by_id(order_id)
        if not order:
            return None

        old = self._object_to_dict(order)
        order.status = status

        # 调用 update_data
        self.db.update_data(
            table_name="repair_order",
            data={"status": status.value},
            where=f"order_id = {order_id}"
        )
        self.audit_log_service.log_audit_event(
            table_name="repair_order",
            record_id=order_id,
            operation=OperationType.UPDATE,
            old_data=old,
            new_data=self._object_to_dict(order)
        )
        return order

    def update_repair_order_finish_time(self, order_id: int, finish_time: datetime) -> Optional[RepairOrder]:
        """
        Update the finish time of a repair order.
        """
        order = self.get_repair_order_by_id(order_id)
        if not order:
            return None

        old = self._object_to_dict(order)
        order.finish_time = finish_time

        self.db.update_data(
            table_name="repair_order",
            data={"finish_time": finish_time},
            where=f"order_id = {order_id}",
        )
        self.audit_log_service.log_audit_event(
            table_name="repair_order",
            record_id=order_id,
            operation=OperationType.UPDATE,
            old_data=old,
            new_data=self._object_to_dict(order)
        )
        return order

    def delete_repair_order(self, order_id: int) -> Optional[RepairOrder]:
        """
        Delete a repair order by ID.
        """
        order = self.get_repair_order_by_id(order_id)
        if not order:
            return None

        # 调用 delete_data
        self.db.delete_data(
            table_name="repair_order",
            where=f"order_id = {order_id}",
        )
        self.audit_log_service.log_audit_event(
            table_name="repair_order",
            record_id=order_id,
            operation=OperationType.DELETE,
            old_data=self._object_to_dict(order)
        )
        return order

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        result: Dict[str, Any] = {}
        for key, val in vars(obj).items():
            if key.startswith("_"):
                continue
            if isinstance(val, (RepairStatus, StaffJobType)):
                result[key] = val.value
            else:
                result[key] = val
        return result
