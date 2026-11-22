"""Score a URL string with the local model. The address is not opened."""

from __future__ import annotations

from app.url.features import structure_vector
from app.url.registry import load_url_runtime
from app.url.safety import admission

_INDICATORS = {
    7: "at_sign",
    8: "ip_host",
    9: "punycode",
    12: "lookalike_brand",
    13: "credential_path",
    14: "unusual_port",
    15: "many_subdomains",
}


def _base(status: str, code: str | None, model_version: str | None) -> dict:
    limitations = ["not_fetched", "not_a_proof", "confidence_not_calibrated"]
    if code == "ocr_damaged":
        limitations.append("ocr_url_not_repaired")
    if code in {"internal_address", "local_name", "unsupported_scheme", "scheme_required", "invalid_address"}:
        limitations.append(code)
    recommendations = ["address_not_opened"]
    if code == "ocr_damaged":
        recommendations.append("correct_the_address")
    elif status == "ok":
        recommendations.append("check_before_opening")
    return {
        "status": status,
        "code": code,
        "risk_level": "unknown",
        "risk_score": None,
        "model_version": model_version,
        "uncertain": True,
        "indicators": [],
        "recommendations": recommendations,
        "limitations": limitations,
        "classified": False,
    }


def observable_indicators(value: str) -> list[str]:
    vector = structure_vector(value)
    found = [name for index, name in _INDICATORS.items() if vector[index] >= 1]
    if len(value) > 90:
        found.append("long_address")
    return found


def analyze_url(value: str) -> dict:
    blocked = admission(value)
    if blocked == "ocr_damaged":
        return _base("needs_review", "ocr_damaged", None)
    if blocked:
        return _base("limited", blocked, None)
    runtime = load_url_runtime()
    if runtime is None:
        raise RuntimeError("url_model_missing")
    payload = runtime["payload"]
    pipeline = payload["pipeline"]
    predicted = str(pipeline.predict([value])[0])
    margin = abs(float(pipeline.decision_function([value])[0]))
    uncertain = margin < float(payload["uncertainty_margin"])
    risk = "unknown" if uncertain else ("high" if predicted == "phishing" else "low")
    indicators = observable_indicators(value)
    recommendations = ["address_not_opened", "check_before_opening"]
    if risk == "high":
        recommendations.append("do_not_open")
        recommendations.append("not_proof")
    elif risk == "low":
        recommendations.append("low_not_safe")
    else:
        recommendations.append("result_uncertain")
    limitations = [
        "not_fetched",
        "not_a_proof",
        "confidence_not_calibrated",
        "benign_from_popular_domains",
        "phishtank_community_labels",
        "constructed_benign_paths",
    ]
    return {
        "status": "ok",
        "code": None,
        "risk_level": risk,
        "risk_score": None,
        "model_version": payload["model_version"],
        "uncertain": uncertain or risk == "unknown",
        "indicators": indicators,
        "recommendations": recommendations,
        "limitations": limitations,
        "classified": True,
    }
