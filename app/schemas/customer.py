from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    """
    Schema for customer profile.
    """
    status: str
    message: Optional[str] = None
    customer_id: Optional[int] = None
    name: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class VehicleResponse(BaseModel):
    vehicle_id: int
    license_plate: str
    brand: Optional[str]
    model: str
    type: Optional[str]
    color: Optional[str]
    remarks: Optional[str]


class CustomerVehiclesResponse(BaseModel):
    status: str
    message: Optional[str] = None
    customer_id: Optional[int] = None
    vehicles: Optional[List[VehicleResponse]] = None


class RepairRequestResponse(BaseModel):
    request_id: int
    vehicle_id: int
    customer_id: int
    description: str
    request_time: datetime


class CustomerRepairRequestsResponse(BaseModel):
    status: str
    message: Optional[str] = None
    customer_id: Optional[int] = None
    repair_requests: Optional[List[RepairRequestResponse]] = None


class RepairOrderResponse(BaseModel):
    order_id: int
    vehicle_id: int
    customer_id: int
    request_id: int
    required_staff_type: Optional[str]
    status: Optional[str]
    order_time: datetime
    remarks: Optional[str] = None


class CustomerRepairOrdersResponse(BaseModel):
    status: str
    message: Optional[str] = None
    customer_id: Optional[int] = None
    repair_orders: Optional[List[RepairOrderResponse]] = None


class RepairLogResponse(BaseModel):
    log_id: int
    order_id: int
    staff_id: int
    log_time: datetime
    log_message: Optional[str] = None


class CustomerRepairLogsResponse(BaseModel):
    status: str
    message: Optional[str] = None
    repair_logs: Optional[List[RepairLogResponse]] = None
