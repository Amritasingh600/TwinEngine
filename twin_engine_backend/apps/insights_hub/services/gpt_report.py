"""
Azure GPT-4o Report Generator Service.

Pipeline:
  1. Receives raw operational data dict from data_collector
  2. Builds a structured prompt for GPT-4o
  3. Sends to Azure OpenAI endpoint
  4. Parses the response into:  executive_summary, insights[], recommendations[]

Returns structured text that the PDF builder can render.
"""

import json
import logging

from django.conf import settings
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# ── Azure OpenAI client (singleton-style) ──
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
    return _client


# ── System prompt ──
SYSTEM_PROMPT = """You are TwinEngine AI — an expert hospitality operations analyst.
You will receive raw operational data from a restaurant outlet (orders, payments,
table utilisation, inventory, staff, etc.).

Your job is to produce a professional executive operations report with:

1. **Executive Summary** — 3-5 paragraph overview of the day/period. Include key
   highlights, concerns, and overall performance assessment. Use actual numbers
   from the data. Be specific, not generic.

2. **Key Insights** — Return exactly 6-8 bullet-point insights. Each must reference
   a specific metric or data point. Examples: peak hour performance, wait time
   trends, top-selling items, payment method distribution, staffing adequacy.

3. **Recommendations** — Return exactly 4-6 actionable recommendations based on the
   data. Be concrete (e.g., "Add 1 waiter during 7-9 PM to reduce average wait
   time from 18 to 12 minutes").

IMPORTANT FORMATTING RULES:
- Use plain text, NOT markdown.  No # headings, no ** bold **, no bullet markers.
- For the executive summary: write natural paragraphs separated by blank lines.
- For insights: return a JSON array of strings.
- For recommendations: return a JSON array of strings.
- Use the Indian Rupee symbol (₹) for all currency values.
- Always reference actual numbers from the data provided.

Return your response as a JSON object with exactly these keys:
{
    "executive_summary": "string (multi-paragraph plain text)",
    "insights": ["string", "string", ...],
    "recommendations": ["string", "string", ...]
}

Return ONLY valid JSON. No extra text outside the JSON.
"""


def generate_report_with_gpt(raw_data: dict) -> dict:
    """
    Call Azure GPT-4o with raw operational data and return structured report.

    Args:
        raw_data: dict from data_collector.collect_raw_data()

    Returns:
        {
            "executive_summary": str,
            "insights": list[str],
            "recommendations": list[str],
            "model_used": str,
        }
    """
    client = _get_client()
    deployment = settings.AZURE_OPENAI_DEPLOYMENT

    # Build the user message with the raw data
    user_message = (
        f"Generate an operations report for this restaurant data.\n\n"
        f"DATA:\n{json.dumps(raw_data, indent=2, default=str)}"
    )

    logger.info(
        "Sending %d chars of data to GPT-4o (deployment: %s)",
        len(user_message), deployment,
    )

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content.strip()
        model_used = response.model or deployment

        logger.info("GPT-4o responded (%d chars), model: %s", len(content), model_used)

        # Parse the JSON response
        parsed = json.loads(content)

        return {
            "executive_summary": parsed.get("executive_summary", "Report generation incomplete."),
            "insights": parsed.get("insights", []),
            "recommendations": parsed.get("recommendations", []),
            "model_used": model_used,
        }

    except json.JSONDecodeError as e:
        logger.error("GPT-4o returned invalid JSON: %s", e)
        # Fallback: use the raw text as the summary
        return {
            "executive_summary": content if 'content' in dir() else "Failed to parse GPT-4o response.",
            "insights": ["Report parsing error — raw response could not be structured."],
            "recommendations": ["Retry report generation or check Azure OpenAI configuration."],
            "model_used": deployment,
        }
    except Exception as e:
        logger.error("GPT-4o API call failed: %s", e)
        raise


def generate_report_fallback(raw_data: dict) -> dict:
    """
    Fallback report generation when GPT-4o is unavailable.
    Uses the raw data to produce a basic structured report.
    """
    order_summary = raw_data.get("order_summary", {})
    payment_summary = raw_data.get("payment_summary", {})
    outlet_info = raw_data.get("outlet_info", {})
    period = raw_data.get("report_period", {})
    inventory = raw_data.get("inventory_summary", {})
    tables = raw_data.get("table_overview", {})

    total_revenue = order_summary.get("total_revenue", 0) or 0
    total_orders = order_summary.get("total_orders", 0) or 0
    total_guests = order_summary.get("total_guests", 0) or 0
    avg_wait = order_summary.get("avg_wait_minutes", 0) or 0
    avg_ticket = order_summary.get("avg_ticket", 0) or 0
    status_bd = order_summary.get("status_breakdown", {})

    completed = status_bd.get("COMPLETED", 0)
    cancelled = status_bd.get("CANCELLED", 0)
    total_tips = payment_summary.get("total_tips", 0) or 0

    executive_summary = (
        f"Operations Report for {outlet_info.get('name', 'Outlet')} "
        f"({outlet_info.get('brand', '')}) — {outlet_info.get('city', '')}.\n\n"
        f"Period: {period.get('start_date', '')} to {period.get('end_date', '')}.\n\n"
        f"The outlet processed {total_orders} orders generating a total revenue of "
        f"Rs.{total_revenue:,.2f} and serving {total_guests} guests. "
        f"The average ticket size was Rs.{avg_ticket:,.2f} "
        f"and the average wait time was {avg_wait:.1f} minutes.\n\n"
        f"{completed} orders were completed successfully"
        f"{f' while {cancelled} were cancelled' if cancelled else ''}. "
        f"Total tips collected: Rs.{total_tips:,.2f}.\n\n"
        f"{'Wait times are within acceptable limits.' if avg_wait < 15 else 'Wait times exceeded the 15-minute threshold — staffing review recommended.'}"
    )

    insights = [
        f"Total revenue: Rs.{total_revenue:,.2f} from {total_orders} orders.",
        f"Average ticket size: Rs.{avg_ticket:,.2f}.",
        f"Average wait time: {avg_wait:.1f} minutes.",
        f"Guest count: {total_guests}.",
        f"Tables available: {tables.get('total_tables', 'N/A')} with capacity {tables.get('total_capacity', 'N/A')}.",
        f"Inventory items low on stock: {inventory.get('low_stock_count', 0)}.",
    ]

    recommendations = []
    if avg_wait > 15:
        recommendations.append(
            "Average wait time exceeds 15 minutes. Consider adding staff during peak hours."
        )
    if cancelled > 0:
        recommendations.append(
            f"{cancelled} orders were cancelled. Review cancellation reasons to reduce waste."
        )
    if inventory.get("low_stock_count", 0) > 0:
        low_items = [i['name'] for i in inventory.get("low_stock_items", [])]
        recommendations.append(
            f"Restock low inventory items: {', '.join(low_items[:5])}."
        )
    recommendations.append("Review top-selling items to ensure menu optimisation.")
    if total_tips < total_revenue * 0.05:
        recommendations.append(
            "Tip collection is below 5% of revenue. Consider staff incentive programmes."
        )

    return {
        "executive_summary": executive_summary,
        "insights": insights,
        "recommendations": recommendations,
        "model_used": "fallback-local",
    }
