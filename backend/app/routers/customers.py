"""Customers router with CRUD, search, filter, and related-order retrieval."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_role
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.order import OrderListResponse
from app.utils.audit import log_action

router = APIRouter(prefix="/customers", tags=["customers"])


def _get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("")
def list_customers(
    search: Optional[str] = None,
    region: Optional[str] = None,
    customer_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """List customers with optional search and filter. Paginated."""
    query = db.query(Customer)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.company.ilike(search_term),
            )
        )

    if region is not None:
        query = query.filter(Customer.region == region)

    if customer_type is not None:
        query = query.filter(Customer.customer_type == customer_type)

    total = query.count()
    customers = query.order_by(Customer.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": c.id, "name": c.name, "company": c.company,
                "email": c.email, "phone": c.phone, "region": c.region,
                "customer_type": c.customer_type, "total_spending": c.total_spending or 0.0,
                "last_purchase_date": c.last_purchase_date,
                "created_at": c.created_at, "updated_at": c.updated_at,
            }
            for c in customers
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """Get a single customer by ID. Returns 404 if not found."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found",
        )
    return customer


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Create a new customer record."""
    new_customer = Customer(
        name=payload.name,
        company=payload.company,
        email=payload.email,
        phone=payload.phone,
        region=payload.region,
        customer_type=payload.customer_type,
        total_spending=0.0,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    log_action(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="customer",
        entity_id=new_customer.id,
        details=f"Created customer {new_customer.name}",
        ip_address=_get_client_ip(request),
    )

    return new_customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Update an existing customer's fields. Returns 404 if not found."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found",
        )

    if payload.name is not None:
        customer.name = payload.name
    if payload.company is not None:
        customer.company = payload.company
    if payload.email is not None:
        customer.email = payload.email
    if payload.phone is not None:
        customer.phone = payload.phone
    if payload.region is not None:
        customer.region = payload.region
    if payload.customer_type is not None:
        customer.customer_type = payload.customer_type

    db.commit()
    db.refresh(customer)

    log_action(
        db,
        user_id=current_user.id,
        action="update",
        entity_type="customer",
        entity_id=customer.id,
        details=f"Updated customer {customer.name}",
        ip_address=_get_client_ip(request),
    )

    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Delete a customer.

    If the customer has associated orders, performs a soft delete by marking
    the customer_type as 'archived'.  Otherwise, hard-deletes the record.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found",
        )

    order_count = db.query(Order).filter(Order.customer_id == customer_id).count()
    if order_count > 0:
        # Soft delete: mark as archived instead of removing
        customer.customer_type = "archived"
        db.commit()

        log_action(
            db,
            user_id=current_user.id,
            action="soft_delete",
            entity_type="customer",
            entity_id=customer.id,
            details=f"Soft-deleted customer {customer.name} (has {order_count} orders)",
            ip_address=_get_client_ip(request),
        )

        return {"detail": f"Customer {customer_id} soft-deleted (has {order_count} existing orders)"}

    db.delete(customer)
    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="delete",
        entity_type="customer",
        entity_id=customer_id,
        details=f"Deleted customer {customer.name}",
        ip_address=_get_client_ip(request),
    )

    return {"detail": "deleted"}


@router.get("/{customer_id}/orders", response_model=List[OrderListResponse])
def get_customer_orders(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """Return all orders for a specific customer. Returns 404 if customer not found."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found",
        )

    orders = (
        db.query(Order)
        .options(joinedload(Order.customer))
        .filter(Order.customer_id == customer_id)
        .order_by(Order.order_date.desc())
        .all()
    )

    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": customer.name,
            "order_date": order.order_date,
            "payment_status": order.payment_status,
            "shipment_status": order.shipment_status,
            "region": order.region,
            "salesperson": order.salesperson,
            "total_amount": order.total_amount,
        })
    return result
