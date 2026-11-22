from collections import Counter

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline

from app.ml.labels import LABELS
from app.ml.preprocess import preprocess_text
from training.dataset import Example

_POSITIVE_VIEWS = {
    "dangerous_only": {"dangerous"},
    "suspicious_or_dangerous": {"suspicious", "dangerous"},
}


def _round(value: float) -> float:
    return round(float(value), 6)


def binary_rates(true_labels: list[str], predicted: list[str], positive: set[str]) -> dict[str, float | int]:
    pairs = list(zip(true_labels, predicted, strict=True))
    true_positive = sum(true in positive and pred in positive for true, pred in pairs)
    false_positive = sum(true not in positive and pred in positive for true, pred in pairs)
    false_negative = sum(true in positive and pred not in positive for true, pred in pairs)
    true_negative = sum(true not in positive and pred not in positive for true, pred in pairs)
    false_positive_rate = false_positive / (false_positive + true_negative) if (false_positive + true_negative) else 0.0
    false_negative_rate = false_negative / (false_negative + true_positive) if (false_negative + true_positive) else 0.0
    return {
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "tn": true_negative,
        "false_positive_rate": _round(false_positive_rate),
        "false_negative_rate": _round(false_negative_rate),
    }


def classification_metrics(true_labels: list[str], predicted: list[str]) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(
        true_labels,
        predicted,
        labels=list(LABELS),
        zero_division=0,
    )
    per_label = {}
    for index, label in enumerate(LABELS):
        per_label[label] = {
            "precision": _round(precision[index]),
            "recall": _round(recall[index]),
            "f1": _round(f1[index]),
            "support": int(support[index]),
        }
    matrix = confusion_matrix(true_labels, predicted, labels=list(LABELS))
    macro_f1 = float(np.mean(f1)) if len(f1) else 0.0
    return {
        "per_label": per_label,
        "macro_f1": _round(macro_f1),
        "confusion_matrix": {
            "labels": list(LABELS),
            "matrix": matrix.astype(int).tolist(),
        },
        "operating_points": {
            name: binary_rates(true_labels, predicted, positive) for name, positive in _POSITIVE_VIEWS.items()
        },
    }


def predict_labels(pipeline: Pipeline, examples: list[Example]) -> list[str]:
    if not examples:
        return []
    predicted = pipeline.predict([preprocess_text(item.text) for item in examples])
    return [str(label) for label in predicted]


def metrics_by_language(examples: list[Example], predicted: list[str]) -> dict:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for example, label in zip(examples, predicted, strict=True):
        grouped.setdefault(example.language, []).append((example.label, label))
    report: dict[str, dict] = {
        "kk": {"status": "not_evaluated", "examples": 0},
    }
    for language in ("ru", "en"):
        pairs = grouped.get(language, [])
        if not pairs:
            report[language] = {"status": "not_evaluated", "examples": 0}
            continue
        true_labels = [item[0] for item in pairs]
        predicted_labels = [item[1] for item in pairs]
        report[language] = {
            "status": "evaluated",
            "examples": len(pairs),
            "label_counts": dict(Counter(true_labels)),
            **classification_metrics(true_labels, predicted_labels),
        }
    return report


def rule_baseline(text: str) -> str:
    """A small keyword baseline used only to compare against the trained model."""

    lowered = text.lower()
    urgency = any(token in lowered for token in ("сроч", "немедл", "urgent", "immediately", "дереу"))
    secret = any(token in lowered for token in ("код", "otp", "pin", "парол", "password"))
    payment = any(token in lowered for token in ("перевед", "оплат", "wire", " fee", "деньг", "төле"))
    link = "http://" in lowered or "https://" in lowered or "www." in lowered
    authority = any(token in lowered for token in ("банк", "bank", "госуслуг"))
    if (secret or payment) and (urgency or link or authority):
        return "dangerous"
    if not any((urgency, secret, payment, link, authority)):
        return "safe"
    return "needs_check"
