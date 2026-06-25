"""Orders router with CRUD, search, filter, and sort capabilities."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_role
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.utils.audit import log_action

router = APIRouter(prefix="/orders", tags=["orders"])


def _get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _build_order_response(order: Order) -> dict:
    """Build an OrderResponse-compatible dict from an Order ORM instance."""
    customer_name = order.customer.name if order.customer else None
    items = []
    for item in order.items:
        product_name = item.product.name if item.product else None
        items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item.total,
        })
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "customer_name": customer_name,
        "order_date": order.order_date,
        "payment_status": order.payment_status,
        "shipment_status": order.shipment_status,
        "region": order.region,
        "salesperson": order.salesperson,
        "total_amount": order.total_amount,
        "items": items,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _build_order_list_response(order: Order) -> dict:
    """Build an OrderListResponse-compatible dict from an Order ORM instance."""
    customer_name = order.customer.name if order.customer else None
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "customer_name": customer_name,
        "order_date": order.order_date,
        "payment_status": order.payment_status,
        "shipment_status": order.shipment_status,
        "region": order.region,
        "salesperson": order.salesperson,
        "total_amount": order.total_amount,
    }


@router.get("")
def list_orders(
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_status: Optional[str] = None,
    shipment_status: Optional[str] = None,
    region: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """List orders with search, filter, sort, and pagination.

    Search matches against customer name, product name (via items), and order ID.
    Sort supports 'date', 'amount', and 'status'.
    Returns a paginated envelope: {items, total, skip, limit}.
    """
    query = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .distinct()
    )

    # Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Order.id.cast(str).ilike(search_term),
                Order.salesperson.ilike(search_term),
                Order.region.ilike(search_term),
                Order.items.any(
                    OrderItem.product.has(Product.name.ilike(search_term))
                ),
            )
        )

    # Filters
    if date_from is not None:
        query = query.filter(Order.order_date >= date_from)
    if date_to is not None:
        query = query.filter(Order.order_date <= date_to)
    if payment_status is not None:
        query = query.filter(Order.payment_status == payment_status)
    if shipment_status is not None:
        query = query.filter(Order.shipment_status == shipment_status)
    if region is not None:
        query = query.filter(Order.region == region)

    # Count before pagination
    total = query.count()

    # Sorting
    if sort_by == "date":
        order_col = Order.order_date.desc() if sort_order == "desc" else Order.order_date.asc()
    elif sort_by == "amount":
        order_col = Order.total_amount.desc() if sort_order == "desc" else Order.total_amount.asc()
    elif sort_by == "status":
        order_col = Order.payment_status.asc() if sort_order == "asc" else Order.payment_status.desc()
    else:
        order_col = Order.id.desc() if sort_order == "desc" else Order.id.asc()

    orders = query.order_by(order_col).offset(skip).limit(limit).all()

    items = [_build_order_list_response(o) for o in orders]

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """Get a single order with its line items. Returns 404 if not found."""
    order = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )
    return _build_order_response(order)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Create a new order with line items.

    Total amount is calculated from the items.  The customer's total_spending
    is updated to reflect the new order.
    """
    # Validate customer exists
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {payload.customer_id} not found",
        )

    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item",
        )

    # Calculate total and validate products
    total_amount = 0.0
    order_items_data = []
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} not found",
            )
        item_total = item.quantity * item.unit_price
        total_amount += item_total
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item_total,
        })

    # Create order
    order = Order(
        customer_id=payload.customer_id,
        region=payload.region,
        salesperson=payload.salesperson,
        payment_status=payload.payment_status or "pending",
        shipment_status=payload.shipment_status or "pending",
        total_amount=total_amount,
    )
    db.add(order)
    db.flush()

    # Create order items
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total=item_data["total"],
        )
        db.add(order_item)

    # Update customer spending
    customer.total_spending = (customer.total_spending or 0.0) + total_amount
    customer.last_purchase_date = order.order_date

    db.commit()

    # Reload with relationships
    db.refresh(order)
    order = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )

    log_action(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="order",
        entity_id=order.id,
        details=f"Created order #{order.id} for customer {customer.name}, total: {total_amount}",
        ip_address=_get_client_ip(request),
    )

    return _build_order_response(order)


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Update an existing order's mutable fields. Returns 404 if not found."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )

    if payload.customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {payload.customer_id} not found",
            )
        order.customer_id = payload.customer_id

    if payload.region is not None:
        order.region = payload.region
    if payload.salesperson is not None:
        order.salesperson = payload.salesperson
    if payload.payment_status is not None:
        order.payment_status = payload.payment_status
    if payload.shipment_status is not None:
        order.shipment_status = payload.shipment_status

    db.commit()
    db.refresh(order)

    order = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order.id)
        .first()
    )

    log_action(
        db,
        user_id=current_user.id,
        action="update",
        entity_type="order",
        entity_id=order.id,
        details=f"Updated order #{order.id}",
        ip_address=_get_client_ip(request),
    )

    return _build_order_response(order)


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Delete an order and all its line items. Returns 404 if not found."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )

    # Reverse customer spending adjustment
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if customer and order.total_amount:
        customer.total_spending = max(0.0, (customer.total_spending or 0.0) - order.total_amount)

    db.delete(order)
    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="delete",
        entity_type="order",
        entity_id=order_id,
        details=f"Deleted order #{order_id}",
        ip_address=_get_client_ip(request),
    )

    return {"detail": "deleted"}
