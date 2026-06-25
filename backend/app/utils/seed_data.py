"""
InsightFlow seed data generator.

Run from the backend directory with:
    python -m app.utils.seed_data

Creates realistic demo data for development and testing purposes.
"""

import random
import uuid
from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Local imports — these work when invoked via `python -m app.utils.seed_data`
# from the backend directory.
# ---------------------------------------------------------------------------
from app.database import SessionLocal, engine
from app.models.user import Role, User
from app.models.customer import Customer
from app.models.product import Product, Supplier
from app.models.order import Order, OrderItem
from app.models.inventory import Inventory, Payment, Shipment
from app.models.audit_log import SalesTarget
from app.services.auth_service import hash_password

# Ensure tables exist before seeding
from app.database import Base
import app.models  # noqa: F401 — registers all models with Base.metadata

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Static seed data definitions
# ---------------------------------------------------------------------------

ROLES = [
    {"name": "admin", "permissions": "all"},
    {"name": "manager", "permissions": "read,write,analytics,reports"},
    {"name": "staff", "permissions": "read,write"},
]

USERS = [
    {
        "email": "admin@insightflow.com",
        "full_name": "Admin User",
        "role_name": "admin",
    },
    {
        "email": "manager@insightflow.com",
        "full_name": "Sarah Mitchell",
        "role_name": "manager",
    },
    {
        "email": "staff1@insightflow.com",
        "full_name": "James Rodriguez",
        "role_name": "staff",
    },
    {
        "email": "staff2@insightflow.com",
        "full_name": "Emily Zhang",
        "role_name": "staff",
    },
    {
        "email": "analyst@insightflow.com",
        "full_name": "Michael Park",
        "role_name": "manager",
    },
]

DEFAULT_PASSWORD = "password123"

SUPPLIERS = [
    {
        "name": "TechSource Global",
        "contact_person": "Richard Lee",
        "email": "sales@techsourceglobal.com",
        "phone": "+1-415-555-0101",
        "address": "200 Tech Plaza, San Francisco, CA 94105",
    },
    {
        "name": "OfficeMax Supplies Co.",
        "contact_person": "Jennifer Adams",
        "email": "orders@officemax-supplies.com",
        "phone": "+1-212-555-0202",
        "address": "450 Commerce Ave, New York, NY 10001",
    },
    {
        "name": "Comfort Living Furniture",
        "contact_person": "Thomas Chen",
        "email": "wholesale@comfortliving.com",
        "phone": "+1-312-555-0303",
        "address": "88 Design District, Chicago, IL 60607",
    },
    {
        "name": "FreshHarvest Foods Inc.",
        "contact_person": "Maria Gonzalez",
        "email": "bulk@freshharvestfoods.com",
        "phone": "+1-305-555-0404",
        "address": "1200 Agri Park, Miami, FL 33101",
    },
    {
        "name": "StyleCraft Apparel Group",
        "contact_person": "Daniel Kim",
        "email": "b2b@stylecraftapparel.com",
        "phone": "+1-213-555-0505",
        "address": "750 Fashion Blvd, Los Angeles, CA 90015",
    },
]

