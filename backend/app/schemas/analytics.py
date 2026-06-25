from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class MonthRevenue(BaseModel):
    month: str
    revenue: float


class RevenueAnalytics(BaseModel):
    monthly_data: List[MonthRevenue]
    total_revenue: float
    avg_order_value: float


class GrowthAnalytics(BaseModel):
    current_period_revenue: float
    previous_period_revenue: float
    growth_rate: float
    growth_amount: float


class CustomerRepeatRate(BaseModel):
    repeat_customers: int
    total_customers: int
    repeat_rate: float


class ProductPerformance(BaseModel):
    product_id: int
    product_name: str
    category: str
    total_revenue: float
    total_quantity: int
    profit_margin: float


class RegionPerformance(BaseModel):
    region: str
    revenue: float
    orders: int
    avg_order_value: float


class PaymentDelay(BaseModel):
    order_id: int
    customer_name: str
    amount: float
    due_date: date
    days_overdue: int


class SalesTargetStatus(BaseModel):
    region: str
    target: float
    actual: float
    completion_rate: float
