from datetime import date, datetime
from typing import List

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.inventory import Payment
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.dashboard import (
    DashboardAlert,
    DashboardSummary,
    RecentOrder,
    RegionPerformance,
    SalesTrendPoint,
    TopCustomer,
    TopProduct,
)


def get_summary(db: Session) -> DashboardSummary:
    """Aggregate high-level business metrics from orders, customers, products,
    payments, and inventory."""
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .scalar()
    )
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0

    # Overdue payments: status != paid and due_date is in the past
    overdue_amount = (
        db.query(func.coalesce(func.sum(Payment.amount), 0.0))
        .filter(
            Payment.status != "paid",
            Payment.due_date < date.today(),
        )
        .scalar()
    )

    # Low stock: current_stock <= reorder_level and status is active
    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.current_stock <= Product.reorder_level,
            Product.status == "active",
        )
        .scalar()
        or 0
    )

    return DashboardSummary(
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_customers=total_customers,
        total_products=total_products,
        overdue_amount=overdue_amount,
        low_stock_count=low_stock_count,
    )


def get_sales_trend(db: Session, months: int = 12) -> List[SalesTrendPoint]:
    """Return monthly revenue and order count for the last N months."""
    results = (
        db.query(
            func.date_trunc("month", Order.order_date).label("month"),
            func.coalesce(func.sum(Order.total_amount), 0.0).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .filter(Order.order_date >= _months_ago(months))
        .group_by(func.date_trunc("month", Order.order_date))
        .order_by(func.date_trunc("month", Order.order_date))
        .all()
    )

    return [
        SalesTrendPoint(
            month=row.month.strftime("%Y-%m"),
            revenue=row.revenue,
            orders=row.orders,
        )
        for row in results
    ]


def get_top_products(db: Session, limit: int = 5) -> List[TopProduct]:
    """Return the top products by total revenue from order items."""
    results = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.coalesce(func.sum(OrderItem.total), 0.0).label("total_revenue"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.total).desc())
        .limit(limit)
        .all()
    )

    return [
        TopProduct(
            product_id=row.product_id,
            product_name=row.product_name,
            total_revenue=row.total_revenue,
            total_quantity=row.total_quantity,
        )
        for row in results
    ]


def get_top_customers(db: Session, limit: int = 5) -> List[TopCustomer]:
    """Return the top customers by total order amount."""
    results = (
        db.query(
            Customer.id.label("customer_id"),
            Customer.name.label("customer_name"),
            func.coalesce(func.sum(Order.total_amount), 0.0).label("total_spending"),
            func.count(Order.id).label("order_count"),
        )
        .join(Order, Customer.id == Order.customer_id)
        .group_by(Customer.id, Customer.name)
        .order_by(func.sum(Order.total_amount).desc())
        .limit(limit)
        .all()
    )

    return [
        TopCustomer(
            customer_id=row.customer_id,
            customer_name=row.customer_name,
            total_spending=row.total_spending,
            order_count=row.order_count,
        )
        for row in results
    ]


def get_region_performance(db: Session) -> List[RegionPerformance]:
    """Return order counts and revenue grouped by region."""
    results = (
        db.query(
            Order.region,
            func.coalesce(func.sum(Order.total_amount), 0.0).label("total_revenue"),
            func.count(Order.id).label("order_count"),
        )
        .filter(Order.region.isnot(None))
        .group_by(Order.region)
        .order_by(func.sum(Order.total_amount).desc())
        .all()
    )

    return [
        RegionPerformance(
            region=row.region,
            total_revenue=row.total_revenue,
            order_count=row.order_count,
        )
        for row in results
    ]


def get_recent_orders(db: Session, limit: int = 10) -> List[RecentOrder]:
    """Return the most recent orders with customer name."""
    results = (
        db.query(Order, Customer.name.label("customer_name"))
        .join(Customer, Order.customer_id == Customer.id)
        .order_by(Order.order_date.desc(), Order.id.desc())
        .limit(limit)
        .all()
    )

    return [
        RecentOrder(
            id=order.id,
            customer_name=customer_name,
            order_date=datetime.combine(order.order_date, datetime.min.time()),
            total_amount=order.total_amount,
            payment_status=order.payment_status,
            shipment_status=order.shipment_status,
        )
        for order, customer_name in results
    ]


def get_alerts(db: Session) -> List[DashboardAlert]:
    """Generate alerts for low stock products, overdue payments, and
    cancelled orders."""
    alerts: List[DashboardAlert] = []

    # Low stock alerts
    low_stock_products = (
        db.query(Product)
        .filter(
            Product.current_stock <= Product.reorder_level,
            Product.status == "active",
        )
        .limit(10)
        .all()
    )
    for product in low_stock_products:
        alerts.append(
            DashboardAlert(
                alert_type="low_stock",
                message=(
                    f"Product '{product.name}' stock ({product.current_stock}) "
                    f"is at or below reorder level ({product.reorder_level})."
                ),
                severity="warning",
                entity_id=product.id,
            )
        )

    # Overdue payment alerts
    overdue_payments = (
        db.query(Payment, Customer.name.label("customer_name"))
        .join(Order, Payment.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(
            Payment.status != "paid",
            Payment.due_date < date.today(),
        )
        .limit(10)
        .all()
    )
    for payment, customer_name in overdue_payments:
        days_overdue = (date.today() - payment.due_date).days
        alerts.append(
            DashboardAlert(
                alert_type="overdue_payment",
                message=(
                    f"Payment for order #{payment.order_id} ({customer_name}) "
                    f"is {days_overdue} days overdue. Amount: {payment.amount}."
                ),
                severity="critical" if days_overdue > 30 else "warning",
                entity_id=payment.order_id,
            )
        )

    # Cancelled order alerts (recent)
    cancelled_orders = (
        db.query(Order, Customer.name.label("customer_name"))
        .join(Customer, Order.customer_id == Customer.id)
        .filter(
            case(
                (Order.payment_status == "cancelled", True),
                (Order.shipment_status == "cancelled", True),
                else_=False,
            )
        )
        .limit(5)
        .all()
    )
    for order, customer_name in cancelled_orders:
        alerts.append(
            DashboardAlert(
                alert_type="cancelled_order",
                message=(
                    f"Order #{order.id} for {customer_name} has been cancelled."
                ),
                severity="info",
                entity_id=order.id,
            )
        )

    return alerts


def _months_ago(months: int) -> date:
    """Return the date N months ago from today."""
    today = date.today()
    month = today.month - months
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    day = min(today.day, 28)  # safe day for any month
    return date(year, month, day)