CUSTOMERS = [
    {
        "name": "Walmart Retail Corp",
        "company": "Walmart Inc.",
        "email": "procurement@walmart-corp.example.com",
        "phone": "+1-479-555-1001",
        "region": "North",
        "customer_type": "retail",
    },
    {
        "name": "Best Buy Wholesale",
        "company": "Best Buy Co. Inc.",
        "email": "wholesale@bestbuy.example.com",
        "phone": "+1-612-555-1002",
        "region": "South",
        "customer_type": "wholesale",
    },
    {
        "name": "Amazon Enterprise Solutions",
        "company": "Amazon.com Inc.",
        "email": "enterprise@amazon-solutions.example.com",
        "phone": "+1-206-555-1003",
        "region": "East",
        "customer_type": "enterprise",
    },
    {
        "name": "Target Distribution Center",
        "company": "Target Corporation",
        "email": "supply@target-dist.example.com",
        "phone": "+1-651-555-1004",
        "region": "West",
        "customer_type": "retail",
    },
    {
        "name": "Costco Wholesale Partners",
        "company": "Costco Wholesale Corp.",
        "email": "vendor@costco.example.com",
        "phone": "+1-425-555-1005",
        "region": "Central",
        "customer_type": "wholesale",
    },
    {
        "name": "Home Depot Procurement",
        "company": "The Home Depot Inc.",
        "email": "buy@homedepot-proc.example.com",
        "phone": "+1-770-555-1006",
        "region": "North",
        "customer_type": "retail",
    },
    {
        "name": "Staples Business Advantage",
        "company": "Staples Inc.",
        "email": "biz@staples-advantage.example.com",
        "phone": "+1-508-555-1007",
        "region": "South",
        "customer_type": "enterprise",
    },
    {
        "name": "Kroger Food Markets",
        "company": "The Kroger Co.",
        "email": "supply@kroger-markets.example.com",
        "phone": "+1-513-555-1008",
        "region": "East",
        "customer_type": "retail",
    },
    {
        "name": "Macy's Department Store",
        "company": "Macy's Inc.",
        "email": "vendor@macys-dept.example.com",
        "phone": "+1-513-555-1009",
        "region": "West",
        "customer_type": "wholesale",
    },
    {
        "name": "FedEx Logistics Corp",
        "company": "FedEx Corporation",
        "email": "procurement@fedex-logistics.example.com",
        "phone": "+1-901-555-1010",
        "region": "Central",
        "customer_type": "enterprise",
    },
]

PRODUCTS = [
    # Electronics — supplier: TechSource Global (index 0)
    {"name": "Wireless Bluetooth Headphones", "category": "Electronics", "supplier_idx": 0, "unit_price": 79.99, "cost_price": 35.00, "reorder_level": 20},
    {"name": "USB-C Hub Adapter 7-in-1", "category": "Electronics", "supplier_idx": 0, "unit_price": 45.99, "cost_price": 18.00, "reorder_level": 30},
    {"name": "27-inch LED Monitor 4K", "category": "Electronics", "supplier_idx": 0, "unit_price": 299.99, "cost_price": 150.00, "reorder_level": 10},
    # Office Supplies — supplier: OfficeMax (index 1)
    {"name": "Premium A4 Paper (500 sheets)", "category": "Office Supplies", "supplier_idx": 1, "unit_price": 12.99, "cost_price": 5.00, "reorder_level": 100},
    {"name": "Ergonomic Mesh Office Chair", "category": "Office Supplies", "supplier_idx": 1, "unit_price": 189.99, "cost_price": 80.00, "reorder_level": 15},
    {"name": "Desk Organizer Set Bamboo", "category": "Office Supplies", "supplier_idx": 1, "unit_price": 29.99, "cost_price": 12.00, "reorder_level": 40},
    # Furniture — supplier: Comfort Living (index 2)
    {"name": "Electric Standing Desk 60-inch", "category": "Furniture", "supplier_idx": 2, "unit_price": 449.99, "cost_price": 200.00, "reorder_level": 8},
    {"name": "3-Drawer Steel Filing Cabinet", "category": "Furniture", "supplier_idx": 2, "unit_price": 129.99, "cost_price": 55.00, "reorder_level": 12},
    {"name": "12-Person Conference Table", "category": "Furniture", "supplier_idx": 2, "unit_price": 799.99, "cost_price": 350.00, "reorder_level": 3},
    # Food & Beverage — supplier: FreshHarvest (index 3)
    {"name": "Organic Arabica Coffee Beans 1kg", "category": "Food & Beverage", "supplier_idx": 3, "unit_price": 24.99, "cost_price": 10.00, "reorder_level": 50},
    {"name": "Premium Japanese Green Tea 100-bag", "category": "Food & Beverage", "supplier_idx": 3, "unit_price": 15.99, "cost_price": 6.00, "reorder_level": 60},
    {"name": "Protein Bar Variety Pack (24 ct)", "category": "Food & Beverage", "supplier_idx": 3, "unit_price": 34.99, "cost_price": 14.00, "reorder_level": 40},
    # Clothing — supplier: StyleCraft (index 4)
    {"name": "Business Casual Blazer", "category": "Clothing", "supplier_idx": 4, "unit_price": 89.99, "cost_price": 35.00, "reorder_level": 25},
    {"name": "100% Cotton Dress Shirt", "category": "Clothing", "supplier_idx": 4, "unit_price": 49.99, "cost_price": 18.00, "reorder_level": 35},
    {"name": "Performance Polo Shirt Moisture-Wicking", "category": "Clothing", "supplier_idx": 4, "unit_price": 29.99, "cost_price": 11.00, "reorder_level": 50},
]

