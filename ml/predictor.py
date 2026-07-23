# 예약 취소 예측 TF SavedModel 로딩 및 추론
from pathlib import Path

try:
    # struct2tensor는 saved_model.pb의 DecodeProto* 커스텀 연산 등록용. tf.saved_model.load보다 먼저 import 필요.
    # arm64 macOS(로컬 개발 환경)에는 정상 wheel이 없어 설치/임포트가 실패할 수 있음 — 그 경우 예측 기능만 비활성화하고
    # 나머지 API는 그대로 동작하게 한다. Render(Linux x86_64) 배포 환경에서는 정상 로드된다.
    import struct2tensor  # noqa: F401
    import tensorflow as tf

    _TF_AVAILABLE = True
except ImportError:
    tf = None
    _TF_AVAILABLE = False

MODEL_NAME = "hotel_cancellation_gbt"
MODEL_VERSION = "1"
MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_model" / "001"

DECISION_THRESHOLD = 0.5

_infer = None


def load_model() -> None:
    global _infer
    if not _TF_AVAILABLE:
        print("[ml] tensorflow/struct2tensor를 불러올 수 없어 모델 로드를 건너뜁니다.")
        return
    model = tf.saved_model.load(str(MODEL_DIR))
    _infer = model.signatures["serving_default"]


def _bytes_feature(value) -> tf.train.Feature:
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[str(value).encode("utf-8")]))


def _build_example(features: dict) -> bytes:
    example = tf.train.Example(
        features=tf.train.Features(feature={k: _bytes_feature(v) for k, v in features.items()})
    )
    return example.SerializeToString()


def predict(features: dict) -> tuple[float, str]:
    """features -> (취소 확률, 예측 상태 'CANCELLED'/'NOT_CANCELLED')"""
    if _infer is None:
        raise RuntimeError("모델이 아직 로드되지 않았습니다. load_model()을 먼저 호출하세요.")

    serialized = _build_example(features)
    result = _infer(inputs=tf.constant([serialized]))

    classes = [c.decode("utf-8") for c in result["classes"].numpy()[0]]
    scores = result["scores"].numpy()[0]
    cancel_idx = classes.index("1")
    probability = float(scores[cancel_idx])
    predicted_status = "CANCELLED" if probability >= DECISION_THRESHOLD else "NOT_CANCELLED"
    return probability, predicted_status


def risk_level_of(probability: float) -> str:
    if probability < 0.25:
        return "LOW"
    if probability < 0.5:
        return "MEDIUM"
    if probability < 0.75:
        return "HIGH"
    return "CRITICAL"
