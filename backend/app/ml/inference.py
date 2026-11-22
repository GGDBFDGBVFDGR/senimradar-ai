import re

from app.ml.indicators import detect_indicators, recommendation_codes
from app.ml.labels import MIN_ANALYSIS_CHARS, RISK_BY_LABEL
from app.ml.markers import model_input
from app.ml.preprocess import looks_kazakh, preprocess_text
from app.ml.registry import load_runtime

_DIGIT_RE = re.compile(r"\d")
_WORD_CUE_RE = re.compile(r"^[^\W\d_]+(?: [^\W\d_]+)?$", re.UNICODE)


def explain_cues(pipeline, text: str, label: str, structural: bool, limit: int = 5) -> list[str]:
    """Return word fragments that occur contiguously in the message.

    Character n-grams and internal marker tokens are not shown as quotations.
    """

    features = pipeline.named_steps["features"]
    classifier = pipeline.named_steps["clf"]
    prepared = model_input(text, structural)
    vector = features.transform([prepared])
    names = features.get_feature_names_out()
    class_index = list(classifier.classes_).index(label)
    coefficients = classifier.coef_[class_index]
    visible = preprocess_text(text)
    row = vector.tocsr()
    scored: list[tuple[float, str]] = []
    for index, value in zip(row.indices, row.data, strict=False):
        raw_name = str(names[index])
        if not raw_name.startswith("word__"):
            continue
        weight = float(coefficients[index] * value)
        if weight <= 0:
            continue
        token = raw_name.split("__", 1)[-1].strip()
        if token.startswith("marker_") or len(token) < 3 or _DIGIT_RE.search(token):
            continue
        if _WORD_CUE_RE.fullmatch(token) is None or token not in visible:
            continue
        scored.append((weight, token))
    scored.sort(key=lambda item: item[0], reverse=True)
    cues: list[str] = []
    for _, token in scored:
        if token not in cues:
            cues.append(token)
        if len(cues) == limit:
            break
    return cues


def analyze_message(text: str, language: str) -> dict:
    runtime = load_runtime()
    if runtime is None:
        raise RuntimeError("model_missing")
    payload = runtime["payload"]
    card = runtime["card"]
    pipeline = payload["pipeline"]
    kazakh = language == "kk" or looks_kazakh(text)
    limitations = ["synthetic_training_data", "not_a_proof"]
    for code in ("researcher_authored_scenarios", "kazakh_not_field_data"):
        if code in card.get("limitations", []) and code not in limitations:
            limitations.append(code)
    if not card.get("confidence_calibrated", False):
        limitations.append("confidence_not_calibrated")
    if kazakh:
        limitations.append("kazakh_not_evaluated")
    elif language == "unknown":
        limitations.append("language_not_confirmed")

    if len(text.strip()) < MIN_ANALYSIS_CHARS:
        return {
            "status": "insufficient",
            "language": language,
            "language_evaluation": "not_evaluated" if kazakh else "not_confirmed",
            "model_version": payload["model_version"],
            "risk_level": "unknown",
            "risk_score": None,
            "confidence_calibrated": False,
            "uncertain": True,
            "indicators": [],
            "cues": [],
            "recommendations": ["result_uncertain", "not_proof"],
            "limitations": [*limitations, "insufficient_text"],
        }

    if kazakh:
        indicators = detect_indicators(text)
        return {
            "status": "ok",
            "language": language,
            "language_evaluation": "not_evaluated",
            "model_version": payload["model_version"],
            "risk_level": "unknown",
            "risk_score": None,
            "confidence_calibrated": bool(card.get("confidence_calibrated", False)),
            "uncertain": True,
            "indicators": indicators,
            "cues": [],
            "recommendations": recommendation_codes(indicators, "unknown", True),
            "limitations": limitations,
        }

    structural = bool(card.get("structural_markers", False))
    prepared = model_input(text, structural)
    probabilities = pipeline.predict_proba([prepared])[0]
    classes = [str(label) for label in pipeline.classes_]
    order = sorted(range(len(classes)), key=lambda index: probabilities[index], reverse=True)
    predicted = classes[order[0]]
    margin = float(probabilities[order[0]] - probabilities[order[1]]) if len(order) > 1 else 1.0
    top_probability = float(probabilities[order[0]])
    floor = payload.get("min_top_probability")
    low_confidence = floor is not None and top_probability < float(floor)
    uncertain = predicted == "needs_check" or margin < float(payload["uncertainty_margin"]) or low_confidence
    indicators = detect_indicators(text)
    risk_level = "unknown" if low_confidence else RISK_BY_LABEL[predicted]
    language_evaluation = "evaluated" if language in {"ru", "en"} else "not_confirmed"
    # The independent English holdout is too weak to show as a verdict.
    if language == "en":
        limitations.append("english_holdout_weak")
        risk_level = "unknown"
        uncertain = True
        cues: list[str] = []
    elif low_confidence:
        limitations.append("low_confidence")
        cues = []
    else:
        cues = explain_cues(pipeline, text, predicted, structural)
    return {
        "status": "ok",
        "language": language,
        "language_evaluation": language_evaluation,
        "model_version": payload["model_version"],
        "risk_level": risk_level,
        "risk_score": None,
        "confidence_calibrated": bool(card.get("confidence_calibrated", False)),
        "uncertain": uncertain,
        "indicators": indicators,
        "cues": cues,
        "recommendations": recommendation_codes(indicators, risk_level, uncertain),
        "limitations": limitations,
    }
