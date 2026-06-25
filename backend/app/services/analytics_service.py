from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.audit_log import SalesTarget
from app.models.customer import Customer
from app.models.inventory import Payment
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.analytics import (
    CustomerRepeatRate,
    GrowthAnalytics,
    MonthRevenue,
    PaymentDelay,
    ProductPerformance,
    RegionPerformance,
    RevenueAnalytics,
    SalesTargetStatus,
)


def get_revenue_analytics(
    db: Session,
    year: Optional[int] = None,
) -> RevenueAnalytics:
    """Return monthly revenue data, optionally filtered to a specific year."""
    target_year = year or date.today().year

    results = (
        db.query(
            func.date_trunc("month", Order.order_date).label("month"),
            func.coalesce(func.sum(Order.total_amount), 0.0).label("revenue"),
        )
        .filter(func.extract("year", Order.order_date) == target_year)
        .group_by(func.date_trunc("month", Order.order_date))
        .order_by(func.date_trunc("month", Order.order_date))
        .all()
    )

    monthly_data = [
        MonthRevenue(
            month=row.month.strftime("%Y-%m"),
            revenue=row.revenue,
        )
        for row in results
    ]

    total_revenue = sum(m.revenue for m in monthly_data)

    # Average order value across all orders in the year
    avg_order_value = (
        db.query(func.coalesce(func.avg(Order.total_amount), 0.0))
        .filter(func.extract("year", Order.order_date) == target_year)
        .scalar()
    )

    return RevenueAnalytics(
        monthly_data=monthly_data,
        total_revenue=total_revenue,
        avg_order_value=avg_order_value,
    )


def get_growth_analytics(
    db: Session,
    period: str = "monthly",
) -> GrowthAnalytics:
    """Compare revenue between the current and previous period.

    period: 'monthly' compares this month vs last month,
            'quarterly' compares this quarter vs last quarter,
            'yearly' compares this year vs last year.
    """
    today = date.today()

    if period == "yearly":
        current_start = date(today.year, 1, 1)
        previous_start = date(today.year - 1, 1, 1)
        previous_end = date(today.year - 1, 12, 31)
    elif period == "quarterly":
        current_quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        current_start = date(today.year, current_quarter_start_month, 1)
        prev_quarter_end = current_start - timedelta(days=1)
        prev_quarter_start_month = ((prev_quarter_end.month - 1) // 3) * 3 + 1
        previous_start = date(prev_quarter_end.year, prev_quarter_start_month, 1)
        previous_end = prev_quarter_end
    else:
        # monthly (default)
        current_start = date(today.year, today.month, 1)
        previous_end = current_start - timedelta(days=1)
        previous_start = date(previous_end.year, previous_end.month, 1)

    current_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(Order.order_date >= current_start, Order.order_date <= today)
        .scalar()
    )

    previous_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(
            Order.order_date >= previous_start,
            Order.order_date <= previous_end,
        )
        .scalar()
    )

    growth_amount = current_revenue - previous_revenue
    if previous_revenue > 0:
        growth_rate = (growth_amount / previous_revenue) * 100
    else:
        growth_rate = 100.0 if current_revenue > 0 else 0.0

    return GrowthAnalytics(
        current_period_revenue=current_revenue,
        previous_period_revenue=previous_revenue,
        growth_rate=round(growth_rate, 2),
        growth_amount=round(growth_amount, 2),
    )


def get_customer_repeat_rate(db: Session) -> CustomerRepeatRate:
    """Calculate the ratio of customers with more than one order."""
    total_customers = db.query(func.count(Customer.id)).scalar() or 0

    # Customers with 2+ orders
    repeat_customers = (
        db.query(func.count(func.distinct(Order.customer_id)))
        .group_by(Order.customer_id)
        .having(func.count(Order.id) > 1)
    )
    repeat_count = repeat_customers.count()

    repeat_rate = (
        round((repeat_count / total_customers) * 100, 2)
        if total_customers > 0
        else 0.0
    )

    return CustomerRepeatRate(
        repeat_customers=repeat_count,
        total_customers=total_customers,
        repeat_rate=repeat_rate,
    )


