# services/vehicle_service.py
from ..db.connection import Database
from ..models.customer import Vehicle
from ..models.enums import VehicleBrand, VehicleType, VehicleColor, OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class VehicleService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_vehicle(
        self,
        customer_id: int,
        license_plate: str,
        brand: VehicleBrand,
        model: str,
        type: VehicleType,
        color: VehicleColor,
        remarks: Optional[str] = None
    ) -> Vehicle:
        """
        Create a new vehicle for a customer.
        """
        # created_at = datetime.now()
        vehicle = Vehicle(
            customer_id=customer_id,
            license_plate=license_plate,
            brand=brand,
            model=model,
            type=type,
            color=color,
            remarks=remarks,
            # created_at=created_at  # if your model has a timestamp
        )

        # 插入
        self.db.insert_data(
            table_name="vehicle",
            data=vehicle.asdict()
        )

        # 获取自增主键
        row = self.db.execute_query("SELECT LAST_INSERT_ID()")
        vehicle.vehicle_id = int(row[0][0]) if row else None

        # 审计
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
        """
        rows = self.db.select_data(
            table_name="vehicle",
            columns=[
                "vehicle_id", "customer_id", "license_plate",
                "brand", "model", "type", "color", "remarks"
            ],
            where=f"vehicle_id = {vehicle_id}",
        )
        if not rows:
            return None

        r = rows[0]

        def safe_enum(cls, val):
            try:
                return cls(val) if val is not None else None
            except ValueError:
                return None
        return Vehicle(
            vehicle_id=r[0],
            customer_id=r[1],
            license_plate=r[2],
            brand=safe_enum(VehicleBrand, r[3]),
            model=r[4],
            type=safe_enum(VehicleType, r[5]),
            color=safe_enum(VehicleColor, r[6]),
            remarks=r[7],
            # created_at=r[8]
        )

    def get_vehicles_by_customer_id(self, customer_id: int) -> List[Vehicle]:
        """
        Get vehicles by customer ID.
        """
        rows = self.db.select_data(
            table_name="vehicle",
            columns=[
                "vehicle_id", "customer_id", "license_plate",
                "brand", "model", "type", "color", "remarks"
            ],
            where=f"customer_id = {customer_id}",
            order_by="vehicle_id ASC"
        )

        def safe_enum(cls, val):
            try:
                return cls(val) if val is not None else None
            except ValueError:
                return None

        return [
            Vehicle(
                vehicle_id=r[0],
                customer_id=r[1],
                license_plate=r[2],
                brand=safe_enum(VehicleBrand, r[3]),
                model=r[4],
                type=safe_enum(VehicleType, r[5]),
                color=safe_enum(VehicleColor, r[6]),
                remarks=r[7],
                # created_at=r[8]
            )
            for r in rows
        ]

    def get_all_vehicles(self) -> List[Vehicle]:
        """
        Get all vehicles in the system.
        """
        rows = self.db.select_data(
            table_name="vehicle",
            columns=[
                "vehicle_id", "customer_id", "license_plate",
                "brand", "model", "type", "color", "remarks"
            ]
        )

        def safe_enum(cls, val):
            try:
                return cls(val) if val is not None else None
            except Exception:
                return None
        return [
            Vehicle(
                vehicle_id=r[0],
                customer_id=r[1],
                license_plate=r[2],
                brand=safe_enum(VehicleBrand, r[3]),
                model=r[4],
                type=safe_enum(VehicleType, r[5]),
                color=safe_enum(VehicleColor, r[6]),
                remarks=r[7],
                # created_at=r[8]
            )
            for r in rows
        ]

    def update_vehicle(
        self,
        vehicle_id: int,
        *,
        license_plate: Optional[str] = None,
        brand: Optional[VehicleBrand] = None,
        model: Optional[str] = None,
        type: Optional[VehicleType] = None,
        color: Optional[VehicleColor] = None,
        remarks: Optional[str] = None
    ) -> Optional[Vehicle]:
        """
        Update fields of an existing vehicle.
        """
        original = self.get_vehicle_by_id(vehicle_id)
        if not original:
            return None
        old_data = self._object_to_dict(original)

        updates: Dict[str, Any] = {}
        if license_plate is not None:
            updates["license_plate"] = license_plate
            original.license_plate = license_plate
        if brand is not None:
            updates["brand"] = brand.value
            original.brand = brand
        if model is not None:
            updates["model"] = model
            original.model = model
        if type is not None:
            updates["type"] = type.value
            original.type = type
        if color is not None:
            updates["color"] = color.value
            original.color = color
        if remarks is not None:
            updates["remarks"] = remarks
            original.remarks = remarks

        if updates:
            self.db.update_data(
                table_name="vehicle",
                data=updates,
                where=f"vehicle_id = {vehicle_id}",
            )
            self.audit_log_service.log_audit_event(
                table_name="vehicle",
                record_id=vehicle_id,
                operation=OperationType.UPDATE,
                old_data=old_data,
                new_data=self._object_to_dict(original)
            )
        return original

    def delete_vehicle(self, vehicle_id: int) -> bool:
        """
        Delete a vehicle by ID.
        Returns True if the vehicle existed and was deleted.
        """
        original = self.get_vehicle_by_id(vehicle_id)
        if not original:
            return False
        old_data = self._object_to_dict(original)

        deleted = self.db.delete_data(
            table_name="vehicle",
            where=f"vehicle_id = {vehicle_id}",
        )
        if deleted:
            self.audit_log_service.log_audit_event(
                table_name="vehicle",
                record_id=vehicle_id,
                operation=OperationType.DELETE,
                old_data=old_data
            )
            return True
        return False

    def _object_to_dict(self, obj: Vehicle) -> Dict[str, Any]:
        """
        Convert a Vehicle object to dict for audit logging.
        """
        result: Dict[str, Any] = {}
        for key, val in vars(obj).items():
            if key.startswith("_"):
                continue
            if isinstance(val, (VehicleBrand, VehicleType, VehicleColor)):
                result[key] = val.value
            else:
                result[key] = val
        return result
