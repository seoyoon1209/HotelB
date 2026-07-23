# AI 데모의 "연관 요인 분석"/"추천 마케팅 시나리오"를 실제 LLM(OpenAI)으로 생성.
# 호출 비용 때문에 예약 하나당 한 번만 호출하고 결과를 메모리에 캐싱한다(WEB_CONCURRENCY=1 전제).
from __future__ import annotations

import json

from openai import AsyncOpenAI
from settings.Settings import get_settings

_client: AsyncOpenAI | None = None
_cache: dict[int, dict] = {}

# 원본 코드값 → LLM에 전달할 한글 표현 (출력이 영어 코드를 그대로 뱉지 않도록).
_DEPOSIT_LABEL = {
    "No Deposit": "보증금 없음",
    "Non Refund": "환불 불가",
    "Refundable": "환불 가능",
}
_SEGMENT_LABEL = {
    "OTA": "온라인 여행사(OTA)",
    "Online TA": "온라인 여행사(OTA)",
    "Offline TA/TO": "오프라인 여행사",
    "Groups": "단체",
    "Direct": "직접 예약",
    "Corporate": "기업",
    "Other": "기타",
}
_MEAL_LABEL = {
    "SC": "조식 미포함",
    "BB": "조식 포함",
    "HB": "조식·석식 포함",
    "FB": "조식·중식·석식 포함",
}

_SYSTEM_PROMPT = (
    "너는 호텔 예약 취소 위험을 분석하는 어시스턴트다. "
    "주어진 예약 속성을 보고 취소 위험과 연관된 요인을 관찰 사실 위주로 짧게 나열하고, "
    "직원이 시도해볼 만한 마케팅/응대 시나리오를 제안해라. "
    "요인은 상관관계일 뿐 확정된 취소 원인이 아니므로 인과관계를 단정하는 표현은 쓰지 마라. "
    "반드시 아래 JSON 형식으로만 답하라: "
    '{"factors": ["...", "..."], "scenarios": [{"title": "...", "message": "..."}]}. '
    "factors는 2~4개, scenarios는 2~3개, 모두 자연스러운 한국어로 간결하게. "
    "영어 코드값(예: OTA, Direct, Refundable)을 그대로 쓰지 말고 한국어 표현으로 풀어서 써라."
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
    probability_text = f"{float(probability) * 100:.0f}%" if probability is not None else "정보 없음"
    segment = reservation.get("segment_name")
    deposit = reservation.get("deposit_name")
    meal = reservation.get("meal_code")
    return (
        f"예약번호: {reservation.get('reservation_code')}\n"
        f"취소 확률: {probability_text}\n"
        f"위험도: {reservation.get('risk_level') or '정보 없음'}\n"
        f"체크인까지 남은 일수: {reservation.get('lead_time')}일\n"
        f"시장 세그먼트: {_SEGMENT_LABEL.get(segment, segment) or '정보 없음'}\n"
        f"보증금 유형: {_DEPOSIT_LABEL.get(deposit, deposit) or '정보 없음'}\n"
        f"식사 유형: {_MEAL_LABEL.get(meal, meal) or '정보 없음'}"
    )


async def get_insight(reservation: dict) -> dict:
    reservation_id = reservation["reservation_id"]
    if reservation_id in _cache:
        return _cache[reservation_id]

    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

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
