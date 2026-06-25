from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """Immutable log of user actions for security and compliance auditing."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"


class UploadHistory(Base):
    """Record of file uploads including row counts and error details."""

    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_name = Column(String(500), nullable=False)
    total_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    error_messages = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<UploadHistory(id={self.id}, file_name='{self.file_name}')>"


class SalesTarget(Base):
    """Regional sales target for a given period."""

    __tablename__ = "sales_targets"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    period = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<SalesTarget(id={self.id}, region='{self.region}', period='{self.period}')>"


class AIReport(Base):
    """Stored AI-generated report or analysis response."""

    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    data_context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AIReport(id={self.id}, report_type='{self.report_type}')>"
