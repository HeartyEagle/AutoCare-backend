# services/vehicle_service.py
from ..db.connection import Database
from ..models.customer import Vehicle
from ..models.enums import VehicleBrand, VehicleType, VehicleColor
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List


class VehicleService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_vehicle(
            self, customer_id: int, license_plate: str, brand: VehicleBrand,
            model: str, type: VehicleType, color: VehicleColor, remarks: Optional[str] = None
    ) -> Vehicle:
        """
        Create a new vehicle for a customer.
        Args:
            customer_id (int): ID of the customer.
            license_plate (str): License plate of the vehicle.
            brand (VehicleBrand): Brand of the vehicle.
            model (str): Model of the vehicle.
            type (VehicleType): Type of the vehicle.
            color (VehicleColor): Color of the vehicle.
            remarks (Optional[str]): Additional remarks about the vehicle.
        Returns:
            Vehicle: The created vehicle.
        """
        # Create Vehicle object with provided data
        vehicle = Vehicle(
            customer_id=customer_id,
            license_plate=license_plate,
            brand=brand,
            model=model,
            type=type,
            color=color,
            remarks=remarks
        )

        # SQL query to insert vehicle
        insert_query = """
            INSERT INTO vehicle (customer_id, license_plate, brand, model, type, color, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_non_query(
            insert_query,
            (vehicle.customer_id, vehicle.license_plate, vehicle.brand.value,
             vehicle.model, vehicle.type.value, vehicle.color.value, vehicle.remarks)
        )

        # Fetch the inserted vehicle ID (assuming database returns last inserted ID)
        select_id_query = "SELECT @@IDENTITY AS id"
        vehicle_id_row = self.db.execute_query(select_id_query)
        vehicle.vehicle_id = int(
            vehicle_id_row[0][0]) if vehicle_id_row else None

        # Log audit event for the INSERT operation
        self.audit_log_service.log_audit_event(
            table_name="vehicle",
            record_id=vehicle.vehicle_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(vehicle)
        )

        return vehicle

    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """
        Get a vehicle by ID.
        Args:
            vehicle_id (int): ID of the vehicle.
        Returns:
            Optional[Vehicle]: Vehicle object if found, otherwise None.
        """
        select_query = """
            SELECT vehicle_id, customer_id, license_plate, brand, model, type, color, remarks
            FROM vehicle
            WHERE vehicle_id = ?
        """
        rows = self.db.execute_query(select_query, (vehicle_id,))
        if rows:
            # Map row to Vehicle dataclass
            return Vehicle(
                vehicle_id=rows[0][0],
                customer_id=rows[0][1],
                license_plate=rows[0][2],
                brand=VehicleBrand(rows[0][3]) if rows[0][3] else None,
                model=rows[0][4],
                type=VehicleType(rows[0][5]) if rows[0][5] else None,
                color=VehicleColor(rows[0][6]) if rows[0][6] else None,
                remarks=rows[0][7] if rows[0][7] else None
            )
        return None

    def get_vehicles_by_customer_id(self, customer_id: int) -> List[Vehicle]:
        """
        Get vehicles by customer ID.
        Args:
            customer_id (int): ID of the customer.
        Returns:
            Optional[Vehicle]: Vehicle object if found, otherwise None.
        """
        select_query = """
            SELECT vehicle_id, customer_id, license_plate, brand, model, type, color, remarks
            FROM vehicle
            WHERE customer_id = ?
        """
        rows = self.db.execute_query(select_query, (customer_id,))
        vehicles = [
            Vehicle(
                vehicle_id=row[0],
                customer_id=row[1],
                license_plate=row[2],
                brand=VehicleBrand(row[3]) if row[3] else None,
                model=row[4],
                type=VehicleType(row[5]) if row[5] else None,
                color=VehicleColor(row[6]) if row[6] else None,
                remarks=row[7] if row[7] else None
            ) for row in rows
        ]
        return vehicles

    def get_all_vehicles(self) -> List[Vehicle]:
        """
        Get all vehicles in the system.
        Returns:
            List[Vehicle]: List of all vehicle objects.
        """
        select_query = """
            SELECT vehicle_id, customer_id, license_plate, brand, model, type, color, remarks
            FROM vehicle
        """
        rows = self.db.execute_query(select_query)
        vehicles = [
            Vehicle(
                vehicle_id=row[0],
                customer_id=row[1],
                license_plate=row[2],
                brand=VehicleBrand(row[3]) if row[3] else None,
                model=row[4],
                type=VehicleType(row[5]) if row[5] else None,
                color=VehicleColor(row[6]) if row[6] else None,
                remarks=row[7] if row[7] else None
            )
            for row in rows
        ]
        return vehicles

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convert an object to a dictionary for audit logging.
        Args:
            obj: Object to convert.
        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        if not obj:
            return {}
        result = {}
        for key, value in vars(obj).items():
            if not key.startswith("_"):  # Exclude private attributes
                if isinstance(value, (VehicleBrand, VehicleType, VehicleColor)):
                    result[key] = value.value if value else None
                else:
                    result[key] = value
        return result