REGIONS = ["North", "South", "East", "West", "Central"]
SALESPERSONS = ["Alice Chen", "Bob Smith", "Carol Wang", "David Kim", "Eve Johnson"]
PAYMENT_METHODS = ["credit_card", "bank_transfer", "check", "cash", "net30"]
CARRIERS = ["FedEx Express", "UPS Ground", "USPS Priority", "DHL Express", "Amazon Logistics"]

SALES_TARGETS = [
    {"region": "North", "target_amount": 150000.0, "period": "quarterly", "year": 2025, "month": None},
    {"region": "South", "target_amount": 120000.0, "period": "quarterly", "year": 2025, "month": None},
    {"region": "East", "target_amount": 180000.0, "period": "quarterly", "year": 2025, "month": None},
    {"region": "West", "target_amount": 140000.0, "period": "quarterly", "year": 2025, "month": None},
    {"region": "Central", "target_amount": 160000.0, "period": "quarterly", "year": 2025, "month": None},
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _random_date_in_last_n_months(n_months: int = 12) -> date:
    """Return a random date within the last n_months."""
    today = date.today()
    start = today - timedelta(days=n_months * 30)
    delta = (today - start).days
    return start + timedelta(days=random.randint(0, delta))


def _generate_tracking_number() -> str:
    """Generate a pseudo tracking number."""
    return f"TRK{uuid.uuid4().hex[:12].upper()}"


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_roles(db: Session) -> dict:
    """Create roles and return a name -> Role mapping."""
    print("  Creating roles...")
    role_map = {}
    for role_data in ROLES:
        role = Role(**role_data)
        db.add(role)
        role_map[role_data["name"]] = role
    db.flush()
    print(f"    -> {len(role_map)} roles created")
    return role_map


def seed_users(db: Session, role_map: dict) -> List[User]:
    """Create users with hashed passwords."""
    print("  Creating users...")
    users = []
    hashed = hash_password(DEFAULT_PASSWORD)
    for user_data in USERS:
        user = User(
            email=user_data["email"],
            hashed_password=hashed,
            full_name=user_data["full_name"],
            role_id=role_map[user_data["role_name"]].id,
            is_active=True,
        )
        db.add(user)
        users.append(user)
    db.flush()
    print(f"    -> {len(users)} users created (password: {DEFAULT_PASSWORD})")
    return users


def seed_suppliers(db: Session) -> List[Supplier]:
    """Create supplier records."""
    print("  Creating suppliers...")
    suppliers = []
    for s in SUPPLIERS:
        supplier = Supplier(**s)
        db.add(supplier)
        suppliers.append(supplier)
    db.flush()
    print(f"    -> {len(suppliers)} suppliers created")
    return suppliers


def seed_customers(db: Session) -> List[Customer]:
    """Create customer records."""
    print("  Creating customers...")
    customers = []
    for c in CUSTOMERS:
        customer = Customer(
            name=c["name"],
            company=c["company"],
            email=c["email"],
            phone=c["phone"],
            region=c["region"],
            customer_type=c["customer_type"],
            total_spending=0.0,
        )
        db.add(customer)
        customers.append(customer)
    db.flush()
    print(f"    -> {len(customers)} customers created")
    return customers


def seed_products(db: Session, suppliers: List[Supplier]) -> List[Product]:
    """Create products linked to suppliers."""
    print("  Creating products...")
    products = []
    for p in PRODUCTS:
        product = Product(
            name=p["name"],
            category=p["category"],
            supplier_id=suppliers[p["supplier_idx"]].id,
            unit_price=p["unit_price"],
            cost_price=p["cost_price"],
            current_stock=random.randint(50, 500),
            reorder_level=p["reorder_level"],
            status="active",
        )
        db.add(product)
        products.append(product)
    db.flush()
    print(f"    -> {len(products)} products created")
    return products


def seed_orders(
    db: Session,
    customers: List[Customer],
    products: List[Product],
) -> List[Order]:
    """Create 50 orders with 1-4 line items each over the last 12 months."""
    print("  Creating orders (50 orders with items)...")
    orders = []
    today = date.today()

    for i in range(50):
        customer = random.choice(customers)
        region = random.choice(REGIONS)
        salesperson = random.choice(SALESPERSONS)
        order_date = _random_date_in_last_n_months(12)

        # Determine payment status based on order age
        days_ago = (today - order_date).days
        if days_ago < 30:
            payment_status = random.choices(
                ["paid", "pending", "overdue"],
                weights=[60, 35, 5],
                k=1,
            )[0]
        elif days_ago < 90:
            payment_status = random.choices(
                ["paid", "pending", "overdue"],
                weights=[80, 15, 5],
                k=1,
            )[0]
        else:
            payment_status = random.choices(
                ["paid", "pending", "overdue"],
                weights=[92, 5, 3],
                k=1,
            )[0]

        # Determine shipment status based on payment and age
        if payment_status == "paid" and days_ago > 7:
            shipment_status = random.choices(
                ["delivered", "shipped", "pending"],
                weights=[80, 15, 5],
                k=1,
            )[0]
        elif payment_status == "paid":
            shipment_status = random.choices(
                ["shipped", "pending", "preparing"],
                weights=[50, 40, 10],
                k=1,
            )[0]
        else:
            shipment_status = random.choices(
                ["pending", "preparing"],
                weights=[70, 30],
                k=1,
            )[0]

        order = Order(
            customer_id=customer.id,
            order_date=order_date,
            payment_status=payment_status,
            shipment_status=shipment_status,
            region=region,
            salesperson=salesperson,
            total_amount=0.0,
        )
        db.add(order)
        db.flush()  # get order.id

        # Generate 1-4 line items
        num_items = random.randint(1, 4)
        selected_products = random.sample(products, min(num_items, len(products)))
        total_amount = 0.0

        for product in selected_products:
            quantity = random.randint(1, 20)
            # Occasionally adjust price slightly (bulk discount or market variation)
            price_variation = random.uniform(0.90, 1.05)
            unit_price = round(product.unit_price * price_variation, 2)
            item_total = round(unit_price * quantity, 2)
            total_amount += item_total

            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )
            db.add(item)

        order.total_amount = round(total_amount, 2)

        # Update customer total spending and last purchase date
        customer.total_spending = (customer.total_spending or 0.0) + order.total_amount
        if customer.last_purchase_date is None or order_date > customer.last_purchase_date.date():
            customer.last_purchase_date = datetime.combine(order_date, datetime.min.time())

        orders.append(order)

    db.flush()
    print(f"    -> {len(orders)} orders created with line items")
    return orders


