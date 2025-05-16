# models/repair_models.py
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime
from .enums import RepairStatus, StaffJobType


@dataclass
class RepairRequest:
    # Primary key, optional for new objects before DB insert
    request_id: Optional[int] = None
    vehicle_id: int = 0  # Foreign key to vehicle
    customer_id: int = 0  # Foreign key to customer
    description: str = ""
    status: Optional[str] = "pending"  # pending, or order_created
    request_time: Optional[datetime] = None

    def asdict(self):
        return asdict(self)


@dataclass
class RepairAssignment:
    # Primary key, optional for new objects
    assignment_id: Optional[int] = None
    order_id: int = 0  # Foreign key to repair_order
    staff_id: int = 0  # Foreign key to staff
    status: str = "pending"  # pending, accepted, rejected
    time_worked: Optional[float] = None

    @property
    def assignment_fee(self) -> float:
        """Calculate assignment fee based on time worked and staff hourly rate."""
        if self.time_worked and self.staff and hasattr(self.staff, 'hourly_rate'):
            return self.time_worked * self.staff.hourly_rate
        return 0.0

    def asdict(self):
        return asdict(self)


@dataclass
class RepairOrder:
    order_id: Optional[int] = None  # Primary key, optional for new objects
    vehicle_id: int = 0  # Foreign key to vehicle
    customer_id: int = 0  # Foreign key to customer
    request_id: int = 0  # Foreign key to repair_request
    required_staff_type: Optional[StaffJobType] = None
    status: Optional[RepairStatus] = None
    order_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    remarks: Optional[str] = None

    @property
    def material_fee(self) -> float:
        """Calculate total material fee from repair logs if status is COMPLETED."""
        if self.status == RepairStatus.COMPLETED and self.repair_logs:
            return sum(log.material_fee for log in self.repair_logs if log.material_fee)
        return 0.0

    @property
    def labor_fee(self) -> float:
        """Calculate total labor fee from repair assignments if status is COMPLETED."""
        if self.status == RepairStatus.COMPLETED and self.repair_assignments:
            return sum(assignment.assignment_fee for assignment in self.repair_assignments if assignment.assignment_fee)
        return 0.0

    def asdict(self):
        return asdict(self)


@dataclass
class RepairLog:
    log_id: Optional[int] = None  # Primary key, optional for new objects
    order_id: int = 0  # Foreign key to repair_order
    staff_id: int = 0  # Foreign key to staff
    log_time: Optional[datetime] = None
    log_message: str = ""

    @property
    def material_fee(self) -> float:
        """Calculate total material fee from materials."""
        if self.materials:
            return sum(material.total_price for material in self.materials if material.total_price)
        return 0.0

    def asdict(self):
        return asdict(self)


@dataclass
class Material:
    material_id: Optional[int] = None  # Primary key, optional for new objects
    log_id: int = 0  # Foreign key to repair_log
    name: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    remarks: Optional[str] = None

    @property
    def total_price(self) -> float:
        """Calculate total price as quantity * unit_price."""
        return self.quantity * self.unit_price

    def asdict(self):
        return asdict(self)
