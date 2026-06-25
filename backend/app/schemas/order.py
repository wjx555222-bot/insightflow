from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    total: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]
    region: Optional[str] = None
    salesperson: Optional[str] = None
    payment_status: Optional[str] = None
    shipment_status: Optional[str] = None


class OrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    region: Optional[str] = None
    salesperson: Optional[str] = None
    payment_status: Optional[str] = None
    shipment_status: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    order_date: date
    payment_status: str
    shipment_status: str
    region: Optional[str] = None
    salesperson: Optional[str] = None
    total_amount: float
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    order_date: date
    payment_status: str
    shipment_status: str
    region: Optional[str] = None
    salesperson: Optional[str] = None
    total_amount: float

    model_config = ConfigDict(from_attributes=True)
