"""Upload router for CSV file imports and upload history."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.models.audit_log import UploadHistory
from app.models.user import User
from app.schemas.upload import ImportSummary, UploadHistoryResponse
from app.services import csv_service

router = APIRouter(prefix="/upload", tags=["upload"])


def _validate_csv_file(file: UploadFile) -> bytes:
    """Read and validate the uploaded CSV file. Returns file content as bytes."""
    if file.filename is None or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted",
        )

    content = file.file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    return content


@router.post("/orders", response_model=ImportSummary)
def upload_orders(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Upload and import orders from a CSV file."""
    content = _validate_csv_file(file)
    summary = csv_service.process_csv(
        file_content=content,
        file_name=file.filename,
        entity_type="orders",
        db=db,
        user_id=current_user.id,
    )
    return summary


@router.post("/customers", response_model=ImportSummary)
def upload_customers(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Upload and import customers from a CSV file."""
    content = _validate_csv_file(file)
    summary = csv_service.process_csv(
        file_content=content,
        file_name=file.filename,
        entity_type="customers",
        db=db,
        user_id=current_user.id,
    )
    return summary


@router.post("/products", response_model=ImportSummary)
def upload_products(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Upload and import products from a CSV file."""
    content = _validate_csv_file(file)
    summary = csv_service.process_csv(
        file_content=content,
        file_name=file.filename,
        entity_type="products",
        db=db,
        user_id=current_user.id,
    )
    return summary


@router.post("/inventory", response_model=ImportSummary)
def upload_inventory(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Upload and import inventory records from a CSV file."""
    content = _validate_csv_file(file)
    summary = csv_service.process_csv(
        file_content=content,
        file_name=file.filename,
        entity_type="inventory",
        db=db,
        user_id=current_user.id,
    )
    return summary


@router.get("/history", response_model=List[UploadHistoryResponse])
def get_upload_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "staff")),
):
    """List upload history in reverse chronological order. Paginated."""
    records = (
        db.query(UploadHistory)
        .order_by(UploadHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records
