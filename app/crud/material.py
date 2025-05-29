# services/material_service.py
from ..db.connection import Database
from ..models.repair import Material
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class MaterialService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_material(
        self,
        log_id: int,
        name: str,
        quantity: float,
        unit_price: float,
        remarks: Optional[str] = None
    ) -> Material:
        """
        Create a new material entry for a repair log.
        """
        material = Material(
            log_id=log_id,
            name=name,
            quantity=quantity,
            unit_price=unit_price,
            remarks=remarks
        )

        # 插入
        self.db.insert_data(
            table_name="material",
            data={
                "log_id":      material.log_id,
                "name":        material.name,
                "quantity":    material.quantity,
                "unit_price":  material.unit_price,
                "remarks":     material.remarks
            }
        )

        # 获取自增主键
        row = self.db.execute_query("SELECT LAST_INSERT_ID()")
        material.material_id = int(row[0][0]) if row else None

        # 审计
        self.audit_log_service.log_audit_event(
            table_name="material",
            record_id=material.material_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(material)
        )
        return material

    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        Retrieve a single material entry by its ID.
        """
        rows = self.db.select_data(
            table_name="material",
            columns=[
                "material_id", "log_id", "name",
                "quantity", "unit_price", "remarks"
            ],
            where=f"material_id = {material_id}",
        )
        if not rows:
            return None

        r = rows[0]
        return Material(
            material_id=r[0],
            log_id=r[1],
            name=r[2],
            quantity=r[3],
            unit_price=r[4],
            remarks=r[5]
        )

    def get_materials_by_log_id(self, log_id: int) -> List[Material]:
        """
        Retrieve all material entries associated with a given repair log.
        """
        rows = self.db.select_data(
            table_name="material",
            columns=[
                "material_id", "log_id", "name",
                "quantity", "unit_price", "remarks"
            ],
            where=f"log_id = {log_id}",
            order_by="material_id ASC"
        )
        return [
            Material(
                material_id=r[0],
                log_id=r[1],
                name=r[2],
                quantity=r[3],
                unit_price=r[4],
                remarks=r[5]
            )
            for r in rows
        ]

    def update_material(
        self,
        material_id: int,
        name: Optional[str] = None,
        quantity: Optional[float] = None,
        unit_price: Optional[float] = None,
        remarks: Optional[str] = None
    ) -> Optional[Material]:
        """
        Update fields of a material entry.
        """
        # 先取旧数据用于审计
        original = self.get_material_by_id(material_id)
        if not original:
            return None
        old_data = self._object_to_dict(original)

        # 构造要更新的字段
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
            original.name = name
        if quantity is not None:
            data["quantity"] = quantity
            original.quantity = quantity
        if unit_price is not None:
            data["unit_price"] = unit_price
            original.unit_price = unit_price
        if remarks is not None:
            data["remarks"] = remarks
            original.remarks = remarks

        if data:
            # 调用通用更新
            self.db.update_data(
                table_name="material",
                data=data,
                where=f"material_id = {material_id}",
            )
            # 审计
            self.audit_log_service.log_audit_event(
                table_name="material",
                record_id=material_id,
                operation=OperationType.UPDATE,
                old_data=old_data,
                new_data=self._object_to_dict(original)
            )
        return original

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material entry by its ID.
        Returns True if deleted.
        """
        # 先取旧数据用于审计
        original = self.get_material_by_id(material_id)
        if not original:
            return False
        old_data = self._object_to_dict(original)

        # 调用通用删除
        deleted = self.db.delete_data(
            table_name="material",
            where=f"material_id = {material_id}",
        )
        if deleted:
            self.audit_log_service.log_audit_event(
                table_name="material",
                record_id=material_id,
                operation=OperationType.DELETE,
                old_data=old_data
            )
            return True
        return False

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        将 dataclass 对象转换为 dict，用于审计日志。
        """
        if not obj:
            return {}
        return {
            key: value
            for key, value in vars(obj).items()
            if not key.startswith("_")
        }
