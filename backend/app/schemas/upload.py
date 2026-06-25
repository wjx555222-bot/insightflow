from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class ImportSummary(BaseModel):
    total_rows: int
    success_rows: int
    failed_rows: int
    duplicate_rows: int
    errors: List[str]


class UploadHistoryResponse(BaseModel):
    id: int
    file_type: str
    file_name: str
    total_rows: int
    success_rows: int
    failed_rows: int
    duplicate_rows: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
