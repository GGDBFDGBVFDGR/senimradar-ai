"""Stage 2.1 comparison. Does not overwrite tfidf-logreg-0001.

Hyperparameters and the confidence floor are chosen on validation only.
The adaption test and the research test are scored once, after that choice.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date
from importlib.metadata import version

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from app.ml.indicators import detect_indicators
from app.ml.inference import explain_cues
from app.ml.labels import RISK_BY_LABEL
from app.ml.markers import model_input
from training.config import (
    ARTIFACT_DIR,
    C_GRID,
    EVAL_BILINGUAL_FILE,
    EVAL_EN_FILE,
    TRAIN_FILE,
)
from training.dataset import Example, load_evaluation_rows, load_training_rows
from training.evaluate import classification_metrics
from training.model import build_pipeline, calibration_accepted, expected_calibration_error
from training.research import load_research_examples, overlap_report
from training.split import prepare_splits
from app.ml.svm_classifier import MarginSoftmaxSVM

LOCKED_PROBE = "Не сообщайте никому SMS-код"
PRECISION_FLOOR = 0.70
RECALL_TIE = 0.01
ADAPTION_RU_RECALL_FLOOR = 0.753
ADAPTION_RU_PRECISION_FLOOR = 0.838
ADAPTION_RU_MACRO_FLOOR = 0.768
CONFIDENCE_FLOORS = (None, 0.40, 0.45, 0.50, 0.55)
TARGET_LANGUAGES = {"ru", "kk", "mixed"}


def _sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fit(kind: str, texts: list[str], labels: list[str], c_value: float, structural: bool) -> Pipeline:
    prepared = [model_input(text, structural) for text in texts]
    if kind == "logreg":
        pipeline = build_pipeline(c_value)
    else:
        pipeline = build_pipeline(c_value)
        pipeline.set_params(clf=MarginSoftmaxSVM(c_value=c_value))
    pipeline.fit(prepared, labels)
    return pipeline


def _predict(pipeline: Pipeline, texts: list[str], structural: bool) -> tuple[list[str], np.ndarray]:
    if not texts:
        return [], np.zeros((0, 1))
    probabilities = pipeline.predict_proba([model_input(text, structural) for text in texts])
    classes = [str(label) for label in pipeline.classes_]
    predicted = [classes[int(index)] for index in probabilities.argmax(axis=1)]
    return predicted, probabilities


def _select_c(kind: str, train: list[Example], validation: list[Example], structural: bool) -> tuple[float, dict[str, float]]:
    scores: dict[str, float] = {}
    best_c = C_GRID[0]
    best_score = -1.0
    train_texts = [item.text for item in train]
    train_labels = [item.label for item in train]
    validation_texts = [item.text for item in validation]
    validation_labels = [item.label for item in validation]
    for c_value in C_GRID:
        pipeline = _fit(kind, train_texts, train_labels, c_value, structural)
        predicted, _ = _predict(pipeline, validation_texts, structural)
        score = float(f1_score(validation_labels, predicted, average="macro", zero_division=0))
        scores[str(c_value)] = round(score, 6)
        if score > best_score:
            best_score = score
            best_c = c_value
    return best_c, scores


def _language(examples: list[Example], language: str) -> list[Example]:
    return [item for item in examples if item.language == language]


def _harm(examples: list[Example], predicted: list[str]) -> dict[str, int]:
    dangerous_as_safe = dangerous_as_warning = dangerous_as_high = 0
    safe_as_high = safe_total = dangerous_total = 0
    for item, label in zip(examples, predicted, strict=True):
        if item.label == "dangerous":
            dangerous_total += 1
            if label == "safe":
                dangerous_as_safe += 1
            elif label in {"needs_check", "suspicious"}:
                dangerous_as_warning += 1
            elif label == "dangerous":
                dangerous_as_high += 1
        if item.label == "safe":
            safe_total += 1
            if label == "dangerous":
                safe_as_high += 1
    return {
        "dangerous_total": dangerous_total,
        "dangerous_as_safe": dangerous_as_safe,
        "dangerous_as_warning": dangerous_as_warning,
        "dangerous_as_high": dangerous_as_high,
        "safe_total": safe_total,
        "safe_as_high": safe_as_high,
    }


def _pack(examples: list[Example], predicted: list[str]) -> dict:
    metrics = classification_metrics([item.label for item in examples], predicted) if examples else {}
    return {"examples": len(examples), "metrics": metrics, "harm": _harm(examples, predicted) if examples else {}}


def _role_harm(examples: list[Example], predicted: list[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item, label in zip(examples, predicted, strict=True):
        role = item.split_source.split(":", 1)[-1]
        if role == "warning":
            counts[f"warning_predicted_{label}"] += 1
        if role == "hard_negative" and label == "dangerous":
            counts["hard_negative_as_dangerous"] += 1
        if role == "quiet_scam" and label == "safe":
            counts["quiet_scam_as_safe"] += 1
    return dict(counts)


def _select_floor(pipeline: Pipeline, examples: list[Example], structural: bool) -> float | None:
    if not examples:
        return None
    predicted, probabilities = _predict(pipeline, [item.text for item in examples], structural)
    top = probabilities.max(axis=1)
    labels = [item.label for item in examples]
    dangerous_total = sum(label == "dangerous" for label in labels)
    raw_hits = sum(label == "dangerous" and guess == "dangerous" for label, guess in zip(labels, predicted, strict=True))
    raw_recall = raw_hits / dangerous_total if dangerous_total else 0.0
    best_floor: float | None = None
    best_false = sum(label == "safe" and guess == "dangerous" for label, guess in zip(labels, predicted, strict=True))
    for floor in CONFIDENCE_FLOORS:
        if floor is None:
            continue
        kept = top >= floor
        hits = sum(
            label == "dangerous" and guess == "dangerous" and keep
            for label, guess, keep in zip(labels, predicted, kept, strict=True)
        )
        false_high = sum(
            label == "safe" and guess == "dangerous" and keep
            for label, guess, keep in zip(labels, predicted, kept, strict=True)
        )
        recall = hits / dangerous_total if dangerous_total else 0.0
        if recall + 1e-9 < 0.85 * raw_recall:
            continue
        if false_high < best_false:
            best_false = false_high
            best_floor = floor
    return best_floor


def _uncertainty_margin(pipeline: Pipeline, examples: list[Example], structural: bool) -> float:
    if not examples:
        return 0.0
    predicted, probabilities = _predict(pipeline, [item.text for item in examples], structural)
    ordered = np.partition(probabilities, -2, axis=1)
    margins = ordered[:, -1] - ordered[:, -2]
    errors = margins[np.array(predicted) != np.array([item.label for item in examples])]
    if errors.size == 0:
        return 0.0
    return float(np.quantile(errors, 0.75))


def _score_split(pipeline: Pipeline, examples: list[Example], structural: bool) -> dict:
    predicted, _ = _predict(pipeline, [item.text for item in examples], structural)
    report = {
        "all": _pack(examples, predicted),
        "by_language": {},
    }
    languages = sorted({item.language for item in examples})
    for language in languages:
        chosen = [(item, label) for item, label in zip(examples, predicted, strict=True) if item.language == language]
        if not chosen:
            continue
        subset = [item for item, _ in chosen]
        guesses = [label for _, label in chosen]
        report["by_language"][language] = _pack(subset, guesses)
        report["by_language"][language]["roles"] = _role_harm(subset, guesses)
    return report


def _auxiliary_calibration(pipeline: Pipeline, train: list[Example], validation: list[Example], structural: bool) -> dict:
    """Measure sigmoid calibration without replacing the shipped pipeline."""

    if not train or not validation:
        return {"status": "not_measured", "error_type": "empty_split", "shipped": False}
    try:
        calibrated = CalibratedClassifierCV(pipeline, method="sigmoid", cv=3)
        calibrated.fit(
            [model_input(item.text, structural) for item in train],
            [item.label for item in train],
        )
        probabilities = calibrated.predict_proba([model_input(item.text, structural) for item in validation])
        confidence = probabilities.max(axis=1)
        predicted = calibrated.classes_[probabilities.argmax(axis=1)]
        truth = np.array([item.label for item in validation])
        correct = (predicted == truth).astype(float)
        total = len(validation)
        edges = np.linspace(0.0, 1.0, 11)
        error = 0.0
        for index in range(10):
            lower, upper = edges[index], edges[index + 1]
            if index == 9:
                mask = (confidence >= lower) & (confidence <= upper)
            else:
                mask = (confidence >= lower) & (confidence < upper)
            count = int(mask.sum())
            if count == 0:
                continue
            error += (count / total) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
        return {
            "status": "measured",
            "validation_ece": round(float(error), 6),
            "accepted_for_display": calibration_accepted(float(error)) and total >= 200,
            "shipped": False,
        }
    except Exception as exc:  # noqa: BLE001 - a failed calibration attempt is a result, not a crash
        return {"status": "not_measured", "error_type": type(exc).__name__, "shipped": False}


def _probe(pipeline: Pipeline, structural: bool, floor: float | None) -> dict:
    predicted, probabilities = _predict(pipeline, [LOCKED_PROBE], structural)
    top = float(probabilities[0].max())
    raw = predicted[0]
    withheld = floor is not None and top < floor
    risk = "unknown" if withheld else RISK_BY_LABEL[raw]
    cues = [] if withheld else explain_cues(pipeline, LOCKED_PROBE, raw, structural)
    visible = LOCKED_PROBE.lower()
    return {
        "raw_label": raw,
        "top_probability_or_margin_softmax": round(top, 4),
        "shown_risk": risk,
        "withheld_for_low_confidence": withheld,
        "indicators": detect_indicators(LOCKED_PROBE),
        "cues": cues,
        "cues_are_substrings": all(cue in visible for cue in cues),
    }


def run() -> dict:
    legacy_model = ARTIFACT_DIR / "model.joblib"
    legacy_card = ARTIFACT_DIR / "model_card.json"
    before = {"model": _sha256(legacy_model), "card": _sha256(legacy_card)}
    adaption_train, _ = load_training_rows(TRAIN_FILE)
    adaption_eval, _ = load_evaluation_rows(EVAL_EN_FILE, EVAL_BILINGUAL_FILE)
    adaption = prepare_splits(adaption_train, adaption_eval)
    research = load_research_examples()
    adaption_test_templates = {item.template for item in adaption.test}
    adaption_fit_templates = {item.template for item in adaption.train + adaption.validation}
    dropped: Counter[str] = Counter()
    for part, rows in research.items():
        forbidden = adaption_test_templates if part != "test" else adaption_fit_templates | adaption_test_templates
        kept = []
        for item in rows:
            if item.template in forbidden:
                dropped[part] += 1
                continue
            kept.append(item)
        research[part] = kept

    train = [*adaption.train, *research["train"]]
    validation_pool = [*adaption.validation, *research["validation"]]
    validation_for_c = [item for item in validation_pool if item.language in TARGET_LANGUAGES]
    specs = (
        ("tfidf-logreg-0002", "logreg", False),
        ("tfidf-logreg-0002m", "logreg", True),
        ("tfidf-linearsvm-0001", "svm", False),
        ("tfidf-linearsvm-0001m", "svm", True),
    )
    candidates = []
    for model_version, kind, structural in specs:
        selected_c, c_scores = _select_c(kind, train, validation_for_c, structural)
        pipeline = _fit(kind, [item.text for item in train], [item.label for item in train], selected_c, structural)
        predicted, _ = _predict(pipeline, [item.text for item in validation_for_c], structural)
        metrics = classification_metrics([item.label for item in validation_for_c], predicted)
        candidates.append(
            {
                "model_version": model_version,
                "kind": kind,
                "structural_markers": structural,
                "selected_c": selected_c,
                "validation_macro_f1_by_c": c_scores,
                "validation_metrics": metrics,
                "pipeline": pipeline,
            }
        )

    simple = next(item for item in candidates if item["model_version"] == "tfidf-logreg-0002")
    eligible = [
        item
        for item in candidates
        if item["validation_metrics"]["per_label"]["dangerous"]["precision"] >= PRECISION_FLOOR
    ]
    winner = None
    if eligible:
        winner = max(
            eligible,
            key=lambda item: (
                item["validation_metrics"]["per_label"]["dangerous"]["recall"],
                item["validation_metrics"]["macro_f1"],
            ),
        )
        simple_recall = simple["validation_metrics"]["per_label"]["dangerous"]["recall"]
        winner_recall = winner["validation_metrics"]["per_label"]["dangerous"]["recall"]
        simple_eligible = simple in eligible
        if simple_eligible and winner_recall <= simple_recall + RECALL_TIE:
            winner = simple

    floor = None
    margin = 0.0
    if winner is not None:
        floor = _select_floor(winner["pipeline"], validation_for_c, winner["structural_markers"])
        margin = _uncertainty_margin(winner["pipeline"], validation_for_c, winner["structural_markers"])
        winner["min_top_probability"] = floor
        winner["uncertainty_margin"] = margin
        winner["validation_ece"] = expected_calibration_error(
            winner["pipeline"],
            [item.text for item in validation_for_c],
            [item.label for item in validation_for_c],
        ) if not winner["structural_markers"] else None
        if winner["structural_markers"]:
            # The shared ECE helper preprocesses without markers. Score the real input here.
            predicted, probabilities = _predict(
                winner["pipeline"],
                [item.text for item in validation_for_c],
                True,
            )
            confidence = probabilities.max(axis=1)
            truth = np.array([item.label for item in validation_for_c])
            correct = (np.array(predicted) == truth).astype(float)
            edges = np.linspace(0.0, 1.0, 11)
            error = 0.0
            total = len(validation_for_c)
            for index in range(10):
                lower, upper = edges[index], edges[index + 1]
                upper_check = confidence <= upper if index == 9 else confidence < upper
                mask = (confidence >= lower) & upper_check
                count = int(mask.sum())
                if count:
                    error += (count / total) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
            winner["validation_ece"] = float(error)

    legacy = joblib.load(legacy_model)
    legacy_pipeline = legacy["pipeline"]
    adaption_ru_test = _language(adaption.test, "ru")
    legacy_ru_predicted, _ = _predict(legacy_pipeline, [item.text for item in adaption_ru_test], False)
    legacy_ru = _pack(adaption_ru_test, legacy_ru_predicted)
    research_legacy = _score_split(legacy_pipeline, research["test"], False)

    winner_report = None
    gate = {"passed": False, "reasons": ["no_eligible_candidate"]}
    if winner is not None:
        winner_ru_predicted, _ = _predict(
            winner["pipeline"],
            [item.text for item in adaption_ru_test],
            winner["structural_markers"],
        )
        winner_ru = _pack(adaption_ru_test, winner_ru_predicted)
        dangerous = winner_ru["metrics"]["per_label"]["dangerous"]
        reasons = []
        if dangerous["recall"] < ADAPTION_RU_RECALL_FLOOR:
            reasons.append("adaption_russian_recall")
        if dangerous["precision"] < ADAPTION_RU_PRECISION_FLOOR:
            reasons.append("adaption_russian_precision")
        if winner_ru["metrics"]["macro_f1"] < ADAPTION_RU_MACRO_FLOOR:
            reasons.append("adaption_russian_macro_f1")
        gate = {"passed": not reasons, "reasons": reasons}
        winner_report = {
            "adaption_russian_test": winner_ru,
            "research_test": _score_split(winner["pipeline"], research["test"], winner["structural_markers"]),
            "research_validation": _score_split(
                winner["pipeline"],
                research["validation"],
                winner["structural_markers"],
            ),
        }
        card = {
            "model_version": winner["model_version"],
            "algorithm": winner["kind"],
            "structural_markers": winner["structural_markers"],
            "random_seed": 42,
            "selected_c": winner["selected_c"],
            "validation_macro_f1_by_c": winner["validation_macro_f1_by_c"],
            "uncertainty_margin": round(margin, 6),
            "min_top_probability": floor,
            "validation_ece": round(float(winner["validation_ece"]), 6),
            "confidence_calibrated": calibration_accepted(float(winner["validation_ece"])),
            "risk_score_displayed": False,
            "trained_on": "adaption_train_plus_researcher_scenarios",
            "experiment_date": date.today().isoformat(),
            "counts": {
                "adaption_train": len(adaption.train),
                "research_train": len(research["train"]),
                "validation_for_selection": len(validation_for_c),
                "research_test": len(research["test"]),
            },
            "packages": {"scikit-learn": version("scikit-learn"), "numpy": version("numpy")},
            "limitations": [
                "synthetic_training_data",
                "researcher_authored_scenarios",
                "kazakh_not_field_data",
                "kazakh_not_evaluated",
                "confidence_not_shown_as_percent",
            ],
        }
        artifact_name = f"{winner['model_version']}.joblib"
        card_name = f"{winner['model_version']}.json"
        joblib.dump(
            {
                "pipeline": winner["pipeline"],
                "model_version": winner["model_version"],
                "uncertainty_margin": margin,
                "confidence_calibrated": card["confidence_calibrated"],
                "min_top_probability": floor,
            },
            ARTIFACT_DIR / artifact_name,
        )
        (ARTIFACT_DIR / card_name).write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        if gate["passed"]:
            pointer = {
                "model_version": winner["model_version"],
                "artifact": artifact_name,
                "card": card_name,
            }
            (ARTIFACT_DIR / "active_model.json").write_text(
                json.dumps(pointer, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            gate["activated"] = winner["model_version"]
        else:
            gate["activated"] = "tfidf-logreg-0001"

    after = {"model": _sha256(legacy_model), "card": _sha256(legacy_card)}
    if before != after:
        raise SystemExit("tfidf-logreg-0001 bytes changed")

    summary = {
        "legacy_version": "tfidf-logreg-0001",
        "legacy_sha256_unchanged": before == after,
        "legacy_adaption_russian_test": legacy_ru,
        "legacy_research_test": research_legacy,
        "research_counts": {part: len(rows) for part, rows in research.items()},
        "research_overlap_with_adaption_test_templates_dropped": dict(dropped),
        "research_split_overlap": {
            "train_validation": overlap_report(research["train"], research["validation"]),
            "train_test": overlap_report(research["train"], research["test"]),
            "validation_test": overlap_report(research["validation"], research["test"]),
        },
        "candidates": [
            {
                "model_version": item["model_version"],
                "structural_markers": item["structural_markers"],
                "selected_c": item["selected_c"],
                "validation_macro_f1_by_c": item["validation_macro_f1_by_c"],
                "validation_macro_f1": item["validation_metrics"]["macro_f1"],
                "validation_dangerous_precision": item["validation_metrics"]["per_label"]["dangerous"]["precision"],
                "validation_dangerous_recall": item["validation_metrics"]["per_label"]["dangerous"]["recall"],
            }
            for item in candidates
        ],
        "selected_on_validation": None if winner is None else winner["model_version"],
        "min_top_probability": floor,
        "gate": gate,
        "selected_test": winner_report,
        "locked_probe": {
            "legacy": _probe(legacy_pipeline, False, None),
            "selected": None
            if winner is None
            else _probe(winner["pipeline"], winner["structural_markers"], floor),
        },
        "transformer": {
            "ran": False,
            "reason": "16 GB RAM, 8 CPU cores, about 15 GB free disk. Fine-tuning was not started without consent.",
        },
    }
    if winner is not None:
        summary["auxiliary_calibration"] = _auxiliary_calibration(
            winner["pipeline"],
            train,
            validation_for_c,
            winner["structural_markers"],
        )
    (ARTIFACT_DIR / "stage-2-1-comparison.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


if __name__ == "__main__":
    result = run()
    print(
        json.dumps(
            {
                "selected": result["selected_on_validation"],
                "gate": result["gate"],
                "research_counts": result["research_counts"],
                "legacy_sha256_unchanged": result["legacy_sha256_unchanged"],
                "probe": result["locked_probe"],
            },
            ensure_ascii=False,
        )
    )
