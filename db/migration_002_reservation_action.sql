-- 마이그레이션: reservation_action 테이블 추가.
-- schema.sql은 이미 실행되어 다른 테이블이 존재하는 DB에 이 파일만 추가로 실행하면 된다.
-- (schema.sql 자체에도 동일 내용이 반영되어 있음 — 새 DB를 처음부터 만들 땐 schema.sql만 실행하면 됨)

BEGIN;

CREATE TABLE IF NOT EXISTS reservation_action (
    action_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_id        BIGINT NOT NULL,

    discount_percent      INTEGER NOT NULL DEFAULT 0,
    breakfast_coupon      BOOLEAN NOT NULL DEFAULT FALSE,

    probability_before    NUMERIC(6, 5) NOT NULL,
    probability_after     NUMERIC(6, 5) NOT NULL,
    label_before           VARCHAR(20) NOT NULL,
    label_after            VARCHAR(20) NOT NULL,

    applied_at             TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reservation_action_reservation
        FOREIGN KEY (reservation_id)
        REFERENCES reservation (reservation_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_reservation_action_discount
        CHECK (discount_percent >= 0 AND discount_percent <= 100),

    CONSTRAINT chk_reservation_action_probabilities
        CHECK (
            probability_before >= 0 AND probability_before <= 1
            AND probability_after >= 0 AND probability_after <= 1
        ),

    CONSTRAINT chk_reservation_action_labels
        CHECK (
            label_before IN ('CANCEL', 'KEEP')
            AND label_after IN ('CANCEL', 'KEEP')
        )
);

COMMENT ON TABLE reservation_action IS '예약별 개입 조치(쿠폰 적용) 이력';
COMMENT ON COLUMN reservation_action.discount_percent IS '적용한 ADR 할인율(%)';
COMMENT ON COLUMN reservation_action.breakfast_coupon IS '조식쿠폰 제공 여부';
COMMENT ON COLUMN reservation_action.probability_before IS '조치 전 취소 확률';
COMMENT ON COLUMN reservation_action.probability_after IS '조치 후(시뮬레이션) 취소 확률';
COMMENT ON COLUMN reservation_action.label_before IS '조치 전 예측 라벨 (CANCEL/KEEP)';
COMMENT ON COLUMN reservation_action.label_after IS '조치 후 예측 라벨 (CANCEL/KEEP)';

CREATE INDEX IF NOT EXISTS idx_reservation_action_reservation_id
    ON reservation_action (reservation_id);

CREATE INDEX IF NOT EXISTS idx_reservation_action_applied_at
    ON reservation_action (applied_at DESC);

COMMIT;
