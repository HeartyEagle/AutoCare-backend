from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr
import re
from typing_extensions import Annotated


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

    @field_validator('username')
    @classmethod
    def username_valid(cls, v: str) -> str:
        '''Username validation: only letters, numbers, underscores and 4~20 chars'''
        # Username validation: only letters, numbers, underscore.
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError(
                'Username can only contain letters, numbers, and underscores')

        # Length check: 4-20 characters
        if len(v) < 4 or len(v) > 20:
            raise ValueError('Username must be between 4 and 20 characters')

        return v

    @field_validator('password')
    @classmethod
    def password_valid(cls, v: str) -> str:
        '''Password validation: at least 6 chars, one letter and one number.'''
        # Password must be at least 6 characters
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')

        # Must contain at least one letter
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')

        # Must contain at least one number
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')

        return v


# Schema for login requests
class UserLogin(BaseModel):
    username: str
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
