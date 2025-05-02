from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from ..db.base import Base
from enum import Enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ..models.user import StaffJobType


class RepairStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class RepairRequest(Base):
    __tablename__ = "repair_request"

    request_id = Column(Integer, primary_key=True,
                        index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey(
        "vehicle.vehicle_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey(
        "customer.customer_id"), nullable=False)
    description = Column(String(255), nullable=False)
    request_time = Column(DateTime(timezone=True), server_default=func.now())

    repair_orders = relationship(
        "RepairOrder", back_populates="repair_request")
    vehicle = relationship("Vehicle", back_populates="repair_requests")
    customer = relationship("Customer", back_populates="repair_requests")


class RepairAssignment(Base):
    __tablename__ = "repair_assignment"

    assignment_id = Column(Integer, primary_key=True,
                           index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(
        "repair_order.order_id"), nullable=False)
    staff_id = Column(Integer, ForeignKey(
        "staff.staff_id"), nullable=False)
    time_worked = Column(Float, nullable=True)

    repair_order = relationship(
        "RepairOrder", back_populates="repair_assignments")
    staff = relationship("Staff", back_populates="repair_assignments")

    @hybrid_property
    def assignment_fee(self):
        if self.time_worked and self.staff:
            return self.time_worked * self.staff.hourly_rate
        return 0


class RepairOrder(Base):
    __tablename__ = "repair_order"

    order_id = Column(Integer, primary_key=True,
                      index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey(
        "vehicle.vehicle_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey(
        "customer.customer_id"), nullable=False)
    request_id = Column(Integer, ForeignKey(
        "repair_request.request_id"), nullable=False)
    required_staff_type = Column(SQLAlchemyEnum(StaffJobType), nullable=False)
    status = Column(SQLAlchemyEnum(RepairStatus), nullable=False)
    order_time = Column(DateTime(timezone=True), server_default=func.now())
    finish_time = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(String(255), nullable=True)

    repair_request = relationship(
        "RepairRequest", back_populates="repair_orders")
    repair_logs = relationship(
        "RepairLog", back_populates="repair_order", cascade="all, delete-orphan")
    staffs = relationship(
        "Staff", secondary="repair_assignment", back_populates="repair_orders")
    repair_assignments = relationship(
        "RepairAssignment", back_populates="repair_order", cascade="all, delete-orphan")
    vehicle = relationship("Vehicle", back_populates="repair_orders")
    customer = relationship("Customer", back_populates="repair_orders")

    @hybrid_property
    def material_fee(self):
        if self.status == RepairStatus.COMPLETED:
            return sum(log.material_fee for log in self.repair_logs)
        return 0

    @hybrid_property
    def labor_fee(self):
        if self.status == RepairStatus.COMPLETED:
            return sum(assignment.assignment_fee for assignment in self.repair_assignments)
        return 0


class RepairLog(Base):
    __tablename__ = "repair_log"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(
        "repair_order.order_id"), nullable=False)
    staff_id = Column(Integer, ForeignKey(
        "staff.staff_id"), nullable=False)
    log_time = Column(DateTime(timezone=True), server_default=func.now())
    log_message = Column(String(255), nullable=False)

    materials = relationship(
        "Material", back_populates="repair_log", cascade="all, delete-orphan")
    repair_order = relationship(
        "RepairOrder", back_populates="repair_logs")
    feedbacks = relationship(
        "Feedback", back_populates="repair_log")
    staff = relationship("Staff", back_populates="repair_logs")

    @hybrid_property
    def material_fee(self):
        if self.material:
            return sum(
                material.total_price for material in self.materials)
        return 0


class Material(Base):
    __tablename__ = "material"

    material_id = Column(Integer, primary_key=True,
                         index=True, autoincrement=True)
    log_id = Column(Integer, ForeignKey(
        "repair_log.log_id"), nullable=False)
    name = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    remarks = Column(String(255), nullable=True)

    repair_log = relationship("RepairLog", back_populates="materials")

    @hybrid_property
    def total_price(self):
        return self.quantity * self.unit_price
