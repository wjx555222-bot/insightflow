from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SupplierResponse(BaseModel):
    id: int
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    supplier_id: Optional[int] = None
    unit_price: float
    cost_price: Optional[float] = None
    current_stock: Optional[int] = None
    reorder_level: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[int] = None
    unit_price: Optional[float] = None
    cost_price: Optional[float] = None
    current_stock: Optional[int] = None
    reorder_level: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    supplier: Optional[SupplierResponse] = None

    model_config = ConfigDict(from_attributes=True)
