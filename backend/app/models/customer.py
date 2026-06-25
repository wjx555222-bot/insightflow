from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    """Customer record with contact and spending information."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    customer_type = Column(String(50), nullable=True)
    total_spending = Column(Float, default=0.0)
    last_purchase_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}')>"
