from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
from .enums import OperationType


@dataclass
class AuditLog:
    log_id: Optional[int] = None
    table_name: str = ""
    record_id: int = 0
    operation: Optional[OperationType] = None
    old_data: Optional[str] = None
    new_data: Optional[str] = None
    operated_at: Optional[datetime] = None

    def asdict(self):
        return asdict(self)
