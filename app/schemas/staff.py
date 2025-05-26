# schemas/staff.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.enums import *


class StaffProfile(BaseModel):
    status: str
    message: Optional[str] = None
    staff_id: Optional[int] = None
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    jobtype: Optional[str] = None
    hourly_rate: Optional[int] = 0


class StaffRepairOrder(BaseModel):
    order_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    customer_id: Optional[int] = None
    request_id: Optional[int] = None
    required_staff_type: Optional[str] = None
    status: Optional[str] = None
    order_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    remarks: Optional[str] = None
    time_worked: Optional[float] = None


class StaffRepairOrdersResponse(BaseModel):
    status: str
    message: str
    staff_id: Optional[int] = None
    staff_name: Optional[str] = None
    repair_orders: Optional[List[StaffRepairOrder]] = None


class MaterialCreate(BaseModel):
    name: str
    quantity: float
    unit_price: float
    remarks: Optional[str] = None


class RepairUpdate(BaseModel):
    order_id: int
    log_message: str
    new_status: Optional[RepairStatus] = None


class RepairOrderGenerate(BaseModel):
    required_staff_type: StaffJobType
    remarks: Optional[str] = None


class AssignmentTimeWorkedUpdate(BaseModel):
    assignment_id: int
    time_worked: float = Field(..., ge=0, description="worked time in hours")


class FinishOrderRequest(BaseModel):
    time_list: List[AssignmentTimeWorkedUpdate]


class StaffProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="员工姓名")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址")
    phone: Optional[str] = Field(None, description="电话")
