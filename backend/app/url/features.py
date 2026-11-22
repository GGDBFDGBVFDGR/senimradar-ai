"""URL string features shared by training and inference. Nothing is fetched."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer

BRANDS = (
    "paypal",
    "apple",
    "google",
    "microsoft",
    "amazon",
    "kaspi",
    "halyk",
    "freedom",
    "jusan",
    "bereke",
    "facebook",
    "instagram",
    "whatsapp",
    "telegram",
    "binance",
    "steam",
    "netflix",
    "adobe",
    "dhl",
)

_LOGIN_RE = re.compile(r"login|signin|verify|account|secure|update|wallet|password|confirm|banking", re.IGNORECASE)
_NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")
STRUCTURE_NAMES = (
    "length",
    "host_length",
    "subdomain_count",
    "path_depth",
    "query_length",
    "digit_ratio",
    "hyphen_count",
    "has_at",
    "host_is_ip",
    "has_punycode",
    "has_non_ascii",
    "exact_brand",
    "lookalike_brand",
    "credential_path",
    "nonstandard_port",
    "many_subdomains",
)


def host_labels(host: str) -> list[str]:
    return [label for label in host.lower().strip(".").split(".") if label]


def _distance(left: str, right: str) -> int:
    if abs(len(left) - len(right)) > 2:
        return 3
    previous = list(range(len(right) + 1))
    for index, char in enumerate(left, start=1):
        current = [index]
        for other_index, other in enumerate(right, start=1):
            change = 0 if char == other else 1
            current.append(min(previous[other_index] + 1, current[other_index - 1] + 1, previous[other_index - 1] + change))
        previous = current
    return previous[-1]


def brand_flags(host: str) -> tuple[float, float]:
    labels = host_labels(host)
    exact = 0.0
    lookalike = 0.0
    for label in labels:
        if label in {"www", "com", "net", "org"}:
            continue
        for brand in BRANDS:
            if label == brand:
                exact = 1.0
            elif len(label) >= 5 and _distance(label, brand) <= 1:
                lookalike = 1.0
    return exact, lookalike


def structure_vector(value: str) -> list[float]:
    parts = urlsplit(value.strip())
    host = parts.hostname or ""
    labels = host_labels(host)
    path = parts.path or ""
    digits = sum(character.isdigit() for character in value)
    exact, lookalike = brand_flags(host)
    subdomain_count = max(0, len(labels) - 2)
    port = parts.port
    return [
        min(len(value), 300) / 300,
        min(len(host), 120) / 120,
        min(subdomain_count, 6) / 6,
        min(path.count("/"), 8) / 8,
        min(len(parts.query), 150) / 150,
        digits / max(len(value), 1),
        min(value.count("-"), 12) / 12,
        1.0 if "@" in (parts.netloc or "") else 0.0,
        1.0 if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host) else 0.0,
        1.0 if "xn--" in host else 0.0,
        1.0 if _NON_ASCII_RE.search(value) else 0.0,
        exact,
        lookalike,
        1.0 if _LOGIN_RE.search(f"{path}?{parts.query}") else 0.0,
        1.0 if port not in {None, 80, 443} else 0.0,
        1.0 if subdomain_count >= 3 else 0.0,
    ]


class UrlVectorizer(BaseEstimator, TransformerMixin):
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=2, max_features=20000, lowercase=True)

    def fit(self, urls, y=None):
        self.vectorizer.fit(list(urls))
        return self

    def transform(self, urls):
        rows = list(urls)
        text = self.vectorizer.transform(rows)
        structural = sparse.csr_matrix(np.array([structure_vector(url) for url in rows], dtype=np.float32))
        return sparse.hstack([text, structural], format="csr")
