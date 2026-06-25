import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.audit_log import UploadHistory
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.product import Product, Supplier
from app.schemas.upload import ImportSummary

logger = logging.getLogger(__name__)

# Column mappings: CSV header -> model attribute
COLUMN_MAPPINGS: Dict[str, Dict[str, str]] = {
    "orders": {
        "order_id": "order_id",
        "customer_id": "customer_id",
        "customer_name": "customer_name",
        "product_id": "product_id",
        "product_name": "product_name",
        "quantity": "quantity",
        "unit_price": "unit_price",
        "order_date": "order_date",
        "region": "region",
        "salesperson": "salesperson",
    },
    "customers": {
        "name": "name",
        "company": "company",
        "email": "email",
        "phone": "phone",
        "region": "region",
        "customer_type": "customer_type",
    },
    "products": {
        "name": "name",
        "category": "category",
        "supplier_name": "supplier_name",
        "unit_price": "unit_price",
        "cost_price": "cost_price",
        "stock": "stock",
    },
    "inventory": {
        "product_name": "product_name",
        "product_id": "product_id",
        "warehouse": "warehouse",
        "quantity": "quantity",
    },
}


def process_csv(
    file_content: bytes,
    file_name: str,
    entity_type: str,
    db: Session,
    user_id: int,
) -> ImportSummary:
    """Process a CSV file and import data into the database.

    Steps:
    1. Read CSV with pandas
    2. Validate columns match expected schema for entity_type
    3. Clean: fill NaN, strip whitespace, standardize types
    4. Detect duplicates based on key columns
    5. Batch insert valid rows
    6. Record in upload_history
    7. Return ImportSummary
    """
    errors: List[str] = []
    total_rows = 0
    success_rows = 0
    failed_rows = 0
    duplicate_rows = 0

    # Validate entity type
    if entity_type not in COLUMN_MAPPINGS:
        return ImportSummary(
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            duplicate_rows=0,
            errors=[f"Unknown entity type: '{entity_type}'. Valid types: {list(COLUMN_MAPPINGS.keys())}"],
        )

    # Step 1: Read CSV
    try:
        df = pd.read_csv(
            pd.io.common.BytesIO(file_content),
            dtype=str,
            keep_default_na=False,
        )
    except Exception as e:
        return ImportSummary(
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            duplicate_rows=0,
            errors=[f"Failed to read CSV file: {str(e)}"],
        )

    if df.empty:
        return ImportSummary(
            total_rows=0,
            success_rows=0,
            failed_rows=0,
            duplicate_rows=0,
            errors=["CSV file is empty."],
        )

    # Step 2: Validate columns
    expected_columns = set(COLUMN_MAPPINGS[entity_type].keys())
    # Normalize column names: lowercase and strip whitespace
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    actual_columns = set(df.columns)

    # Check for required columns (first column in mapping that is a key field)
    missing_columns = expected_columns - actual_columns
    if missing_columns:
        # Only warn about truly required columns (name/id fields)
        required_cols = _get_required_columns(entity_type)
        missing_required = required_cols - actual_columns
        if missing_required:
            return ImportSummary(
                total_rows=0,
                success_rows=0,
                failed_rows=0,
                duplicate_rows=0,
                errors=[
                    f"Missing required columns: {sorted(missing_required)}. "
                    f"Expected columns: {sorted(expected_columns)}"
                ],
            )
        # Warn about optional missing columns but proceed
        if missing_columns:
            errors.append(
                f"Optional columns not found: {sorted(missing_columns - required_cols)}"
            )

    total_rows = len(df)

    # Step 3: Clean data
    df = _clean_dataframe(df, entity_type)

    # Step 4: Detect duplicates
    df, dup_count, dup_errors = _detect_duplicates(df, entity_type)
    duplicate_rows = dup_count
    errors.extend(dup_errors)

    # Step 5: Import rows based on entity type
    try:
        if entity_type == "customers":
            s, f, import_errors = _import_customers(df, db)
        elif entity_type == "products":
            s, f, import_errors = _import_products(df, db)
        elif entity_type == "orders":
            s, f, import_errors = _import_orders(df, db)
        elif entity_type == "inventory":
            s, f, import_errors = _import_inventory(df, db)
        else:
            s, f, import_errors = 0, 0, ["Unknown entity type"]

        success_rows = s
        failed_rows += f
        errors.extend(import_errors)
    except Exception as e:
        logger.error("Import failed: %s", e)
        errors.append(f"Import process error: {str(e)}")
        failed_rows = total_rows - success_rows - duplicate_rows

    # Step 6: Record in upload_history
    try:
        upload_record = UploadHistory(
            user_id=user_id,
            file_type=entity_type,
            file_name=file_name,
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=failed_rows,
            duplicate_rows=duplicate_rows,
            error_messages="\n".join(errors) if errors else None,
        )
        db.add(upload_record)
        db.commit()
    except Exception as e:
        logger.error("Failed to record upload history: %s", e)
        db.rollback()

    # Limit errors list to prevent excessively long responses
    if len(errors) > 50:
        errors = errors[:50] + [f"... and {len(errors) - 50} more errors"]

    return ImportSummary(
        total_rows=total_rows,
        success_rows=success_rows,
        failed_rows=failed_rows,
        duplicate_rows=duplicate_rows,
        errors=errors,
    )


