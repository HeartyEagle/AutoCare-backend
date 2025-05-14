from dataclasses import dataclass, asdict
from typing import Optional, List
from .enums import VehicleBrand, VehicleType, VehicleColor
from datetime import datetime
from enum import Enum


@dataclass
class Vehicle:
    # Primary key, optional for new objects before DB insert
    vehicle_id: Optional[int] = None
    customer_id: int = 0  # Foreign key to customer
    license_plate: str = ""
    brand: Optional[VehicleBrand] = None
    model: str = ""
    type: Optional[VehicleType] = None
    color: Optional[VehicleColor] = None
    remarks: Optional[str] = None

    def asdict(self):
        return {key: (asdict(self)[key] if not (isinstance(asdict(self)[key], Enum)) else asdict(self)[key].name) for key in asdict(self).keys()}


@dataclass
class Feedback:
    feedback_id: Optional[int] = None  # Primary key, optional for new objects
    customer_id: int = 0  # Foreign key to customer
    order_id: int = 0
    log_id: int = 0  # Foreign key to repair_log
    rating: int = 0
    comments: Optional[str] = None
    feedback_time: Optional[datetime] = None

    def asdict(self):
        return asdict(self)
