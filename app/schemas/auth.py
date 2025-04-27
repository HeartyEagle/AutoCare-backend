from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Union, Dict


class Token(BaseModel):
    '''Schema for JWT token'''
    status: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    message: Optional[str] = None


class TokenPayload(BaseModel):
    '''Schema for JWT token payload'''
    sub: Optional[int] = None  # store user.id
    exp: Optional[int] = None  # store token expiry


class RegisterResponse(BaseModel):
    '''Schema for user registration response'''
    status: str
    message: Optional[str] = None
    user_id: Optional[int] = None  # store user.id
