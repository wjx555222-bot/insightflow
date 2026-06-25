from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    total_products: int
    overdue_amount: float
    low_stock_count: int


class SalesTrendPoint(BaseModel):
    month: str
    revenue: float
    orders: int


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    total_revenue: float
    total_quantity: int


class TopCustomer(BaseModel):
    customer_id: int
    customer_name: str
    total_spending: float
    order_count: int


class RegionPerformance(BaseModel):
    region: str
    total_revenue: float
    order_count: int


class RecentOrder(BaseModel):
    id: int
    customer_name: str
    order_date: datetime
    total_amount: float
    payment_status: str
    shipment_status: str


class DashboardAlert(BaseModel):
    alert_type: str
    message: str
    severity: str
    entity_id: Optional[int] = None
