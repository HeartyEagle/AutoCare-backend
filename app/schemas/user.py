from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr
import re
from typing_extensions import Annotated
from ..models.user import StaffJobType


# Base User Schema with common properties
class UserBase(BaseModel):
    username: str


# Schema for creating a new user
class UserCreate(UserBase):
    password: str
    name: Annotated[str, Field(min_length=2, max_length=50)]
    address: Annotated[str, Field(min_length=5, max_length=100)]
    username: Annotated[str, Field(min_length=4, max_length=20)]
    email: Annotated[EmailStr, Field(min_length=5, max_length=50)]
    phone: Annotated[str, Field(min_length=10, max_length=15)]


class StaffCreate(UserCreate):
    jobtype: StaffJobType
    hourly_rate: Annotated[int, Field(gt=0)]


# Schema for login requests
class UserLogin(BaseModel):
    username: str
    role: str
    password: str


# Response schema after user creation
class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


# Public user data (for API responses)
class User(UserBase):
    id: int
    is_active: bool

    model_config = {
        "from_attributes": True
    }


# Token schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str


class UserSchema(BaseModel):
    id: int
    username: str
    created_at: datetime