def seed_inventory(db: Session, products: List[Product]) -> None:
    """Create inventory records for all products."""
    print("  Creating inventory records...")
    count = 0
    for product in products:
        inv = Inventory(
            product_id=product.id,
            warehouse="Main",
            quantity=product.current_stock,
        )
        db.add(inv)
        count += 1
    db.flush()
    print(f"    -> {count} inventory records created")


def seed_sales_targets(db: Session) -> None:
    """Create regional sales targets."""
    print("  Creating sales targets...")
    for t in SALES_TARGETS:
        target = SalesTarget(**t)
        db.add(target)
    db.flush()
    print(f"    -> {len(SALES_TARGETS)} sales targets created")


def seed_payments(db: Session, orders: List[Order]) -> None:
    """Create payment records for all orders."""
    print("  Creating payment records...")
    count = 0

    for order in orders:
        method = random.choice(PAYMENT_METHODS)
        due_date = order.order_date + timedelta(days=30)

        if order.payment_status == "paid":
            status = "completed"
            paid_date = order.order_date + timedelta(days=random.randint(1, 25))
        elif order.payment_status == "overdue":
            status = "overdue"
            paid_date = None
        else:
            status = "pending"
            paid_date = None

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            method=method,
            status=status,
            due_date=due_date,
            paid_date=paid_date,
        )
        db.add(payment)
        count += 1

    db.flush()
    print(f"    -> {count} payment records created")


