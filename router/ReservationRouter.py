# reservation 테이블 관련
# 예약 생성/취소, 상태 변경(체크인/체크아웃/노쇼 처리) 등은 아직 없음.
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/reservations", tags=["reservations"])

# 예약 목록/단건 조회 공통 쿼리: 예약별 최신 예측 결과(risk_level, cancellation_probability)를
# LATERAL JOIN으로 붙인다. 예측이 아직 없는 예약은 두 컬럼 다 NULL.
_RESERVATION_WITH_RISK_SQL = """
    SELECT r.*, lp.risk_level, lp.cancellation_probability
    FROM reservation r
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
    customer_id: int | None = None
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
    risk_level: str | None = None
    cancellation_probability: Decimal | None = None


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
