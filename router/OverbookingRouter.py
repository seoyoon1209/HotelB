# 오버부킹 지원
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from math import floor

from fastapi import APIRouter, Query
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/overbooking", tags=["overbooking"])

_OVERBOOKING_SUMMARY_SQL = """
    WITH latest_prediction AS (
        SELECT DISTINCT ON (reservation_id)
            reservation_id, cancellation_probability, risk_level
        FROM prediction_result
        ORDER BY reservation_id, predicted_at DESC
    )
    SELECT
        r.check_in_date,
        COUNT(*) AS total_reservations,
        COALESCE(SUM(lp.cancellation_probability), 0) AS expected_cancellations,
        COUNT(*) FILTER (WHERE lp.risk_level IN ('HIGH', 'CRITICAL')) AS high_risk_count
    FROM reservation r
    LEFT JOIN latest_prediction lp ON lp.reservation_id = r.reservation_id
    WHERE r.check_in_date BETWEEN $1 AND $2
      AND r.reservation_status NOT IN ('CANCELLED', 'NO_SHOW')
    GROUP BY r.check_in_date
    ORDER BY r.check_in_date
"""


class OverbookingSummaryResponse(BaseModel):
    check_in_date: date
    total_reservations: int
    expected_cancellations: Decimal
    high_risk_count: int
    recommended_additional_bookings: int


@router.get("/summary", response_model=list[OverbookingSummaryResponse])
async def get_overbooking_summary(
    conn: DbPoolDep,
    date_from: date = Query(default_factory=date.today),
    date_to: date | None = Query(default=None),
):
    if date_to is None:
        date_to = date_from + timedelta(days=30)

    rows = await conn.fetch(_OVERBOOKING_SUMMARY_SQL, date_from, date_to)
    return [
        {
            **dict(row),
            "recommended_additional_bookings": floor(row["expected_cancellations"]),
        }
        for row in rows
    ]
