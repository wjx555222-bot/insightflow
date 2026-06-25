"""Dashboard router providing summary stats and analytics widgets."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAlert,
    DashboardSummary,
    RecentOrder,
    RegionPerformance,
    SalesTrendPoint,
    TopCustomer,
    TopProduct,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return high-level dashboard KPIs: revenue, orders, customers, etc."""
    return dashboard_service.get_summary(db)


@router.get("/sales-trend", response_model=List[SalesTrendPoint])
def get_sales_trend(
    months: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return monthly revenue and order count for the last N months."""
    return dashboard_service.get_sales_trend(db, months=months)


@router.get("/top-products", response_model=List[TopProduct])
def get_top_products(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the top products ranked by total revenue."""
    return dashboard_service.get_top_products(db, limit=limit)


@router.get("/top-customers", response_model=List[TopCustomer])
def get_top_customers(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the top customers ranked by total spending."""
    return dashboard_service.get_top_customers(db, limit=limit)


@router.get("/region-performance", response_model=List[RegionPerformance])
def get_region_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return order revenue and count grouped by region."""
    return dashboard_service.get_region_performance(db)


@router.get("/recent-orders", response_model=List[RecentOrder])
def get_recent_orders(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the most recent orders with customer names."""
    return dashboard_service.get_recent_orders(db, limit=limit)


@router.get("/alerts", response_model=List[DashboardAlert])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return active alerts for low stock, overdue payments, and cancellations."""
    return dashboard_service.get_alerts(db)
