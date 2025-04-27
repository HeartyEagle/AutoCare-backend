from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from ..db.base import Base
from enum import Enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship


class VehicleBrand(str, Enum):
    TOYOTA = "Toyota"
    HONDA = "Honda"
    FORD = "Ford"
    CHEVROLET = "Chevrolet"
    NISSAN = "Nissan"
    BMW = "BMW"
    MERCEDES = "Mercedes-Benz"
    AUDI = "Audi"
    VOLKSWAGEN = "Volkswagen"
    HYUNDAI = "Hyundai"
    KIA = "Kia"


class VehicleType(str, Enum):
    SEDAN = "Sedan"
    SUV = "SUV"
    TRUCK = "Truck"
    VAN = "Van"
    COUPE = "Coupe"
    HATCHBACK = "Hatchback"
    CONVERTIBLE = "Convertible"
    WAGON = "Wagon"
    MOTORCYCLE = "Motorcycle"
    BUS = "Bus"


class VehicleColor(str, Enum):
    RED = "Red"
    BLUE = "Blue"
    GREEN = "Green"
    BLACK = "Black"
    WHITE = "White"
    SILVER = "Silver"
    YELLOW = "Yellow"
    ORANGE = "Orange"
    PURPLE = "Purple"
    PINK = "Pink"
    GREY = "Grey"


class Vehicle(Base):
    __tablename__ = "vehicle"

    vehicle_id = Column(Integer, primary_key=True,
                        index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey(
        "customer.customer_id"), nullable=False)
    license_plate = Column(String(20), unique=True, nullable=False)
    brand = Column(SQLAlchemyEnum(VehicleBrand), nullable=False)
    model = Column(String(50), nullable=False)
    type = Column(SQLAlchemyEnum(VehicleType), nullable=False)
    color = Column(SQLAlchemyEnum(VehicleColor), nullable=False)
    remarks = Column(String(200), nullable=True)

    customer = relationship(
        "Customer", back_populates="vehicles")
    repair_requests = relationship(
        "RepairRequest", back_populates="vehicle")
    repair_orders = relationship(
        "RepairOrder", back_populates="vehicle")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True,
                         index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey(
        "customer.customer_id"), nullable=False)
    log_id = Column(Integer, ForeignKey(
        "repair_log.log_id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comments = Column(String(255), nullable=True)
    feedback_time = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship(
        "Customer", back_populates="feedbacks")
    repair_log = relationship(
        "RepairLog", back_populates="feedbacks")
