from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Inventory(Base):
    """Warehouse inventory level for a specific product."""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    warehouse = Column(String(100), default="Main", nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, product_id={self.product_id}, qty={self.quantity})>"


class Payment(Base):
    """Payment record associated with an order."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    method = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id={self.order_id}, amount={self.amount})>"


class Shipment(Base):
    """Shipment tracking record for an order."""

    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    carrier = Column(String(255), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    shipped_date = Column(Date, nullable=True)
    delivered_date = Column(Date, nullable=True)

    order = relationship("Order")

    def __repr__(self) -> str:
        return f"<Shipment(id={self.id}, order_id={self.order_id}, status='{self.status}')>"
