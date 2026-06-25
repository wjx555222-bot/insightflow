from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RoleResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: RoleResponse
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
