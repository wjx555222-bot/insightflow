import json
import logging
from datetime import date, timedelta
from typing import Optional

from openai import OpenAI
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.customer import Customer
from app.models.inventory import Payment
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.ai import AIResponse

logger = logging.getLogger(__name__)

# Lazy-initialized OpenAI client
_client: Optional[OpenAI] = None

SYSTEM_PROMPT = """You are a professional business analyst AI assistant for InsightFlow, an enterprise sales management platform.

RULES:
1. ONLY use the data provided in the context. NEVER fabricate or hallucinate numbers.
2. If the data is insufficient, say so explicitly rather than guessing.
3. Structure your response as a JSON object with exactly these fields:
   - "short_answer": A concise 1-2 sentence direct answer
   - "data_evidence": A list of specific data points that support your answer
   - "reasoning": A clear explanation of your analysis logic
   - "suggested_actions": A list of 2-4 actionable recommendations
   - "confidence": One of "high", "medium", or "low" based on data completeness

Always be professional, data-driven, and actionable in your recommendations."""


def _get_client() -> OpenAI:
    """Get or create the OpenAI client."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _build_business_context(db: Session) -> str:
    """Fetch key business metrics to provide as context for AI queries."""
    # Revenue summary
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0)).scalar()
    )
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0

    # Recent monthly revenue
    recent_month_start = date.today().replace(day=1)
    monthly_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
        .filter(Order.order_date >= recent_month_start)
        .scalar()
    )

    # Top products
    top_products = (
        db.query(
            Product.name,
            func.sum(OrderItem.total).label("revenue"),
            func.sum(OrderItem.quantity).label("qty"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .group_by(Product.name)
        .order_by(func.sum(OrderItem.total).desc())
        .limit(5)
        .all()
    )

    # Region breakdown
    regions = (
        db.query(
            Order.region,
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("count"),
        )
        .filter(Order.region.isnot(None))
        .group_by(Order.region)
        .order_by(func.sum(Order.total_amount).desc())
        .limit(5)
        .all()
    )

    # Payment status breakdown
    payment_statuses = (
        db.query(
            Order.payment_status,
            func.count(Order.id).label("count"),
            func.sum(Order.total_amount).label("total"),
        )
        .group_by(Order.payment_status)
        .all()
    )

    # Low stock products
    low_stock = (
        db.query(Product.name, Product.current_stock, Product.reorder_level)
        .filter(
            Product.current_stock <= Product.reorder_level,
            Product.status == "active",
        )
        .limit(5)
        .all()
    )

    context_parts = [
        f"BUSINESS CONTEXT (as of {date.today().isoformat()}):",
        f"- Total Revenue: ${total_revenue:,.2f}",
        f"- Total Orders: {total_orders}",
        f"- Total Customers: {total_customers}",
        f"- Total Products: {total_products}",
        f"- This Month Revenue: ${monthly_revenue:,.2f}",
    ]

    if top_products:
        context_parts.append("\nTop Products by Revenue:")
        for p in top_products:
            context_parts.append(
                f"  - {p.name}: ${p.revenue:,.2f} ({p.qty} units)"
            )

    if regions:
        context_parts.append("\nRevenue by Region:")
        for r in regions:
            context_parts.append(
                f"  - {r.region}: ${r.revenue:,.2f} ({r.count} orders)"
            )

    if payment_statuses:
        context_parts.append("\nPayment Status Breakdown:")
        for ps in payment_statuses:
            context_parts.append(
                f"  - {ps.payment_status}: {ps.count} orders (${ps.total:,.2f})"
            )

    if low_stock:
        context_parts.append("\nLow Stock Alerts:")
        for ls in low_stock:
            context_parts.append(
                f"  - {ls.name}: stock={ls.current_stock}, "
                f"reorder_level={ls.reorder_level}"
            )

    return "\n".join(context_parts)


def _call_openai(user_message: str, context: str) -> AIResponse:
    """Call OpenAI API with the system prompt and parse the response."""
    client = _get_client()

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Context:\n{context}\n\n"
                        f"Question: {user_message}\n\n"
                        "Respond in the required JSON format."
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return AIResponse(
            short_answer=data.get("short_answer", "No analysis available."),
            data_evidence=data.get("data_evidence", []),
            reasoning=data.get("reasoning", ""),
            suggested_actions=data.get("suggested_actions", []),
            confidence=data.get("confidence", "low"),
        )

    except json.JSONDecodeError as e:
        logger.error("Failed to parse AI response as JSON: %s", e)
        return AIResponse(
            short_answer="The AI response could not be parsed. Please try again.",
            data_evidence=[],
            reasoning=f"JSON parse error: {str(e)}",
            suggested_actions=["Retry the request"],
            confidence="low",
        )
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        return AIResponse(
            short_answer="An error occurred while generating the analysis.",
            data_evidence=[],
            reasoning=f"API error: {str(e)}",
            suggested_actions=[
                "Check your OpenAI API key configuration",
                "Retry the request",
            ],
            confidence="low",
        )


def ask_question(
    db: Session,
    question: str,
    user=None,
) -> AIResponse:
    """Answer a free-form business question using available data.

    1. Fetch relevant analytics data from db
    2. Build structured context with the data
    3. Call OpenAI with system prompt defining the AI as a business analyst
    4. Parse response into AIResponse format
    """
    context = _build_business_context(db)
    return _call_openai(question, context)


def generate_report(
    db: Session,
    report_type: str = "weekly",
    additional_context: Optional[str] = None,
) -> AIResponse:
    """Generate a structured business report (weekly, monthly, quarterly)."""
    context = _build_business_context(db)

    report_prompts = {
        "weekly": (
            "Generate a weekly business performance report. "
            "Focus on key metrics, notable trends, and immediate action items."
        ),
        "monthly": (
            "Generate a monthly business performance report. "
            "Include revenue analysis, customer insights, product performance, "
            "and strategic recommendations for the next month."
        ),
        "quarterly": (
            "Generate a quarterly business performance report. "
            "Provide a comprehensive analysis of revenue trends, growth metrics, "
            "regional performance, and strategic recommendations."
        ),
    }

    prompt = report_prompts.get(
        report_type,
        f"Generate a {report_type} business report.",
    )

    if additional_context:
        prompt += f"\n\nAdditional context from user: {additional_context}"

    return _call_openai(prompt, context)


def explain_trend(
    db: Session,
    metric: str,
    period: str = "last_month",
) -> AIResponse:
    """Explain a trend for a specific metric over a given period."""
    context = _build_business_context(db)

    prompt = (
        f"Analyze the trend for the '{metric}' metric over the period '{period}'. "
        f"Explain what is driving the trend, whether it is positive or concerning, "
        f"and what actions should be taken."
    )

    return _call_openai(prompt, context)


def suggest_inventory(
    db: Session,
    category: Optional[str] = None,
) -> AIResponse:
    """Provide AI-driven inventory management recommendations."""
    context = _build_business_context(db)

    # Add inventory-specific data
    query = db.query(
        Product.name,
        Product.category,
        Product.current_stock,
        Product.reorder_level,
        Product.unit_price,
        Product.cost_price,
    )
    if category:
        query = query.filter(Product.category == category)

    products = query.limit(50).all()

    if products:
        inv_lines = ["\nInventory Details:"]
        for p in products:
            status = (
                "LOW STOCK"
                if p.current_stock <= p.reorder_level
                else "OK"
            )
            inv_lines.append(
                f"  - {p.name} [{p.category or 'N/A'}]: "
                f"stock={p.current_stock}, reorder_level={p.reorder_level}, "
                f"price=${p.unit_price:.2f}, status={status}"
            )
        context += "\n".join(inv_lines)

    prompt = (
        "Based on the current inventory data, provide specific recommendations "
        "for stock management. Identify which products need reordering, which are "
        "overstocked, and suggest optimal reorder quantities. "
        "Consider product value and stock turnover."
    )

    if category:
        prompt += f" Focus specifically on the '{category}' category."

    return _call_openai(prompt, context)