def _get_required_columns(entity_type: str) -> set:
    """Return the set of required columns for each entity type."""
    required = {
        "orders": {"customer_name", "product_name", "quantity", "unit_price"},
        "customers": {"name"},
        "products": {"name", "unit_price"},
        "inventory": {"quantity"},
    }
    return required.get(entity_type, set())


def _clean_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Clean the dataframe: fill NaN, strip whitespace, standardize types."""
    # Strip whitespace from all string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    # Replace empty strings with NaN, then fill with appropriate defaults
    df.replace("", pd.NA, inplace=True)

    # Fill NaN with defaults based on entity type
    if entity_type == "customers":
        df["company"] = df["company"].fillna("")
        df["email"] = df["email"].fillna("")
        df["phone"] = df["phone"].fillna("")
        df["region"] = df["region"].fillna("")
        df["customer_type"] = df["customer_type"].fillna("standard")
    elif entity_type == "products":
        df["category"] = df["category"].fillna("")
        df["supplier_name"] = df["supplier_name"].fillna("")
        df["cost_price"] = df["cost_price"].fillna("0")
        df["stock"] = df["stock"].fillna("0")
    elif entity_type == "orders":
        df["region"] = df["region"].fillna("")
        df["salesperson"] = df["salesperson"].fillna("")
        df["customer_id"] = df["customer_id"].fillna("")
        df["product_id"] = df["product_id"].fillna("")
    elif entity_type == "inventory":
        df["warehouse"] = df["warehouse"].fillna("Main")
        df["product_name"] = df["product_name"].fillna("")
        df["product_id"] = df["product_id"].fillna("")

    return df


def _detect_duplicates(
    df: pd.DataFrame,
    entity_type: str,
) -> tuple:
    """Detect and remove duplicate rows. Returns (cleaned_df, dup_count, errors)."""
    dup_count = 0
    errors = []

    # Determine the key column(s) for duplicate detection
    key_columns_map = {
        "customers": ["name", "email"],
        "products": ["name"],
        "orders": [],  # Orders don't have natural dedup keys in CSV
        "inventory": ["product_id", "product_name", "warehouse"],
    }

    key_columns = key_columns_map.get(entity_type, [])

    if key_columns:
        # Only check duplicates on key columns that exist in the df
        valid_keys = [c for c in key_columns if c in df.columns]
        if valid_keys:
            before_count = len(df)
            df = df.drop_duplicates(subset=valid_keys, keep="first")
            dup_count = before_count - len(df)
            if dup_count > 0:
                errors.append(
                    f"Removed {dup_count} duplicate rows based on columns: {valid_keys}"
                )

    return df, dup_count, errors


def _resolve_customer(
    customer_id_str: str,
    customer_name: str,
    db: Session,
) -> Optional[int]:
    """Resolve a customer by ID or name. Create if not found."""
    # Try by ID first
    if customer_id_str:
        try:
            cid = int(customer_id_str)
            customer = db.query(Customer).filter(Customer.id == cid).first()
            if customer:
                return customer.id
        except (ValueError, TypeError):
            pass

    # Try by name
    if customer_name:
        customer = db.query(Customer).filter(Customer.name == customer_name).first()
        if customer:
            return customer.id
        # Auto-create customer
        customer = Customer(name=customer_name)
        db.add(customer)
        db.flush()
        return customer.id

    return None


def _resolve_product(
    product_id_str: str,
    product_name: str,
    db: Session,
) -> Optional[int]:
    """Resolve a product by ID or name. Return None if not found."""
    # Try by ID first
    if product_id_str:
        try:
            pid = int(product_id_str)
            product = db.query(Product).filter(Product.id == pid).first()
            if product:
                return product.id
        except (ValueError, TypeError):
            pass

    # Try by name
    if product_name:
        product = db.query(Product).filter(Product.name == product_name).first()
        if product:
            return product.id

    return None


def _resolve_supplier(supplier_name: str, db: Session) -> Optional[int]:
    """Resolve a supplier by name. Create if not found."""
    if not supplier_name:
        return None

    supplier = db.query(Supplier).filter(Supplier.name == supplier_name).first()
    if supplier:
        return supplier.id

    # Auto-create supplier
    supplier = Supplier(name=supplier_name)
    db.add(supplier)
    db.flush()
    return supplier.id


def _import_customers(
    df: pd.DataFrame,
    db: Session,
) -> tuple:
    """Import customer records from the cleaned dataframe."""
    success = 0
    failed = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            name = str(row.get("name", "")).strip()
            if not name:
                errors.append(f"Row {idx + 1}: Missing required field 'name'")
                failed += 1
                continue

            # Check for existing customer
            existing = db.query(Customer).filter(Customer.name == name).first()
            if existing:
                # Update existing customer
                for field in ["company", "email", "phone", "region", "customer_type"]:
                    value = row.get(field, "")
                    if value:
                        setattr(existing, field, str(value))
                existing.updated_at = datetime.utcnow()
            else:
                customer = Customer(
                    name=name,
                    company=str(row.get("company", "")) or None,
                    email=str(row.get("email", "")) or None,
                    phone=str(row.get("phone", "")) or None,
                    region=str(row.get("region", "")) or None,
                    customer_type=str(row.get("customer_type", "")) or None,
                )
                db.add(customer)

            success += 1
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    try:
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Database commit failed: {str(e)}")
        failed += success
        success = 0

    return success, failed, errors


def _import_products(
    df: pd.DataFrame,
    db: Session,
) -> tuple:
    """Import product records from the cleaned dataframe."""
    success = 0
    failed = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            name = str(row.get("name", "")).strip()
            if not name:
                errors.append(f"Row {idx + 1}: Missing required field 'name'")
                failed += 1
                continue

            # Parse numeric fields
            try:
                unit_price = float(row.get("unit_price", 0))
            except (ValueError, TypeError):
                errors.append(f"Row {idx + 1}: Invalid unit_price value")
                failed += 1
                continue

            try:
                cost_price = float(row.get("cost_price", 0))
            except (ValueError, TypeError):
                cost_price = 0.0

            try:
                stock = int(float(row.get("stock", 0)))
            except (ValueError, TypeError):
                stock = 0

            # Resolve supplier
            supplier_name = str(row.get("supplier_name", "")).strip()
            supplier_id = _resolve_supplier(supplier_name, db)

            # Check for existing product
            existing = db.query(Product).filter(Product.name == name).first()
            if existing:
                existing.category = str(row.get("category", "")) or existing.category
                existing.supplier_id = supplier_id or existing.supplier_id
                existing.unit_price = unit_price
                existing.cost_price = cost_price
                existing.current_stock = stock
                existing.updated_at = datetime.utcnow()
            else:
                product = Product(
                    name=name,
                    category=str(row.get("category", "")) or None,
                    supplier_id=supplier_id,
                    unit_price=unit_price,
                    cost_price=cost_price,
                    current_stock=stock,
                )
                db.add(product)

            success += 1
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    try:
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Database commit failed: {str(e)}")
        failed += success
        success = 0

    return success, failed, errors


def _import_orders(
    df: pd.DataFrame,
    db: Session,
) -> tuple:
    """Import order records from the cleaned dataframe.

    Each CSV row represents one order line item. Rows with the same
    order_date + customer are grouped into one order.
    """
    success = 0
    failed = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # Resolve customer
            customer_id_str = str(row.get("customer_id", "")).strip()
            customer_name = str(row.get("customer_name", "")).strip()
            customer_id = _resolve_customer(customer_id_str, customer_name, db)
            if not customer_id:
                errors.append(
                    f"Row {idx + 1}: Could not resolve customer "
                    f"(id='{customer_id_str}', name='{customer_name}')"
                )
                failed += 1
                continue

            # Resolve product
            product_id_str = str(row.get("product_id", "")).strip()
            product_name = str(row.get("product_name", "")).strip()
            product_id = _resolve_product(product_id_str, product_name, db)
            if not product_id:
                errors.append(
                    f"Row {idx + 1}: Could not resolve product "
                    f"(id='{product_id_str}', name='{product_name}')"
                )
                failed += 1
                continue

            # Parse numeric fields
            try:
                quantity = int(float(row.get("quantity", 1)))
            except (ValueError, TypeError):
                errors.append(f"Row {idx + 1}: Invalid quantity value")
                failed += 1
                continue

            try:
                unit_price = float(row.get("unit_price", 0))
            except (ValueError, TypeError):
                errors.append(f"Row {idx + 1}: Invalid unit_price value")
                failed += 1
                continue

            # Parse order date
            order_date_str = str(row.get("order_date", "")).strip()
            if order_date_str:
                try:
                    order_date = pd.to_datetime(order_date_str).date()
                except Exception:
                    from datetime import date
                    order_date = date.today()
            else:
                from datetime import date
                order_date = date.today()

            region = str(row.get("region", "")).strip() or None
            salesperson = str(row.get("salesperson", "")).strip() or None

            # Create order
            order = Order(
                customer_id=customer_id,
                order_date=order_date,
                region=region,
                salesperson=salesperson,
                total_amount=quantity * unit_price,
            )
            db.add(order)
            db.flush()

            # Create order item
            item = OrderItem(
                order_id=order.id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )
            db.add(item)

            success += 1
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    try:
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Database commit failed: {str(e)}")
        failed += success
        success = 0

    return success, failed, errors


def _import_inventory(
    df: pd.DataFrame,
    db: Session,
) -> tuple:
    """Import inventory records from the cleaned dataframe."""
    success = 0
    failed = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # Resolve product
            product_id_str = str(row.get("product_id", "")).strip()
            product_name = str(row.get("product_name", "")).strip()

            product_id = None
            if product_id_str:
                try:
                    product_id = int(product_id_str)
                    product = db.query(Product).filter(Product.id == product_id).first()
                    if not product:
                        errors.append(
                            f"Row {idx + 1}: Product ID {product_id} not found"
                        )
                        failed += 1
                        continue
                except (ValueError, TypeError):
                    errors.append(f"Row {idx + 1}: Invalid product_id value")
                    failed += 1
                    continue
            elif product_name:
                product = (
                    db.query(Product).filter(Product.name == product_name).first()
                )
                if product:
                    product_id = product.id
                else:
                    errors.append(
                        f"Row {idx + 1}: Product '{product_name}' not found"
                    )
                    failed += 1
                    continue
            else:
                errors.append(
                    f"Row {idx + 1}: Missing product_id or product_name"
                )
                failed += 1
                continue

            # Parse quantity
            try:
                quantity = int(float(row.get("quantity", 0)))
            except (ValueError, TypeError):
                errors.append(f"Row {idx + 1}: Invalid quantity value")
                failed += 1
                continue

            warehouse = str(row.get("warehouse", "Main")).strip() or "Main"

            # Check for existing inventory record
            existing = (
                db.query(Inventory)
                .filter(Inventory.product_id == product_id)
                .first()
            )
            if existing:
                existing.quantity = quantity
                existing.warehouse = warehouse
                existing.last_updated = datetime.utcnow()
            else:
                inv = Inventory(
                    product_id=product_id,
                    warehouse=warehouse,
                    quantity=quantity,
                )
                db.add(inv)

            success += 1
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            failed += 1

    try:
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        errors.append(f"Database commit failed: {str(e)}")
        failed += success
        success = 0

    return success, failed, errors