def get_product_performance(
    db: Session,
    category: Optional[str] = None,
) -> List[ProductPerformance]:
    """Return product-level revenue, quantity, and profit margin,
    optionally filtered by category."""
    query = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.coalesce(Product.category, "Uncategorized").label("category"),
            func.coalesce(func.sum(OrderItem.total), 0.0).label("total_revenue"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
            Product.unit_price,
            Product.cost_price,
        )
        .outerjoin(OrderItem, Product.id == OrderItem.product_id)
        .group_by(
            Product.id,
            Product.name,
            Product.category,
            Product.unit_price,
            Product.cost_price,
        )
    )

    if category:
        query = query.filter(Product.category == category)

    results = query.order_by(func.sum(OrderItem.total).desc()).all()

    performances = []
    for row in results:
        # Profit margin calculation
        if row.unit_price and row.unit_price > 0 and row.cost_price is not None:
            profit_margin = round(
                ((row.unit_price - row.cost_price) / row.unit_price) * 100, 2
            )
        else:
            profit_margin = 0.0

        performances.append(
            ProductPerformance(
                product_id=row.product_id,
                product_name=row.product_name,
                category=row.category,
                total_revenue=row.total_revenue,
                total_quantity=row.total_quantity,
                profit_margin=profit_margin,
            )
        )

    return performances


def get_region_performance(db: Session) -> List[RegionPerformance]:
    """Return revenue, order count, and avg order value grouped by region."""
    results = (
        db.query(
            Order.region,
            func.coalesce(func.sum(Order.total_amount), 0.0).label("revenue"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.avg(Order.total_amount), 0.0).label("avg_order_value"),
        )
        .filter(Order.region.isnot(None))
        .group_by(Order.region)
        .order_by(func.sum(Order.total_amount).desc())
        .all()
    )

    return [
        RegionPerformance(
            region=row.region,
            revenue=row.revenue,
            orders=row.orders,
            avg_order_value=round(row.avg_order_value, 2),
        )
        for row in results
    ]


def get_payment_delay(db: Session) -> List[PaymentDelay]:
    """Return orders with overdue payments and the number of days overdue."""
    results = (
        db.query(
            Payment.order_id,
            Customer.name.label("customer_name"),
            Payment.amount,
            Payment.due_date,
        )
        .join(Order, Payment.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(
            Payment.status != "paid",
            Payment.due_date.isnot(None),
            Payment.due_date < date.today(),
        )
        .order_by(Payment.due_date.asc())
        .all()
    )

    today = date.today()
    return [
        PaymentDelay(
            order_id=row.order_id,
            customer_name=row.customer_name,
            amount=row.amount,
            due_date=row.due_date,
            days_overdue=(today - row.due_date).days,
        )
        for row in results
    ]


def get_sales_targets(
    db: Session,
    year: Optional[int] = None,
) -> List[SalesTargetStatus]:
    """Compare actual regional revenue against sales targets."""
    target_year = year or date.today().year

    # Get targets for the year
    targets = (
        db.query(SalesTarget)
        .filter(SalesTarget.year == target_year)
        .all()
    )

    if not targets:
        return []

    # Get actual revenue by region for the year
    actual_revenue = dict(
        db.query(
            Order.region,
            func.coalesce(func.sum(Order.total_amount), 0.0),
        )
        .filter(func.extract("year", Order.order_date) == target_year)
        .group_by(Order.region)
        .all()
    )

    # Aggregate targets by region (sum monthly targets if present)
    region_targets = {}
    for target in targets:
        region_targets[target.region] = (
            region_targets.get(target.region, 0.0) + target.target_amount
        )

    statuses = []
    for region, target_amount in region_targets.items():
        actual = actual_revenue.get(region, 0.0)
        completion_rate = (
            round((actual / target_amount) * 100, 2)
            if target_amount > 0
            else 0.0
        )
        statuses.append(
            SalesTargetStatus(
                region=region,
                target=target_amount,
                actual=actual,
                completion_rate=completion_rate,
            )
        )

    return statuses
