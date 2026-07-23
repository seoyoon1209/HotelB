from pathlib import Path

MODEL_NAME = "hotel_cancellation_gbt"
MODEL_VERSION = "1"
MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_model" / "001"

DECISION_THRESHOLD = 0.5

_tf = None          # 지연 import된 tensorflow 모듈
_infer = None       # 로드된 서빙 시그니처
_load_error = None  # 로드 실패 원인(있으면 계속 503)


def load_model() -> None:
    """하위 호환용. 실제 로딩은 지연 처리하므로 여기서는 아무 것도 하지 않는다."""
    return


def _ensure_loaded() -> None:
    global _tf, _infer, _load_error
    if _infer is not None:
        return
    if _load_error is not None:
        raise RuntimeError(_load_error)
    try:
        # struct2tensor는 saved_model.pb의 DecodeProto* 커스텀 연산 등록용. tensorflow보다 먼저 import.
        import struct2tensor  # noqa: F401
        import tensorflow as tf

        model = tf.saved_model.load(str(MODEL_DIR))
        _tf = tf
        _infer = model.signatures["serving_default"]
    except Exception as e:  # ImportError(로컬) / OOM / 로드 실패 등
        _load_error = f"예측 모델을 사용할 수 없습니다: {e}"
        raise RuntimeError(_load_error) from e


def _bytes_feature(value):
    return _tf.train.Feature(bytes_list=_tf.train.BytesList(value=[str(value).encode("utf-8")]))


def _build_example(features: dict) -> bytes:
    example = _tf.train.Example(
        features=_tf.train.Features(feature={k: _bytes_feature(v) for k, v in features.items()})
    )
    return example.SerializeToString()


def predict(features: dict) -> tuple[float, str]:
    """features -> (취소 확률, 예측 상태 'CANCELLED'/'NOT_CANCELLED')"""
    _ensure_loaded()

    serialized = _build_example(features)
    result = _infer(inputs=_tf.constant([serialized]))

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
