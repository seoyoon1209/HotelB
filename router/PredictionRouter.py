from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/reservations/{reservation_id}/predictions", tags=["predictions"])


class PredictionResponse(BaseModel):
    prediction_id: int
    reservation_id: int
    model_name: str
    model_version: str
    cancellation_probability: Decimal
    predicted_status: str
    risk_level: str
    decision_threshold: Decimal
    feature_contributions: dict[str, Any] | None = None
    predicted_at: datetime


@router.get("/", response_model=list[PredictionResponse])
async def list_predictions(reservation_id: int, conn: DbPoolDep):
    rows = await conn.fetch(
        "SELECT * FROM prediction_result WHERE reservation_id = $1 ORDER BY predicted_at DESC",
        reservation_id,
    )
    return [dict(row) for row in rows]
