# 최신 예측 모델 정보 + 완료/취소된 예약 기준 참고용 정확도.
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.dbpool import DbPoolDep

router = APIRouter(prefix="/model-info", tags=["model-info"])


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    updated_at: datetime
    accuracy: float | None = None
    sample_size: int


@router.get("/", response_model=ModelInfoResponse)
async def get_model_info(conn: DbPoolDep):
    latest = await conn.fetchrow(
        "SELECT model_name, model_version, predicted_at FROM prediction_result ORDER BY predicted_at DESC LIMIT 1"
    )
    if not latest:
        raise HTTPException(status_code=404, detail="예측 결과가 없습니다.")

    accuracy_row = await conn.fetchrow(
        """
        WITH latest_pred AS (
            SELECT DISTINCT ON (reservation_id) reservation_id, predicted_status
            FROM prediction_result
            ORDER BY reservation_id, predicted_at DESC
        )
        SELECT
            COUNT(*) FILTER (
                WHERE (r.reservation_status = 'CANCELLED' AND lp.predicted_status = 'CANCELLED')
                   OR (r.reservation_status IN ('CONFIRMED', 'CHECKED_IN', 'COMPLETED') AND lp.predicted_status = 'NOT_CANCELLED')
            ) AS correct,
            COUNT(*) AS total
        FROM reservation r
        JOIN latest_pred lp ON lp.reservation_id = r.reservation_id
        WHERE r.reservation_status IN ('CANCELLED', 'CONFIRMED', 'CHECKED_IN', 'COMPLETED')
        """
    )
    total = accuracy_row["total"] or 0
    accuracy = (accuracy_row["correct"] / total) if total else None

    return {
        "model_name": latest["model_name"],
        "model_version": latest["model_version"],
        "updated_at": latest["predicted_at"],
        "accuracy": accuracy,
        "sample_size": total,
    }
