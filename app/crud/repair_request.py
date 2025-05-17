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

    def create_repair_request(self, vehicle_id: int, customer_id: int, description: str, status: str = "pending") -> RepairRequest:
        """
        Create a new repair request with an initial status.
        Args:
            vehicle_id (int): ID of the vehicle associated with the request.
            customer_id (int): ID of the customer making the request.
            description (str): Description of the repair issue.
            status (str): Initial status of the request (defaults to 'pending').
        Returns:
            RepairRequest: The created repair request object.
        """
        repair_request = RepairRequest(
            vehicle_id=vehicle_id,
            customer_id=customer_id,
            description=description,
            status=status,
            request_time=str(datetime.now())  # Use datetime object directly
        )
        self.db.insert_data("repair_request", {
            "vehicle_id": vehicle_id,
            "customer_id": customer_id,
            "description": description,
            "status": status,
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
        Args:
            request_id (int): ID of the repair request to retrieve.
        Returns:
            Optional[RepairRequest]: The repair request object if found, else None.
        """
        rows = self.db.select_data(
            table_name="repair_request",
            columns=["request_id", "vehicle_id", "customer_id",
                     "description", "status", "request_time"],
            where=f"request_id = {request_id}"
        )
        if not rows:
            return None
        row = rows[0]
        return RepairRequest(
            request_id=row[0],
            vehicle_id=row[1],
            customer_id=row[2],
            description=row[3],
            # Default to 'pending' if None
            status=row[4] if row[4] else "pending",
            request_time=row[5] if row[5] else None
        )

    def get_all_repair_requests(self) -> List[RepairRequest]:
        """
        Get all repair requests in the system.

        Returns:
            List[RepairRequest]: List of all repair request objects.
        """
        rows = self.db.select_data(
            table_name="repair_request",
            columns=["request_id", "vehicle_id", "customer_id",
                     "description", "status", "request_time"]
        )
        return [
            RepairRequest(
                request_id=row[0],
                vehicle_id=row[1],
                customer_id=row[2],
                description=row[3],
                # Default to 'pending' if None
                status=row[4] if row[4] else "pending",
                request_time=row[5] if row[5] else None
            )
            for row in rows
        ] if rows else []

    def get_repair_requests_by_customer_id(self, customer_id: int) -> List[RepairRequest]:
        """
        Get all repair requests for a specific customer.
        Args:
            customer_id (int): ID of the customer whose requests to retrieve.
        Returns:
            List[RepairRequest]: List of repair request objects for the customer.
        """
        rows = self.db.select_data(
            table_name="repair_request",
            columns=["request_id", "vehicle_id", "customer_id",
                     "description", "status", "request_time"],
            where=f"customer_id = {customer_id}"
        )
        return [
            RepairRequest(
                request_id=row[0],
                vehicle_id=row[1],
                customer_id=row[2],
                description=row[3],
                # Default to 'pending' if None
                status=row[4] if row[4] else "pending",
                request_time=row[5] if row[5] else None
            )
            for row in rows
        ] if rows else []

    def update_repair_request_status(self, request_id: int, new_status: str) -> Optional[RepairRequest]:
        """
        Update the status of a repair request.

        Args:
            request_id (int): ID of the repair request to update.
            new_status (str): New status to set for the repair request (e.g., 'pending', 'order_created').

        Returns:
            Optional[RepairRequest]: The updated repair request object if successful, else None.
        """
        # Fetch the existing repair request
        repair_request = self.get_repair_request_by_id(request_id)
        if not repair_request:
            return None

        # Store the old data for audit logging
        old_data = self._object_to_dict(repair_request)

        # Update the status in the object and database
        repair_request.status = new_status
        self.db.update_data(
            table_name="repair_request",
            data={"status": new_status},
            where=f"request_id = {request_id}"
        )

        # Log the update action
        self.audit_log_service.log_audit_event(
            table_name="repair_request",
            record_id=request_id,
            operation=OperationType.UPDATE,
            old_data=old_data,
            new_data=self._object_to_dict(repair_request)
        )

        return repair_request

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
