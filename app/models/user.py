from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from ..db.base import Base
from enum import Enum


class StaffJobType(Enum):
    # 漆工 - 负责车辆喷漆和表面修复 (Responsible for painting and surface repair)
    PAINT_WORKER = "Paint Worker"
    # 焊工 - 负责车辆金属焊接和结构修复 (Responsible for metal welding and structural repair)
    WELDER = "Welder"
    # 汽修工 - 负责车辆机械维修 (Responsible for mechanical repairs)
    AUTO_REPAIR_WORKER = "Auto Repair Worker"
    # 电工 - 负责车辆电气系统维修 (Responsible for electrical system repairs)
    AUTO_ELECTRICIAN = "Auto Electrician"
    # 钣金工 - 负责车身钣金修复 (Responsible for body sheet metal repair)
    SHEET_METAL_WORKER = "Sheet Metal Worker"
    # 诊断技师 - 负责车辆故障诊断 (Responsible for vehicle fault diagnosis)
    DIAGNOSTIC_TECHNICIAN = "Diagnostic Technician"
    # 服务顾问 - 负责客户沟通和服务协调 (Responsible for customer communication and service coordination)
    SERVICE_ADVISOR = "Service Advisor"
    # 配件专员 - 负责配件管理和采购 (Responsible for parts management and procurement)
    PARTS_SPECIALIST = "Parts Specialist"

    def __str__(self):
        return self.value


class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    username = Column(String(20), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    phone = Column(String(15), nullable=False)
    email = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(String(100), nullable=False)
    discriminator = Column(String(50), nullable=False, default="customer")

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': discriminator
    }

    def __repr__(self):
        '''Representation of the User.'''
        return f"<User {self.username}>"


class Admin(User):
    __tablename__ = "admin"

    admin_id = Column(Integer, ForeignKey("user.user_id"),
                      primary_key=True, index=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

    def __repr__(self):
        '''Representation of the Admin.'''
        return f"<Admin {self.username}>"


class Staff(User):
    __tablename__ = "staff"

    staff_id = Column(Integer, ForeignKey("user.user_id"),
                      primary_key=True, index=True)
    jobtype = Column(SQLAlchemyEnum(StaffJobType), nullable=False)
    hourly_rate = Column(Integer, nullable=False)

    repair_assignments = relationship(
        "RepairAssignment", back_populates="staff")
    repair_orders = relationship(
        "RepairOrder", secondary="repair_assignment", back_populates="staffs")
    repair_logs = relationship(
        "RepairLog", back_populates="staff")

    __mapper_args__ = {
        'polymorphic_identity': 'staff',
    }

    def __repr__(self):
        '''Representation of the Staff.'''
        return f"<Staff {self.username}>"

    @hybrid_property
    def total_hours_worked(self):
        '''Calculate the total hours worked by the staff.'''
        return sum(assignment.time_worked for assignment in self.repair_assignments)


class Customer(User):
    __tablename__ = "customer"

    customer_id = Column(Integer, ForeignKey("user.user_id"),
                         primary_key=True, index=True)

    vehicles = relationship(
        "Vehicle", back_populates="customer")
    feedbacks = relationship(
        "Feedback", back_populates="customer")
    repair_requests = relationship(
        "RepairRequest", back_populates="customer")
    repair_orders = relationship(
        "RepairOrder", back_populates="customer")

    __mapper_args__ = {
        'polymorphic_identity': 'customer',
    }

    def __repr__(self):
        '''Representation of the Customer.'''
        return f"<Customer {self.username}>"
