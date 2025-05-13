from ..db.connection import Database
from ..models.repair import RepairRequest
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class RepairRequestService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_repair_request(self, vehicle_id: int, customer_id: int, description: str) -> RepairRequest:
        """
        Create a new repair request.
        """
        repair_request = RepairRequest(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            description=description,
            request_time=datetime.now()
        )

        self.db.insert_data("repair_request", {
            "vehicle_id": vehicle_id,
            "customer_id": customer_id,
            "description": description,
            "request_time": repair_request.request_time,
        })

        # Use raw query for identity retrieval (if not wrapped)
        result = self.db.execute_query("SELECT @@IDENTITY AS id")
        repair_request.request_id = int(result[0][0]) if result else None

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
        """
        rows = self.db.select_data(
            table="repair_request",
            columns=["request_id", "vehicle_id", "customer_id", "description", "request_time"],
            filters={"request_id": request_id}
        )

        if not rows:
            return None
        row = rows[0]
        return RepairRequest(
            request_id=row[0],
            vehicle_id=row[1],
            customer_id=row[2],
            description=row[3],
            request_time=row[4] if row[4] else None
        )

    def get_repair_requests_by_customer_id(self, customer_id: int) -> List[RepairRequest]:
        """
        Get all repair requests for a specific customer.
        """
        rows = self.db.select_data(
            table="repair_request",
            columns=["request_id", "vehicle_id", "customer_id", "description", "request_time"],
            filters={"customer_id": customer_id}
        )

        return [
            RepairRequest(
                request_id=row[0],
                vehicle_id=row[1],
                customer_id=row[2],
                description=row[3],
                request_time=row[4] if row[4] else None
            )
            for row in rows
        ] if rows else []

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
