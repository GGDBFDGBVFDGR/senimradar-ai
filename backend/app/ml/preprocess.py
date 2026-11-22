import re

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_REF_RE = re.compile(r"\b(?:ref|note)\s*\d+\b", re.IGNORECASE)
_LONG_DIGITS_RE = re.compile(r"\d{3,}")
_SPACE_RE = re.compile(r"\s+")

KAZAKH_LETTERS = frozenset("әғқңөұүһіӘҒҚҢӨҰҮҺІ")


def preprocess_text(value: str) -> str:
    """Normalize text for the vectorizer without storing the original message."""

    text = value.replace("\u00a0", " ").strip().lower()
    text = _URL_RE.sub(" url ", text)
    text = _REF_RE.sub(" ref ", text)
    text = _LONG_DIGITS_RE.sub(" 0 ", text)
    return _SPACE_RE.sub(" ", text).strip()


def template_key(value: str) -> str:
    """Collapse numbers so translated copies and reference codes stay in one group."""

    text = preprocess_text(value)
    text = re.sub(r"\d+", "0", text)
    return _SPACE_RE.sub(" ", text).strip()


def looks_kazakh(value: str) -> bool:
    return sum(1 for char in value if char in KAZAKH_LETTERS) >= 2
