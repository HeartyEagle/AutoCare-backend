from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.base import Base
from enum import Enum
import json


class OperationType(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    table_name = Column(String(50), nullable=False)  # 操作的表名，例如 repair_order
    record_id = Column(Integer, nullable=False)  # 操作的记录ID，例如 order_id
    operation = Column(OperationType, nullable=False)
    old_data = Column(Text, nullable=True)  # 操作前的记录快照（JSON 格式）
    new_data = Column(Text, nullable=True)  # 操作后的记录快照（JSON 格式）
    operated_by = Column(Integer, ForeignKey(
        "staff.staff_id"), nullable=True)  # 操作人ID
    operated_at = Column(DateTime(timezone=True),
                         server_default=func.now())  # 操作时间

    operator = relationship("Staff")  # 关联到操作人（可选）
