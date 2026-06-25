from typing import List, Optional

from pydantic import BaseModel


class AIAskRequest(BaseModel):
    question: str


class AIReportRequest(BaseModel):
    report_type: str = "weekly"
    additional_context: Optional[str] = None


class AITrendRequest(BaseModel):
    metric: str
    period: str = "last_month"


class AIInventoryRequest(BaseModel):
    category: Optional[str] = None


class AIResponse(BaseModel):
    short_answer: str
    data_evidence: List[str]
    reasoning: str
    suggested_actions: List[str]
    confidence: str
