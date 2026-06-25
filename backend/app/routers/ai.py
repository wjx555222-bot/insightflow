"""AI router providing OpenAI-powered analysis and reporting endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.audit_log import AIReport
from app.models.user import User
from app.schemas.ai import (
    AIAskRequest,
    AIInventoryRequest,
    AIReportRequest,
    AIResponse,
    AITrendRequest,
)
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


def _save_ai_interaction(
    db: Session,
    user_id: int,
    report_type: str,
    question: str,
    response: AIResponse,
    data_context: str = None,
) -> None:
    """Persist an AI interaction to the ai_reports table for audit/history."""
    report = AIReport(
        user_id=user_id,
        report_type=report_type,
        question=question,
        response=response.short_answer,
        data_context=data_context,
    )
    db.add(report)
    db.commit()


@router.post("/ask", response_model=AIResponse)
def ask_question(
    payload: AIAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a free-form business question and get an AI-powered answer.

    The interaction is saved to ai_reports for future reference.
    """
    response = ai_service.ask_question(
        db=db,
        question=payload.question,
        user=current_user,
    )

    _save_ai_interaction(
        db,
        user_id=current_user.id,
        report_type="ask",
        question=payload.question,
        response=response,
    )

    return response


@router.post("/generate-report", response_model=AIResponse)
def generate_report(
    payload: AIReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a structured business report (weekly, monthly, quarterly).

    The interaction is saved to ai_reports for future reference.
    """
    response = ai_service.generate_report(
        db=db,
        report_type=payload.report_type,
        additional_context=payload.additional_context,
    )

    _save_ai_interaction(
        db,
        user_id=current_user.id,
        report_type="generate_report",
        question=f"Generate {payload.report_type} report",
        response=response,
        data_context=payload.additional_context,
    )

    return response


@router.post("/explain-trend", response_model=AIResponse)
def explain_trend(
    payload: AITrendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an AI explanation of a trend for a specific metric and period.

    The interaction is saved to ai_reports for future reference.
    """
    response = ai_service.explain_trend(
        db=db,
        metric=payload.metric,
        period=payload.period,
    )

    _save_ai_interaction(
        db,
        user_id=current_user.id,
        report_type="explain_trend",
        question=f"Explain trend for {payload.metric} over {payload.period}",
        response=response,
    )

    return response


@router.post("/inventory-suggestion", response_model=AIResponse)
def suggest_inventory(
    payload: AIInventoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-driven inventory management recommendations.

    Optionally scoped to a specific product category.
    The interaction is saved to ai_reports for future reference.
    """
    response = ai_service.suggest_inventory(
        db=db,
        category=payload.category,
    )

    _save_ai_interaction(
        db,
        user_id=current_user.id,
        report_type="inventory_suggestion",
        question=f"Inventory suggestions for category: {payload.category or 'all'}",
        response=response,
        data_context=payload.category,
    )

    return response
