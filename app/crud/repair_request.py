# services/repair_request_service.py
from db.connection import Database
from models.repair import RepairRequest
from models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any


class RepairRequestService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_request(self, vehicle_id: int, customer_id: int, description: str) -> RepairRequest:
        """
        Create a new repair request.
        Args:
            vehicle_id (int): ID of the vehicle.
            customer_id (int): ID of the customer.
            description (str): Description of the repair request.
        Returns:
            RepairRequest: The created repair request.
        """
        repair_request = RepairRequest(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            description=description
        )
        insert_query = """
            INSERT INTO repair_request (vehicle_id, customer_id, description, request_time)
            VALUES (?, ?, ?, GETDATE())
        """
        self.db.execute_non_query(
            insert_query,
            (repair_request.vehicle_id, repair_request.customer_id,
             repair_request.description)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        request_id_row = self.db.execute_query(select_id_query)
        repair_request.request_id = int(
            request_id_row[0][0]) if request_id_row else None
        self.audit_log_service.log_audit_event(
            table_name="repair_request",
            record_id=repair_request.request_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(repair_request)
        )
        return repair_request

    def get_repair_request_by_id(self, request_id: int) -> Optional[RepairRequest]:
        """
        Get a repair request by ID.
        Args:
            request_id (int): ID of the repair request.
        Returns:
            Optional[RepairRequest]: RepairRequest object if found, otherwise None.
        """
        select_query = """
            SELECT request_id, vehicle_id, customer_id, description, request_time
            FROM repair_request
            WHERE request_id = ?
        """
        rows = self.db.execute_query(select_query, (request_id,))
        if rows:
            return RepairRequest(
                request_id=rows[0][0],
                vehicle_id=rows[0][1],
                customer_id=rows[0][2],
                description=rows[0][3],
                request_time=rows[0][4] if rows[0][4] else None
            )
        return None

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
