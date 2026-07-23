# prediction_result (AI ml)
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.dbpool import DbPoolDep
from ml import predictor
from ml.features import build_features

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


@router.post("/", response_model=PredictionResponse, status_code=201)
async def create_prediction(reservation_id: int, conn: DbPoolDep):
    """모델을 실제로 돌려 새 예측 결과를 만들고 prediction_result에 저장한다."""
    features = await build_features(reservation_id, conn)
    if features is None:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")

    try:
        probability, predicted_status = predictor.predict(features)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    risk_level = predictor.risk_level_of(probability)

    row = await conn.fetchrow(
        """
        INSERT INTO prediction_result (
            reservation_id, model_name, model_version,
            cancellation_probability, predicted_status, risk_level, decision_threshold
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        reservation_id,
        predictor.MODEL_NAME,
        predictor.MODEL_VERSION,
        probability,
        predicted_status,
        risk_level,
        predictor.DECISION_THRESHOLD,
    )
    return dict(row)
