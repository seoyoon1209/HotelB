from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/reservations", tags=["reservations"])


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


@router.get("/", response_model=list[ReservationResponse])
async def list_reservations(conn: DbPoolDep):
    rows = await conn.fetch("SELECT * FROM reservation ORDER BY reservation_id")
    return [dict(row) for row in rows]


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(reservation_id: int, conn: DbPoolDep):
    row = await conn.fetchrow(
        "SELECT * FROM reservation WHERE reservation_id = $1", reservation_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
    return dict(row)
