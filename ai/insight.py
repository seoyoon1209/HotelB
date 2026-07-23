# Generates the AI demo's "related factor analysis" / "recommended marketing scenarios" with a real LLM (OpenAI).
# To limit cost, calls the LLM only once per reservation and caches the result in memory (assumes WEB_CONCURRENCY=1).
from __future__ import annotations

import json

from openai import AsyncOpenAI
from settings.Settings import get_settings

_client: AsyncOpenAI | None = None
_cache: dict[int, dict] = {}

# Raw code value → readable phrase passed to the LLM (so the output doesn't echo raw codes).
_DEPOSIT_LABEL = {
    "No Deposit": "No Deposit",
    "Non Refund": "Non-Refundable",
    "Refundable": "Refundable",
}
_SEGMENT_LABEL = {
    "OTA": "Online Travel Agency (OTA)",
    "Online TA": "Online Travel Agency (OTA)",
    "Offline TA/TO": "Offline Travel Agency",
    "Groups": "Groups",
    "Direct": "Direct Booking",
    "Corporate": "Corporate",
    "Other": "Other",
}
_MEAL_LABEL = {
    "SC": "No Meals",
    "BB": "Breakfast Included",
    "HB": "Breakfast & Dinner Included",
    "FB": "Breakfast, Lunch & Dinner Included",
}

_SYSTEM_PROMPT = (
    "You are an assistant that analyzes hotel reservation cancellation risk. "
    "Given the reservation attributes, briefly list observation-based factors correlated with the "
    "cancellation risk, and suggest marketing/outreach scenarios that staff could try. "
    "The factors are correlations only, not confirmed causes of cancellation, so do not use wording "
    "that asserts causation. "
    "Respond ONLY in the following JSON format: "
    '{"factors": ["...", "..."], "scenarios": [{"title": "...", "message": "..."}]}. '
    "Provide 2-4 factors and 2-3 scenarios, all in natural, concise English. "
    "Do not use raw code values (e.g. OTA, Direct, Refundable); spell them out in plain English."
)


def _get_client() -> AsyncOpenAI | None:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.openai_api_key:
            return None
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _build_user_prompt(reservation: dict) -> str:
    probability = reservation.get("cancellation_probability")
    probability_text = f"{float(probability) * 100:.0f}%" if probability is not None else "N/A"
    segment = reservation.get("segment_name")
    deposit = reservation.get("deposit_name")
    meal = reservation.get("meal_code")
    return (
        f"Reservation number: {reservation.get('reservation_code')}\n"
        f"Cancellation probability: {probability_text}\n"
        f"Risk level: {reservation.get('risk_level') or 'N/A'}\n"
        f"Days until check-in: {reservation.get('lead_time')}\n"
        f"Market segment: {_SEGMENT_LABEL.get(segment, segment) or 'N/A'}\n"
        f"Deposit type: {_DEPOSIT_LABEL.get(deposit, deposit) or 'N/A'}\n"
        f"Meal type: {_MEAL_LABEL.get(meal, meal) or 'N/A'}"
    )


async def get_insight(reservation: dict) -> dict:
    reservation_id = reservation["reservation_id"]
    if reservation_id in _cache:
        return _cache[reservation_id]

    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    settings = get_settings()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(reservation)},
        ],
    )
    data = json.loads(response.choices[0].message.content)
    result = {
        "factors": data.get("factors", []),
        "scenarios": data.get("scenarios", []),
        "source": "llm",
    }
    _cache[reservation_id] = result
    return result
