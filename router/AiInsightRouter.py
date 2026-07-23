# AI 데모: 연관 요인 분석 / 추천 마케팅 시나리오 (실제 LLM 호출)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.dbpool import DbPoolDep
from ai import insight

router = APIRouter(prefix="/reservations/{reservation_id}/ai-insight", tags=["ai-insight"])

_RESERVATION_INSIGHT_SQL = """
    SELECT
        r.reservation_id,
        r.reservation_code,
        (r.check_in_date - CURRENT_DATE) AS lead_time,
        mt.meal_code,
        ms.segment_name,
        dt.deposit_name,
        lp.cancellation_probability,
        lp.risk_level
    FROM reservation r
    LEFT JOIN meal_type mt ON mt.meal_type_id = r.meal_type_id
    LEFT JOIN market_segment ms ON ms.market_segment_id = r.market_segment_id
    LEFT JOIN deposit_type dt ON dt.deposit_type_id = r.deposit_type_id
    LEFT JOIN LATERAL (
        SELECT risk_level, cancellation_probability
        FROM prediction_result p
        WHERE p.reservation_id = r.reservation_id
        ORDER BY p.predicted_at DESC
        LIMIT 1
    ) lp ON true
    WHERE r.reservation_id = $1
"""


class ScenarioItem(BaseModel):
    title: str
    message: str


class AiInsightResponse(BaseModel):
    factors: list[str]
    scenarios: list[ScenarioItem]
    source: str


@router.get("/", response_model=AiInsightResponse)
async def get_ai_insight(reservation_id: int, conn: DbPoolDep):
    row = await conn.fetchrow(_RESERVATION_INSIGHT_SQL, reservation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")

    try:
        return await insight.get_insight(dict(row))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
