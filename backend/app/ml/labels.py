"""Shared label names. Risk categories follow the dataset, not a hand-picked probability cutoff."""

LABELS = ("safe", "needs_check", "suspicious", "dangerous")

RISK_BY_LABEL = {
    "safe": "low",
    "needs_check": "unknown",
    "suspicious": "medium",
    "dangerous": "high",
}

MIN_ANALYSIS_CHARS = 12
