# reservation 테이블 관련
# 예약 생성/취소, 상태 변경(체크인/체크아웃/노쇼 처리) 등은 아직 없음.
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/reservations", tags=["reservations"])

# 예약 목록/단건 조회 공통 쿼리: 예약별 최신 예측 결과(risk_level, cancellation_probability)를
# LATERAL JOIN으로 붙이고, 시뮬레이터/필터 화면에서 쓰는 호텔·고객·식사·시장구분·보증금 유형의
# 사람이 읽을 수 있는 이름도 함께 붙인다. 예측이 아직 없는 예약은 관련 컬럼이 NULL.
_RESERVATION_WITH_RISK_SQL = """
    SELECT
        r.*,
        h.hotel_name,
        c.customer_name,
        mt.meal_code,
        mt.meal_name,
        ms.segment_code,
        ms.segment_name,
        dt.deposit_code,
        dt.deposit_name,
        dc.channel_code,
        dc.channel_name,
        lp.risk_level,
        lp.cancellation_probability,
        EXISTS (
            SELECT 1 FROM reservation_action ra WHERE ra.reservation_id = r.reservation_id
        ) AS has_action
    FROM reservation r
    JOIN hotel h ON h.hotel_id = r.hotel_id
    LEFT JOIN customer c ON c.customer_id = r.customer_id
    LEFT JOIN meal_type mt ON mt.meal_type_id = r.meal_type_id
    LEFT JOIN market_segment ms ON ms.market_segment_id = r.market_segment_id
    LEFT JOIN deposit_type dt ON dt.deposit_type_id = r.deposit_type_id
    LEFT JOIN distribution_channel dc ON dc.distribution_channel_id = r.distribution_channel_id
    LEFT JOIN LATERAL (
        SELECT p.risk_level, p.cancellation_probability
        FROM prediction_result p
        WHERE p.reservation_id = r.reservation_id
        ORDER BY p.predicted_at DESC
        LIMIT 1
    ) lp ON true
"""


class ReservationResponse(BaseModel):
    reservation_id: int
    reservation_code: str
    hotel_id: int
    hotel_name: str
    customer_id: int | None = None
    customer_name: str | None = None
    room_type_id: int
    booking_date: date
    check_in_date: date
    check_out_date: date
    adult_count: int
    child_count: int
    baby_count: int
    adr: Decimal | None = None
    total_price: Decimal | None = None
    reservation_status: str
    cancelled_at: datetime | None = None
    meal_code: str | None = None
    meal_name: str | None = None
    segment_code: str | None = None
    segment_name: str | None = None
    deposit_code: str | None = None
    deposit_name: str | None = None
    channel_code: str | None = None
    channel_name: str | None = None
    risk_level: str | None = None
    cancellation_probability: Decimal | None = None
    has_action: bool = False


@router.get("/", response_model=list[ReservationResponse])
async def list_reservations(conn: DbPoolDep):
    rows = await conn.fetch(f"{_RESERVATION_WITH_RISK_SQL} ORDER BY r.reservation_id")
    return [dict(row) for row in rows]


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(reservation_id: int, conn: DbPoolDep):
    row = await conn.fetchrow(
        f"{_RESERVATION_WITH_RISK_SQL} WHERE r.reservation_id = $1", reservation_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
    return dict(row)
