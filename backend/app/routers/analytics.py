"""Analytics router providing revenue, growth, and performance endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    CustomerRepeatRate,
    GrowthAnalytics,
    PaymentDelay,
    ProductPerformance,
    RegionPerformance,
    RevenueAnalytics,
    SalesTargetStatus,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/revenue", response_model=RevenueAnalytics)
def get_revenue_analytics(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return monthly revenue data for the specified (or current) year."""
    return analytics_service.get_revenue_analytics(db, year=year)


@router.get("/growth", response_model=GrowthAnalytics)
def get_growth_analytics(
    period: str = "monthly",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare revenue between the current and previous period.

    Period options: monthly, quarterly, yearly.
    """
    return analytics_service.get_growth_analytics(db, period=period)


@router.get("/customer-repeat-rate", response_model=CustomerRepeatRate)
def get_customer_repeat_rate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the ratio of customers with more than one order."""
    return analytics_service.get_customer_repeat_rate(db)


@router.get("/product-performance", response_model=List[ProductPerformance])
def get_product_performance(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-product revenue, quantity, and profit margin.

    Optionally filter by product category.
    """
    return analytics_service.get_product_performance(db, category=category)


@router.get("/region-performance", response_model=List[RegionPerformance])
def get_region_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return revenue, order count, and average order value per region."""
    return analytics_service.get_region_performance(db)


@router.get("/payment-delay", response_model=List[PaymentDelay])
def get_payment_delay(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return orders with overdue payments and days overdue."""
    return analytics_service.get_payment_delay(db)


@router.get("/sales-targets", response_model=List[SalesTargetStatus])
def get_sales_targets(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare actual regional revenue against sales targets for the given year."""
    return analytics_service.get_sales_targets(db, year=year)
