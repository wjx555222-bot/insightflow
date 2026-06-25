"""Products and inventory router with CRUD and stock management."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_db, require_role
from app.models.inventory import Inventory
from app.models.order import OrderItem
from app.models.product import Product, Supplier
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.utils.audit import log_action

router = APIRouter(prefix="/products", tags=["products"])


def _get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _product_to_response(product: Product) -> dict:
    """Convert a Product ORM instance to a ProductResponse-compatible dict."""
    supplier_data = None
    if product.supplier:
        supplier_data = {
            "id": product.supplier.id,
            "name": product.supplier.name,
            "contact_person": product.supplier.contact_person,
            "email": product.supplier.email,
            "phone": product.supplier.phone,
            "address": product.supplier.address,
        }
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "supplier_id": product.supplier_id,
        "unit_price": product.unit_price,
        "cost_price": product.cost_price,
        "current_stock": product.current_stock,
        "reorder_level": product.reorder_level,
        "status": product.status,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "supplier": supplier_data,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Inventory (literal paths BEFORE parameterized /{product_id} routes)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/inventory/low-stock")
def list_low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """List products where current_stock is at or below the reorder level."""
    products = (
        db.query(Product)
        .filter(
            Product.current_stock <= Product.reorder_level,
            Product.status == "active",
        )
        .options(joinedload(Product.supplier))
        .order_by(Product.current_stock.asc())
        .all()
    )

    result = []
    for p in products:
        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "category": p.category,
            "current_stock": p.current_stock,
            "reorder_level": p.reorder_level,
            "supplier_name": p.supplier.name if p.supplier else None,
        })
    return result


@router.get("/inventory")
def list_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """List all inventory records with associated product information."""
    records = (
        db.query(Inventory)
        .options(joinedload(Inventory.product))
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for inv in records:
        result.append({
            "id": inv.id,
            "product_id": inv.product_id,
            "product_name": inv.product.name if inv.product else None,
            "product_category": inv.product.category if inv.product else None,
            "warehouse": inv.warehouse,
            "quantity": inv.quantity,
            "last_updated": inv.last_updated,
        })
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Products CRUD
# ──────────────────────────────────────────────────────────────────────────────

@router.get("")
def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    product_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """List products with optional search by name and filter by category/status."""
    query = db.query(Product).options(joinedload(Product.supplier))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.category.ilike(search_term),
            )
        )

    if category is not None:
        query = query.filter(Product.category == category)

    if product_status is not None:
        query = query.filter(Product.status == product_status)

    total = query.count()
    products = query.order_by(Product.id.desc()).offset(skip).limit(limit).all()
    return {
        "items": [_product_to_response(p) for p in products],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Create a new product. Validates supplier if provided."""
    if payload.supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
        if supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {payload.supplier_id} not found",
            )

    new_product = Product(
        name=payload.name,
        category=payload.category,
        supplier_id=payload.supplier_id,
        unit_price=payload.unit_price,
        cost_price=payload.cost_price or 0.0,
        current_stock=payload.current_stock or 0,
        reorder_level=payload.reorder_level or 10,
        status="active",
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # Also create an inventory record
    inventory = Inventory(
        product_id=new_product.id,
        warehouse="Main",
        quantity=new_product.current_stock,
    )
    db.add(inventory)
    db.commit()

    # Reload with supplier
    product = (
        db.query(Product)
        .options(joinedload(Product.supplier))
        .filter(Product.id == new_product.id)
        .first()
    )

    log_action(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="product",
        entity_id=product.id,
        details=f"Created product {product.name}",
        ip_address=_get_client_ip(request),
    )

    return _product_to_response(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """Get a single product with supplier info. Returns 404 if not found."""
    product = (
        db.query(Product)
        .options(joinedload(Product.supplier))
        .filter(Product.id == product_id)
        .first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return _product_to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Update an existing product's fields. Returns 404 if not found."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    if payload.supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
        if supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {payload.supplier_id} not found",
            )
        product.supplier_id = payload.supplier_id

    if payload.name is not None:
        product.name = payload.name
    if payload.category is not None:
        product.category = payload.category
    if payload.unit_price is not None:
        product.unit_price = payload.unit_price
    if payload.cost_price is not None:
        product.cost_price = payload.cost_price
    if payload.current_stock is not None:
        product.current_stock = payload.current_stock
        # Sync inventory record
        inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        if inv:
            inv.quantity = payload.current_stock
    if payload.reorder_level is not None:
        product.reorder_level = payload.reorder_level

    db.commit()
    db.refresh(product)

    product = (
        db.query(Product)
        .options(joinedload(Product.supplier))
        .filter(Product.id == product.id)
        .first()
    )

    log_action(
        db,
        user_id=current_user.id,
        action="update",
        entity_type="product",
        entity_id=product.id,
        details=f"Updated product {product.name}",
        ip_address=_get_client_ip(request),
    )

    return _product_to_response(product)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Delete a product.

    Checks for existing order items referencing the product. If found, sets
    the product status to 'archived' (soft delete). Otherwise, hard-deletes.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Check for order items referencing this product
    order_item_count = (
        db.query(OrderItem).filter(OrderItem.product_id == product_id).count()
    )

    if order_item_count > 0:
        product.status = "archived"
        db.commit()

        log_action(
            db,
            user_id=current_user.id,
            action="soft_delete",
            entity_type="product",
            entity_id=product.id,
            details=f"Soft-deleted product {product.name} (has {order_item_count} order items)",
            ip_address=_get_client_ip(request),
        )

        return {"detail": f"Product {product_id} soft-deleted (referenced by {order_item_count} order items)"}

    # Remove inventory record
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if inv:
        db.delete(inv)

    db.delete(product)
    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="delete",
        entity_type="product",
        entity_id=product_id,
        details=f"Deleted product {product.name}",
        ip_address=_get_client_ip(request),
    )

    return {"detail": "deleted"}
