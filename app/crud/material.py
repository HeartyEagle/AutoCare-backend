# services/material_service.py
from ..db.connection import Database
from ..models.repair import Material
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any


class MaterialService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_material(self, log_id: int, name: str, quantity: float, unit_price: float, remarks: Optional[str] = None) -> Material:
        """
        Create a new material entry for a repair log.
        Args:
            log_id (int): ID of the repair log.
            name (str): Name of the material.
            quantity (float): Quantity of the material used.
            unit_price (float): Unit price of the material.
            remarks (Optional[str]): Additional remarks about the material.
        Returns:
            Material: The created material entry.
        """
        material = Material(
            log_id=log_id,
            name=name,
            quantity=quantity,
            unit_price=unit_price,
            remarks=remarks
        )
        insert_query = """
            INSERT INTO material (log_id, name, quantity, unit_price, remarks)
            VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute_non_query(
            insert_query,
            (material.log_id, material.name, material.quantity,
             material.unit_price, material.remarks)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        material_id_row = self.db.execute_query(select_id_query)
        material.material_id = int(
            material_id_row[0][0]) if material_id_row else None
        self.audit_log_service.log_audit_event(
            table_name="material",
            record_id=material.material_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(material)
        )
        return material

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
