# schemas/admin.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..models.user import StaffJobType


class AdminUserResponse(BaseModel):
    user_id: int
    name: str
    username: str
    discriminator: str  # customer, staff, admin
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    jobtype: Optional[StaffJobType] = None
    hourly_rate: Optional[float] = None


class AdminUsersResponse(BaseModel):
    status: str
    message: Optional[str] = None
    users: Optional[List[AdminUserResponse]] = None


class AdminStaffResponse(BaseModel):
    staff_id: int
    name: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    jobtype: Optional[str] = None
    hourly_rate: Optional[int] = None


class AdminStaffListResponse(BaseModel):
    status: str
    message: Optional[str] = None
    staff: Optional[List[AdminStaffResponse]] = None


class AdminVehicleResponse(BaseModel):
    vehicle_id: int
    customer_id: int
    license_plate: str
    brand: Optional[str] = None
    model: str
    type: Optional[str] = None
    color: Optional[str] = None
    remarks: Optional[str] = None


class AdminVehiclesResponse(BaseModel):
    status: str
    message: Optional[str] = None
    vehicles: Optional[List[AdminVehicleResponse]] = None


class AdminRepairOrderResponse(BaseModel):
    order_id: int
    vehicle_id: int
    customer_id: int
    request_id: int
    required_staff_type: Optional[str] = None
    status: Optional[str] = None
    order_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    remarks: Optional[str] = None


class AdminRepairOrdersResponse(BaseModel):
    status: str
    message: Optional[str] = None
    repair_orders: Optional[List[AdminRepairOrderResponse]] = None


class CustomerCreate(BaseModel):
    discriminator: str
    name: str
    username: str
    password: str
    phone: str
    email: str
    address: Optional[str] = ""


class StaffCreateRequest(BaseModel):
    discriminator: str
    name: str
    username: str
    password: str
    phone: str
    email: str
    address: Optional[str] = ""
    jobtype: StaffJobType
    hourly_rate: float


class AdminCreate(BaseModel):
    discriminator: str
    name: str
    username: str
    password: str
    phone: str
    email: str
    address: Optional[str] = ""


class AdminUpdateUserProfileReq(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    # staff only fields
    jobtype: Optional[StaffJobType] = None
    hourly_rate: Optional[float] = None
