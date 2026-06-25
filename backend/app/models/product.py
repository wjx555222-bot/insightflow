from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Supplier(Base):
    """Product supplier with contact details."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)

    products = relationship("Product", back_populates="supplier")

    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name='{self.name}')>"


class Product(Base):
    """Product catalog entry with pricing and stock information."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    unit_price = Column(Float, nullable=False, default=0.0)
    cost_price = Column(Float, nullable=False, default=0.0)
    current_stock = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}')>"
