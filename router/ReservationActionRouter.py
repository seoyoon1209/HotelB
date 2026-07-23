# reservation_action 테이블 관련.
# 리포트 화면에서 쓸 주 단위 집계(조치 건수 / 라벨 전환 성공 건수)도 제공
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/reservations/{reservation_id}/actions", tags=["reservation-actions"])
report_router = APIRouter(prefix="/actions/report", tags=["reservation-actions"])


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
    """예약의 조치 이력을 모두 삭제(조치 '안 함'으로 되돌리기). 리포트 집계에서도 함께 빠진다."""
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
