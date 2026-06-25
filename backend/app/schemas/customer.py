from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    region: Optional[str] = None
    customer_type: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    region: Optional[str] = None
    customer_type: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    total_spending: float
    last_purchase_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
