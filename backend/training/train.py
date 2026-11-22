import hashlib
import json
import time
from importlib.metadata import version

import joblib

from training.config import (
    ARTIFACT_DIR,
    EVAL_BILINGUAL_FILE,
    EVAL_EN_FILE,
    MODEL_VERSION,
    TRAIN_FILE,
)
from training.dataset import load_evaluation_rows, load_training_rows, tally
from training.evaluate import classification_metrics, metrics_by_language, predict_labels, rule_baseline
from training.model import (
    calibration_accepted,
    expected_calibration_error,
    fit_pipeline,
    select_c,
    uncertainty_margin,
)
from training.split import prepare_splits


def _sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mean_inference_ms(pipeline, texts: list[str]) -> float:
    sample = texts[:100]
    if not sample:
        return 0.0
    started = time.perf_counter()
    pipeline.predict(sample)
    elapsed = time.perf_counter() - started
    return round((elapsed / len(sample)) * 1000, 3)


def train() -> dict:
    for path in (TRAIN_FILE, EVAL_EN_FILE, EVAL_BILINGUAL_FILE):
        if not path.is_file():
            raise SystemExit(f"Missing dataset file: {path.name}")

    train_rows, train_rejected = load_training_rows(TRAIN_FILE)
    eval_rows, eval_rejected = load_evaluation_rows(EVAL_EN_FILE, EVAL_BILINGUAL_FILE)
    split = prepare_splits(train_rows, eval_rows)
    best_c, validation_scores = select_c(
        [item.text for item in split.train],
        [item.label for item in split.train],
        [item.text for item in split.validation],
        [item.label for item in split.validation],
    )
    pipeline = fit_pipeline(
        [item.text for item in split.train],
        [item.label for item in split.train],
        best_c,
    )
    validation_predicted = predict_labels(pipeline, split.validation)
    test_predicted = predict_labels(pipeline, split.test)
    margin = uncertainty_margin(
        pipeline,
        [item.text for item in split.validation],
        [item.label for item in split.validation],
    )
    ece = expected_calibration_error(
        pipeline,
        [item.text for item in split.validation],
        [item.label for item in split.validation],
    )
    baseline_predicted = [rule_baseline(item.text) for item in split.test]
    prepared_test = [item.text for item in split.test]
    # predict_labels already preprocesses. Time the same public preprocessing path.
    from app.ml.preprocess import preprocess_text

    inference_ms = _mean_inference_ms(pipeline, [preprocess_text(text) for text in prepared_test])

    card = {
        "model_version": MODEL_VERSION,
        "algorithm": "tfidf_word_1_2_plus_char_wb_3_5_logistic_regression",
        "random_seed": 42,
        "selected_c": best_c,
        "validation_macro_f1_by_c": validation_scores,
        "uncertainty_margin": round(margin, 6),
        "validation_ece": round(ece, 6),
        "confidence_calibrated": calibration_accepted(ece),
        "risk_score_displayed": False,
        "dataset": {
            "name": "dokster/adaption-scam-dataset-ru-en-v1",
            "license": "Apache-2.0",
            "nature": "synthetic_template_generated",
            "files": {
                "train_0.jsonl": {"sha256": _sha256(TRAIN_FILE)},
                "eval_en.jsonl": {"sha256": _sha256(EVAL_EN_FILE)},
                "eval_ru_en.jsonl": {"sha256": _sha256(EVAL_BILINGUAL_FILE)},
            },
            "rejected": {"train": train_rejected, "eval": eval_rejected},
            "dropped_train_rows_overlapping_test_templates": split.dropped_train_overlap,
        },
        "counts": {
            "train": tally(split.train),
            "validation": tally(split.validation),
            "test": tally(split.test),
        },
        "validation_metrics": classification_metrics(
            [item.label for item in split.validation],
            validation_predicted,
        ),
        "test_metrics": classification_metrics(
            [item.label for item in split.test],
            test_predicted,
        ),
        "test_metrics_by_language": metrics_by_language(split.test, test_predicted),
        "baseline_test_metrics": classification_metrics(
            [item.label for item in split.test],
            baseline_predicted,
        ),
        "packages": {
            "scikit-learn": version("scikit-learn"),
            "numpy": version("numpy"),
        },
        "mean_inference_ms_on_test_sample": inference_ms,
        "limitations": [
            "synthetic_training_data",
            "kazakh_not_evaluated",
            "english_and_russian_templates_are_not_live_traffic",
            "confidence_not_shown_as_percent",
        ],
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACT_DIR / "model.joblib"
    if model_path.is_file():
        existing = joblib.load(model_path)
        if existing.get("model_version") == "tfidf-logreg-0001":
            raise SystemExit("Refusing to overwrite artifact tfidf-logreg-0001")
    joblib.dump(
        {
            "pipeline": pipeline,
            "model_version": MODEL_VERSION,
            "uncertainty_margin": margin,
            "confidence_calibrated": card["confidence_calibrated"],
        },
        model_path,
    )
    card["artifact_bytes"] = model_path.stat().st_size
    card_path = ARTIFACT_DIR / "model_card.json"
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    return card


if __name__ == "__main__":
    trained = train()
    print(
        json.dumps(
            {
                "model_version": trained["model_version"],
                "test_macro_f1": trained["test_metrics"]["macro_f1"],
                "baseline_macro_f1": trained["baseline_test_metrics"]["macro_f1"],
                "validation_ece": trained["validation_ece"],
                "confidence_calibrated": trained["confidence_calibrated"],
                "artifact_bytes": trained["artifact_bytes"],
                "counts": trained["counts"],
            },
            ensure_ascii=False,
        )
    )
