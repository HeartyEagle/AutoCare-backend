from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from .enums import OperationType


@dataclass
class AuditLog:
    # Primary key, optional for new objects before DB insert
    log_id: Optional[int] = None
    table_name: str = ""  # Name of the table operated on
    record_id: int = 0  # ID of the record operated on
    # Type of operation (INSERT, UPDATE, DELETE)
    operation: Optional[OperationType] = None
    old_data: Optional[str] = None  # JSON snapshot of data before operation
    new_data: Optional[str] = None  # JSON snapshot of data after operation
    operated_at: Optional[datetime] = None  # Timestamp of the operation
