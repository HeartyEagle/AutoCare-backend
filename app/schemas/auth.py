from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Union, Dict


class Token(BaseModel):
    '''Schema for JWT token'''
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    '''Schema for JWT token payload'''
    sub: Optional[int] = None  # store user.id
    exp: Optional[int] = None  # store token expiry