def seed_shipments(db: Session, orders: List[Order]) -> None:
    """Create shipment records for orders that have progressed beyond 'preparing'."""
    print("  Creating shipment records...")
    count = 0

    for order in orders:
        if order.shipment_status in ("pending", "preparing"):
            continue

        carrier = random.choice(CARRIERS)
        tracking = _generate_tracking_number()

        if order.shipment_status == "delivered":
            shipped_date = order.order_date + timedelta(days=random.randint(1, 5))
            delivered_date = shipped_date + timedelta(days=random.randint(2, 10))
            status = "delivered"
        elif order.shipment_status == "shipped":
            shipped_date = order.order_date + timedelta(days=random.randint(1, 5))
            delivered_date = None
            status = "in_transit"
        else:
            shipped_date = None
            delivered_date = None
            status = "pending"

        shipment = Shipment(
            order_id=order.id,
            carrier=carrier,
            tracking_number=tracking,
            status=status,
            shipped_date=shipped_date,
            delivered_date=delivered_date,
        )
        db.add(shipment)
        count += 1

    db.flush()
    print(f"    -> {count} shipment records created")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_seed() -> None:
    """Main seed function — checks for existing data then creates all records."""
    print("=" * 60)
    print("InsightFlow — Seed Data Generator")
    print("=" * 60)

    db: Session = SessionLocal()

    try:
        # ------------------------------------------------------------------
        # Guard: skip if database already has data
        # ------------------------------------------------------------------
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"\nDatabase already contains {existing_users} user(s).")
            print("Seeding skipped to avoid duplicate data.")
            print("To re-seed, drop all tables or use an empty database.")
            return

        print("\nSeeding database...")

        # ------------------------------------------------------------------
        # Create data in foreign-key order
        # ------------------------------------------------------------------
        role_map = seed_roles(db)
        users = seed_users(db, role_map)
        suppliers = seed_suppliers(db)
        customers = seed_customers(db)
        products = seed_products(db, suppliers)
        orders = seed_orders(db, customers, products)
        seed_inventory(db, products)
        seed_sales_targets(db)
        seed_payments(db, orders)
        seed_shipments(db, orders)

        # ------------------------------------------------------------------
        # Final commit
        # ------------------------------------------------------------------
        db.commit()

        print("\n" + "=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60)
        print(f"  Roles:        {db.query(Role).count()}")
        print(f"  Users:        {db.query(User).count()}")
        print(f"  Suppliers:    {db.query(Supplier).count()}")
        print(f"  Customers:    {db.query(Customer).count()}")
        print(f"  Products:     {db.query(Product).count()}")
        print(f"  Orders:       {db.query(Order).count()}")
        print(f"  Order Items:  {db.query(OrderItem).count()}")
        print(f"  Inventory:    {db.query(Inventory).count()}")
        print(f"  Sales Targets:{db.query(SalesTarget).count()}")
        print(f"  Payments:     {db.query(Payment).count()}")
        print(f"  Shipments:    {db.query(Shipment).count()}")
        print()
        print("Login credentials (all passwords: password123):")
        print("  admin@insightflow.com    — Admin")
        print("  manager@insightflow.com  — Manager")
        print("  staff1@insightflow.com   — Staff")
        print("  staff2@insightflow.com   — Staff")
        print("  analyst@insightflow.com  — Manager (Analyst)")
        print()

    except Exception as exc:
        db.rollback()
        print(f"\nSeeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
