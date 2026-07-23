# reservation 테이블 -> 모델 입력 피처(dict[str, str]) 변환
# 모델(assets/*_vocab)이 요구하는 18개 입력 키를 그대로 맞춘다.
import asyncpg

_RESERVATION_FOR_FEATURES_SQL = """
    SELECT
        r.reservation_id,
        r.customer_id,
        r.booking_date,
        r.check_in_date,
        r.adult_count,
        r.child_count,
        r.baby_count,
        r.weekend_nights,
        r.weekday_nights,
        r.adr,
        rt.room_type_code,
        mt.meal_code,
        ms.segment_name,
        dt.deposit_name,
        ct.customer_type_code
    FROM reservation r
    JOIN room_type rt ON rt.room_type_id = r.room_type_id
    LEFT JOIN meal_type mt ON mt.meal_type_id = r.meal_type_id
    LEFT JOIN market_segment ms ON ms.market_segment_id = r.market_segment_id
    LEFT JOIN deposit_type dt ON dt.deposit_type_id = r.deposit_type_id
    LEFT JOIN customer_type ct ON ct.customer_type_id = r.customer_type_id
    WHERE r.reservation_id = $1
"""

_PREV_RESERVATION_STATS_SQL = """
    SELECT
        COUNT(*) FILTER (WHERE reservation_status = 'CANCELLED') AS num_cancel_prev_resv,
        COUNT(*) FILTER (WHERE reservation_status IN ('CHECKED_IN', 'COMPLETED')) AS num_checkin_prev_resv
    FROM reservation
    WHERE customer_id = $1
      AND reservation_id != $2
      AND booking_date < $3
"""


async def build_features(reservation_id: int, conn: asyncpg.Connection) -> dict | None:
    row = await conn.fetchrow(_RESERVATION_FOR_FEATURES_SQL, reservation_id)
    if row is None:
        return None

    num_cancel_prev_resv = 0
    num_checkin_prev_resv = 0
    if row["customer_id"] is not None:
        stats = await conn.fetchrow(
            _PREV_RESERVATION_STATS_SQL,
            row["customer_id"],
            reservation_id,
            row["booking_date"],
        )
        num_cancel_prev_resv = stats["num_cancel_prev_resv"]
        num_checkin_prev_resv = stats["num_checkin_prev_resv"]

    is_repeated_guest = 1 if (num_cancel_prev_resv + num_checkin_prev_resv) > 0 else 0
    lead_time = (row["check_in_date"] - row["booking_date"]).days
    num_guest = row["adult_count"] + row["child_count"] + row["baby_count"]
    adr = float(row["adr"]) if row["adr"] is not None else 0.0

    return {
        "arrival_date": row["check_in_date"].isoformat(),
        "arrival_month": str(row["check_in_date"].month),
        "num_nights_week": str(row["weekday_nights"]),
        "num_nights_weekend": str(row["weekend_nights"]),
        "num_guest": str(num_guest),
        "average_daily_rate": str(round(adr, 2)),
        "lead_time": str(max(lead_time, 0)),
        "meal_type": row["meal_code"] or "SC",
        "market_segment": row["segment_name"] or "Direct",
        "deposit_type": row["deposit_name"] or "No Deposit",
        "customer_type": row["customer_type_code"] or "Transient",
        "reserved_room_type": row["room_type_code"],
        "is_repeated_guest": str(is_repeated_guest),
        "num_cancel_prev_resv": str(num_cancel_prev_resv),
        "num_checkin_prev_resv": str(num_checkin_prev_resv),
        # 아래 두 필드는 모델 vocab이 "0"/"1" 두 값만 가지고 있어 실제 학습 시 인코딩 기준을
        # 알 수 없음(country_code가 실제 국가코드가 아니라 이진값인 이유 불명, cancellation은
        # 이름상 예측 대상(취소 여부)과 동일한 값 도메인이라 학습 데이터 유출 가능성이 있음).
        # 서빙 시점엔 정답을 알 수 없으므로 안전하게 기본값 "0"으로 고정. 학습 파이프라인을
        # 확인할 수 있게 되면 재검토 필요.
        "country_code": "0",
        "cancellation": "0",
        "SPLIT": "VALIDATE",
    }
