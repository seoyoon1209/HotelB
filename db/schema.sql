BEGIN;

-- =========================================================
-- 1. 호텔
-- =========================================================
CREATE TABLE hotel (
    hotel_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hotel_name         VARCHAR(100) NOT NULL,
    hotel_type         VARCHAR(30),
    city               VARCHAR(100),
    country            VARCHAR(100),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE hotel IS '호텔';
COMMENT ON COLUMN hotel.hotel_id IS '호텔 고유 ID';
COMMENT ON COLUMN hotel.hotel_name IS '호텔명';
COMMENT ON COLUMN hotel.hotel_type IS '호텔 유형';
COMMENT ON COLUMN hotel.city IS '도시';
COMMENT ON COLUMN hotel.country IS '국가';


-- =========================================================
-- 2. 고객
-- =========================================================
CREATE TABLE customer (
    customer_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name      VARCHAR(100),
    email              VARCHAR(255),
    phone              VARCHAR(30),
    country            VARCHAR(100),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_customer_email UNIQUE (email)
);

COMMENT ON TABLE customer IS '고객';
COMMENT ON COLUMN customer.customer_name IS '고객명';
COMMENT ON COLUMN customer.email IS '이메일';
COMMENT ON COLUMN customer.phone IS '전화번호';
COMMENT ON COLUMN customer.country IS '고객 국가';


-- =========================================================
-- 3. 객실 유형
-- 호텔마다 객실 유형이 다를 수 있으므로 hotel_id 포함
-- =========================================================
CREATE TABLE room_type (
    room_type_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hotel_id           BIGINT NOT NULL,
    room_type_code     VARCHAR(30) NOT NULL,
    room_type_name     VARCHAR(100) NOT NULL,
    capacity           INTEGER,
    base_price         NUMERIC(12, 2),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_room_type_hotel
        FOREIGN KEY (hotel_id)
        REFERENCES hotel (hotel_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_room_type_hotel_code
        UNIQUE (hotel_id, room_type_code),

    CONSTRAINT chk_room_type_capacity
        CHECK (capacity IS NULL OR capacity > 0),

    CONSTRAINT chk_room_type_base_price
        CHECK (base_price IS NULL OR base_price >= 0)
);

COMMENT ON TABLE room_type IS '객실 유형';
COMMENT ON COLUMN room_type.room_type_code IS '객실 유형 코드';
COMMENT ON COLUMN room_type.room_type_name IS '객실 유형명';
COMMENT ON COLUMN room_type.capacity IS '최대 수용 인원';
COMMENT ON COLUMN room_type.base_price IS '기본 객실 가격';


-- =========================================================
-- 4. 식사 유형
-- =========================================================
CREATE TABLE meal_type (
    meal_type_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meal_code          VARCHAR(30) NOT NULL UNIQUE,
    meal_name          VARCHAR(100) NOT NULL,
    description        TEXT
);

COMMENT ON TABLE meal_type IS '식사 유형';
COMMENT ON COLUMN meal_type.meal_code IS '식사 유형 코드';
COMMENT ON COLUMN meal_type.meal_name IS '식사 유형명';


-- =========================================================
-- 5. 시장 구분
-- =========================================================
CREATE TABLE market_segment (
    market_segment_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_code        VARCHAR(30) NOT NULL UNIQUE,
    segment_name        VARCHAR(100) NOT NULL,
    description         TEXT
);

COMMENT ON TABLE market_segment IS '시장 구분';
COMMENT ON COLUMN market_segment.segment_code IS '시장 구분 코드';
COMMENT ON COLUMN market_segment.segment_name IS '시장 구분명';


-- =========================================================
-- 6. 예약 유입 경로
-- =========================================================
CREATE TABLE distribution_channel (
    distribution_channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_code             VARCHAR(30) NOT NULL UNIQUE,
    channel_name             VARCHAR(100) NOT NULL,
    description              TEXT
);

COMMENT ON TABLE distribution_channel IS '예약 유입 경로';
COMMENT ON COLUMN distribution_channel.channel_code IS '예약 유입 경로 코드';
COMMENT ON COLUMN distribution_channel.channel_name IS '예약 유입 경로명';


-- =========================================================
-- 7. 보증금 유형
-- =========================================================
CREATE TABLE deposit_type (
    deposit_type_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    deposit_code        VARCHAR(30) NOT NULL UNIQUE,
    deposit_name        VARCHAR(100) NOT NULL,
    refundable          BOOLEAN NOT NULL DEFAULT FALSE,
    description         TEXT
);

COMMENT ON TABLE deposit_type IS '보증금 유형';
COMMENT ON COLUMN deposit_type.deposit_code IS '보증금 유형 코드';
COMMENT ON COLUMN deposit_type.deposit_name IS '보증금 유형명';
COMMENT ON COLUMN deposit_type.refundable IS '환불 가능 여부';


-- =========================================================
-- 8. 고객 유형
-- =========================================================
CREATE TABLE customer_type (
    customer_type_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_type_code  VARCHAR(30) NOT NULL UNIQUE,
    customer_type_name  VARCHAR(100) NOT NULL,
    description         TEXT
);

COMMENT ON TABLE customer_type IS '고객 유형';
COMMENT ON COLUMN customer_type.customer_type_code IS '고객 유형 코드';
COMMENT ON COLUMN customer_type.customer_type_name IS '고객 유형명';


-- =========================================================
-- 9. 예약
-- 숫자/날짜 데이터는 예약 테이블에 저장하고,
-- 반복되는 범주형 데이터는 FK로 연결
-- =========================================================
CREATE TABLE reservation (
    reservation_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_code        VARCHAR(50) NOT NULL UNIQUE,

    hotel_id                BIGINT NOT NULL,
    customer_id             BIGINT,
    room_type_id            BIGINT NOT NULL,
    meal_type_id            BIGINT,
    market_segment_id       BIGINT,
    distribution_channel_id BIGINT,
    deposit_type_id         BIGINT,
    customer_type_id        BIGINT,

    booking_date            DATE NOT NULL,
    check_in_date           DATE NOT NULL,
    check_out_date          DATE NOT NULL,

    adult_count             INTEGER NOT NULL DEFAULT 1,
    child_count             INTEGER NOT NULL DEFAULT 0,
    baby_count              INTEGER NOT NULL DEFAULT 0,

    weekend_nights          INTEGER NOT NULL DEFAULT 0,
    weekday_nights          INTEGER NOT NULL DEFAULT 0,

    adr                      NUMERIC(12, 2),
    total_price              NUMERIC(12, 2),

    reservation_status      VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    cancelled_at            TIMESTAMPTZ,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reservation_hotel
        FOREIGN KEY (hotel_id)
        REFERENCES hotel (hotel_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_reservation_customer
        FOREIGN KEY (customer_id)
        REFERENCES customer (customer_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_reservation_room_type
        FOREIGN KEY (room_type_id)
        REFERENCES room_type (room_type_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_reservation_meal_type
        FOREIGN KEY (meal_type_id)
        REFERENCES meal_type (meal_type_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_reservation_market_segment
        FOREIGN KEY (market_segment_id)
        REFERENCES market_segment (market_segment_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_reservation_distribution_channel
        FOREIGN KEY (distribution_channel_id)
        REFERENCES distribution_channel (distribution_channel_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_reservation_deposit_type
        FOREIGN KEY (deposit_type_id)
        REFERENCES deposit_type (deposit_type_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_reservation_customer_type
        FOREIGN KEY (customer_type_id)
        REFERENCES customer_type (customer_type_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_reservation_dates
        CHECK (
            booking_date <= check_in_date
            AND check_in_date < check_out_date
        ),

    CONSTRAINT chk_reservation_guest_counts
        CHECK (
            adult_count >= 0
            AND child_count >= 0
            AND baby_count >= 0
            AND adult_count + child_count + baby_count > 0
        ),

    CONSTRAINT chk_reservation_nights
        CHECK (
            weekend_nights >= 0
            AND weekday_nights >= 0
            AND weekend_nights + weekday_nights > 0
        ),

    CONSTRAINT chk_reservation_adr
        CHECK (adr IS NULL OR adr >= 0),

    CONSTRAINT chk_reservation_total_price
        CHECK (total_price IS NULL OR total_price >= 0),

    CONSTRAINT chk_reservation_status
        CHECK (
            reservation_status IN (
                'PENDING',
                'CONFIRMED',
                'CHECKED_IN',
                'COMPLETED',
                'CANCELLED',
                'NO_SHOW'
            )
        ),

    CONSTRAINT chk_cancelled_at
        CHECK (
            reservation_status = 'CANCELLED'
            OR cancelled_at IS NULL
        )
);

COMMENT ON TABLE reservation IS '예약';
COMMENT ON COLUMN reservation.reservation_code IS '예약번호';
COMMENT ON COLUMN reservation.booking_date IS '예약 접수일';
COMMENT ON COLUMN reservation.check_in_date IS '체크인 예정일';
COMMENT ON COLUMN reservation.check_out_date IS '체크아웃 예정일';
COMMENT ON COLUMN reservation.adult_count IS '성인 수';
COMMENT ON COLUMN reservation.child_count IS '아동 수';
COMMENT ON COLUMN reservation.baby_count IS '유아 수';
COMMENT ON COLUMN reservation.weekend_nights IS '주말 숙박일 수';
COMMENT ON COLUMN reservation.weekday_nights IS '주중 숙박일 수';
COMMENT ON COLUMN reservation.adr IS '일평균 객실 요금';
COMMENT ON COLUMN reservation.reservation_status IS '예약 상태';


-- =========================================================
-- 10. AI 예측 결과
-- 같은 예약을 여러 모델 버전으로 재예측할 수 있도록 1:N 구조
-- =========================================================
CREATE TABLE prediction_result (
    prediction_id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_id            BIGINT NOT NULL,

    model_name                VARCHAR(100) NOT NULL,
    model_version             VARCHAR(50) NOT NULL,

    cancellation_probability  NUMERIC(6, 5) NOT NULL,
    predicted_status          VARCHAR(20) NOT NULL,
    risk_level                VARCHAR(20) NOT NULL,

    decision_threshold        NUMERIC(6, 5) NOT NULL DEFAULT 0.50000,
    feature_contributions     JSONB,

    predicted_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_prediction_reservation
        FOREIGN KEY (reservation_id)
        REFERENCES reservation (reservation_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_cancellation_probability
        CHECK (
            cancellation_probability >= 0
            AND cancellation_probability <= 1
        ),

    CONSTRAINT chk_prediction_threshold
        CHECK (
            decision_threshold >= 0
            AND decision_threshold <= 1
        ),

    CONSTRAINT chk_predicted_status
        CHECK (
            predicted_status IN ('CANCELLED', 'NOT_CANCELLED')
        ),

    CONSTRAINT chk_prediction_risk_level
        CHECK (
            risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        )
);

COMMENT ON TABLE prediction_result IS 'AI 예약 취소 예측 결과';
COMMENT ON COLUMN prediction_result.model_name IS 'AI 모델명';
COMMENT ON COLUMN prediction_result.model_version IS 'AI 모델 버전';
COMMENT ON COLUMN prediction_result.cancellation_probability IS '예약 취소 확률';
COMMENT ON COLUMN prediction_result.predicted_status IS '예측 결과';
COMMENT ON COLUMN prediction_result.risk_level IS '취소 위험 등급';
COMMENT ON COLUMN prediction_result.feature_contributions IS 'SHAP 등 변수별 영향도 JSON';


-- =========================================================
-- 조회 및 JOIN 성능을 위한 인덱스
-- =========================================================
CREATE INDEX idx_room_type_hotel_id
    ON room_type (hotel_id);

CREATE INDEX idx_reservation_hotel_id
    ON reservation (hotel_id);

CREATE INDEX idx_reservation_customer_id
    ON reservation (customer_id);

CREATE INDEX idx_reservation_room_type_id
    ON reservation (room_type_id);

CREATE INDEX idx_reservation_check_in_date
    ON reservation (check_in_date);

CREATE INDEX idx_reservation_status
    ON reservation (reservation_status);

CREATE INDEX idx_reservation_hotel_check_in
    ON reservation (hotel_id, check_in_date);

CREATE INDEX idx_prediction_reservation_id
    ON prediction_result (reservation_id);

CREATE INDEX idx_prediction_probability
    ON prediction_result (cancellation_probability DESC);

CREATE INDEX idx_prediction_risk_level
    ON prediction_result (risk_level);

COMMIT;
