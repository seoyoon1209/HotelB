# reservation_action
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/reservations/{reservation_id}/actions", tags=["reservation-actions"])
report_router = APIRouter(prefix="/actions/report", tags=["reservation-actions"])
export_router = APIRouter(prefix="/actions/export", tags=["reservation-actions"])


class ReservationActionCreate(BaseModel):
    discount_percent: int
    breakfast_coupon: bool
    probability_before: float
    probability_after: float
    label_before: str
    label_after: str


class ReservationActionResponse(BaseModel):
    action_id: int
    reservation_id: int
    discount_percent: int
    breakfast_coupon: bool
    probability_before: Decimal
    probability_after: Decimal
    label_before: str
    label_after: str
    applied_at: datetime


@router.post("/", response_model=ReservationActionResponse, status_code=201)
async def create_action(reservation_id: int, payload: ReservationActionCreate, conn: DbPoolDep):
    reservation = await conn.fetchrow(
        "SELECT reservation_id FROM reservation WHERE reservation_id = $1", reservation_id
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")

    if payload.label_before not in ("CANCEL", "KEEP") or payload.label_after not in ("CANCEL", "KEEP"):
        raise HTTPException(status_code=422, detail="label은 CANCEL 또는 KEEP이어야 합니다.")

    row = await conn.fetchrow(
        """
        INSERT INTO reservation_action (
            reservation_id, discount_percent, breakfast_coupon,
            probability_before, probability_after, label_before, label_after
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        reservation_id,
        payload.discount_percent,
        payload.breakfast_coupon,
        payload.probability_before,
        payload.probability_after,
        payload.label_before,
        payload.label_after,
    )
    return dict(row)


@router.get("/", response_model=list[ReservationActionResponse])
async def list_actions(reservation_id: int, conn: DbPoolDep):
    rows = await conn.fetch(
        "SELECT * FROM reservation_action WHERE reservation_id = $1 ORDER BY applied_at DESC",
        reservation_id,
    )
    return [dict(row) for row in rows]


@router.delete("/", status_code=204)
async def delete_actions(reservation_id: int, conn: DbPoolDep):
    reservation = await conn.fetchrow(
        "SELECT reservation_id FROM reservation WHERE reservation_id = $1", reservation_id
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")

    await conn.execute("DELETE FROM reservation_action WHERE reservation_id = $1", reservation_id)


class ActionReportRow(BaseModel):
    period_start: str
    period_end: str
    actions_taken: int
    label_flipped: int


@report_router.get("/", response_model=list[ActionReportRow])
async def get_action_report(conn: DbPoolDep, weeks: int = Query(default=4, ge=1, le=52)):
    rows = await conn.fetch(
        """
        SELECT
            date_trunc('week', applied_at)::date AS period_start,
            (date_trunc('week', applied_at) + interval '6 days')::date AS period_end,
            COUNT(*) AS actions_taken,
            COUNT(*) FILTER (WHERE label_before = 'CANCEL' AND label_after = 'KEEP') AS label_flipped
        FROM reservation_action
        WHERE applied_at >= now() - ($1 * interval '1 week')
        GROUP BY 1, 2
        ORDER BY 1 DESC
        """,
        weeks,
    )
    return [
        {
            "period_start": str(row["period_start"]),
            "period_end": str(row["period_end"]),
            "actions_taken": row["actions_taken"],
            "label_flipped": row["label_flipped"],
        }
        for row in rows
    ]


class ActionExportRow(BaseModel):
    consulted: bool
    applied_at: datetime | None = None
    reservation_code: str
    customer_name: str | None = None
    hotel_name: str | None = None
    check_in_date: date
    adr: Decimal
    nights: int
    adult_count: int
    child_count: int
    baby_count: int
    discount_percent: int | None = None
    breakfast_coupon: bool | None = None
    probability_before: Decimal | None = None
    probability_after: Decimal | None = None
    label_before: str | None = None
    label_after: str | None = None


@export_router.get("/", response_model=list[ActionExportRow])
async def get_action_export(conn: DbPoolDep):
    rows = await conn.fetch(
        """
        SELECT
            (ra.action_id IS NOT NULL) AS consulted,
            ra.applied_at,
            r.reservation_code,
            c.customer_name,
            h.hotel_name,
            r.check_in_date,
            r.adr,
            (r.check_out_date - r.check_in_date) AS nights,
            r.adult_count,
            r.child_count,
            r.baby_count,
            ra.discount_percent,
            ra.breakfast_coupon,
            ra.probability_before,
            ra.probability_after,
            ra.label_before,
            ra.label_after
        FROM reservation r
        JOIN customer c ON c.customer_id = r.customer_id
        LEFT JOIN hotel h ON h.hotel_id = r.hotel_id
        LEFT JOIN LATERAL (
            SELECT * FROM reservation_action a
            WHERE a.reservation_id = r.reservation_id
            ORDER BY a.applied_at DESC
            LIMIT 1
        ) ra ON true
        ORDER BY ra.applied_at DESC NULLS LAST, r.check_in_date, r.reservation_code
        """
    )
    return [dict(row) for row in rows]
