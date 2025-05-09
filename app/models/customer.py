from dataclasses import dataclass
from typing import Optional, List
from .enums import VehicleBrand, VehicleType, VehicleColor
from datetime import datetime


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


@dataclass
class Feedback:
    feedback_id: Optional[int] = None  # Primary key, optional for new objects
    customer_id: int = 0  # Foreign key to customer
    log_id: int = 0  # Foreign key to repair_log
    rating: int = 0
    comments: Optional[str] = None
    feedback_time: Optional[datetime] = None
