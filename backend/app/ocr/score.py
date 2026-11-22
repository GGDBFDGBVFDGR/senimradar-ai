"""Character and word error rates for OCR samples with a known source text."""

from __future__ import annotations

import re
import unicodedata

_SPACE_RE = re.compile(r"\s+")


def normalize_ocr_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value).casefold()
    return _SPACE_RE.sub(" ", text).strip()


def levenshtein(left: str, right: str) -> int:
    return _edit_distance(list(left), list(right))


def _edit_distance(left: list[str], right: list[str]) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for index, char in enumerate(left, start=1):
        current = [index]
        for other_index, other in enumerate(right, start=1):
            change = 0 if char == other else 1
            current.append(
                min(previous[other_index] + 1, current[other_index - 1] + 1, previous[other_index - 1] + change)
            )
        previous = current
    return previous[-1]


def character_error_rate(reference: str, hypothesis: str) -> float:
    expected = normalize_ocr_text(reference)
    actual = normalize_ocr_text(hypothesis)
    if not expected:
        return 0.0 if not actual else 1.0
    return levenshtein(expected, actual) / len(expected)


def word_error_rate(reference: str, hypothesis: str) -> float:
    expected = normalize_ocr_text(reference).split(" ")
    actual = normalize_ocr_text(hypothesis).split(" ")
    expected = [word for word in expected if word]
    actual = [word for word in actual if word]
    if not expected:
        return 0.0 if not actual else 1.0
    return _edit_distance(expected, actual) / len(expected)
