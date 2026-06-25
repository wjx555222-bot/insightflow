"""Batch operations router for bulk delete and export."""

from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.models.user import User
from app.models.order import Order
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.utils.audit import log_action

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchDeleteRequest(BaseModel):
    ids: List[int]


class BatchDeleteResponse(BaseModel):
    deleted: int
    failed: int
    errors: List[str] = []


@router.post("/orders/delete", response_model=BatchDeleteResponse)
def batch_delete_orders(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    deleted = 0
    failed = 0
    errors = []
    for oid in payload.ids:
        order = db.query(Order).filter(Order.id == oid).first()
        if order:
            db.delete(order)
            deleted += 1
        else:
            failed += 1
            errors.append(f"Order #{oid} not found")
    db.commit()
    log_action(db, user_id=current_user.id, action="batch_delete", entity_type="order",
               details=f"Batch deleted {deleted} orders", entity_id=None)
    return BatchDeleteResponse(deleted=deleted, failed=failed, errors=errors)


@router.post("/customers/delete", response_model=BatchDeleteResponse)
def batch_delete_customers(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    deleted = 0
    failed = 0
    errors = []
    for cid in payload.ids:
        customer = db.query(Customer).filter(Customer.id == cid).first()
        if customer:
            db.delete(customer)
            deleted += 1
        else:
            failed += 1
            errors.append(f"Customer #{cid} not found")
    db.commit()
    log_action(db, user_id=current_user.id, action="batch_delete", entity_type="customer",
               details=f"Batch deleted {deleted} customers", entity_id=None)
    return BatchDeleteResponse(deleted=deleted, failed=failed, errors=errors)


@router.post("/products/delete", response_model=BatchDeleteResponse)
def batch_delete_products(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    deleted = 0
    failed = 0
    errors = []
    for pid in payload.ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if product:
            # Also delete associated inventory
            inv = db.query(Inventory).filter(Inventory.product_id == pid).first()
            if inv:
                db.delete(inv)
            db.delete(product)
            deleted += 1
        else:
            failed += 1
            errors.append(f"Product #{pid} not found")
    db.commit()
    log_action(db, user_id=current_user.id, action="batch_delete", entity_type="product",
               details=f"Batch deleted {deleted} products", entity_id=None)
    return BatchDeleteResponse(deleted=deleted, failed=failed, errors=errors)
