import re

from app.ml.markers import prohibition_only

# Observations only. A match is not a fraud verdict.
# A password is not treated as a one-time code. A prohibition is not treated as a request.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "urgency",
        re.compile(
            r"срочн|немедлен|прямо сейчас|в течение|дереу|шұғыл|тез арада|urgent|immediately|right away|last chance",
            re.IGNORECASE,
        ),
    ),
    (
        "otp_request",
        re.compile(
            r"одноразов\w*\s+код|код(?:е|у|а)?\s+из|сообщите код|введите код|\botp\b|\bpin\b",
            re.IGNORECASE,
        ),
    ),
    (
        "bank_impersonation",
        re.compile(
            r"служб\w*\s+безопасност\w*\s+банк|банк(?:а|е|у|ом)?\b|\bbank\b|госуслуг",
            re.IGNORECASE,
        ),
    ),
    (
        "suspicious_link",
        re.compile(r"https?://|www\.", re.IGNORECASE),
    ),
    (
        "payment_request",
        re.compile(
            r"перевед\w*|перевод\w*|оплат\w*|wire\b|processing fee|ақша\s+аудар|төлең|төлем",
            re.IGNORECASE,
        ),
    ),
    (
        "password_request",
        re.compile(r"парол\w*|password|құпиясөз|seed phrase|сид-фраз", re.IGNORECASE),
    ),
)


def detect_indicators(text: str) -> list[str]:
    warning = prohibition_only(text)
    found: list[str] = ["fraud_warning"] if warning else []
    for code, pattern in _PATTERNS:
        if pattern.search(text) is None:
            continue
        if warning and code in {"otp_request", "password_request", "payment_request"}:
            continue
        found.append(code)
    return found


def recommendation_codes(indicators: list[str], risk_level: str, uncertain: bool) -> list[str]:
    codes: list[str] = ["not_proof"] if risk_level in {"medium", "high"} else []
    if "fraud_warning" in indicators:
        codes.append("warning_not_a_request")
    if "otp_request" in indicators or "password_request" in indicators:
        codes.append("do_not_share_codes")
    if "payment_request" in indicators:
        codes.append("do_not_transfer")
    if "suspicious_link" in indicators:
        codes.append("do_not_open_link")
    if risk_level in {"medium", "high", "unknown"} or uncertain or indicators:
        codes.append("verify_official_channel")
    if uncertain or risk_level == "unknown":
        codes.append("result_uncertain")
    return codes
