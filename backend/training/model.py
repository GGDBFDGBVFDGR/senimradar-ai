import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import FeatureUnion, Pipeline

from app.ml.preprocess import preprocess_text
from training.config import (
    CALIBRATION_BINS,
    CALIBRATION_ECE_LIMIT,
    C_GRID,
    CHAR_FEATURES,
    MIN_DF,
    RANDOM_SEED,
    WORD_FEATURES,
)


def build_pipeline(c_value: float, min_df: int = MIN_DF) -> Pipeline:
    features = FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    min_df=min_df,
                    max_features=WORD_FEATURES,
                    sublinear_tf=True,
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=min_df,
                    max_features=CHAR_FEATURES,
                    sublinear_tf=True,
                ),
            ),
        ]
    )
    classifier = LogisticRegression(
        C=c_value,
        class_weight="balanced",
        max_iter=1000,
        solver="lbfgs",
        random_state=RANDOM_SEED,
    )
    return Pipeline([("features", features), ("clf", classifier)])


def fit_pipeline(texts: list[str], labels: list[str], c_value: float, min_df: int = MIN_DF) -> Pipeline:
    pipeline = build_pipeline(c_value, min_df=min_df)
    pipeline.fit([preprocess_text(text) for text in texts], labels)
    return pipeline


def select_c(
    train_texts: list[str],
    train_labels: list[str],
    validation_texts: list[str],
    validation_labels: list[str],
) -> tuple[float, dict[str, float]]:
    scores: dict[str, float] = {}
    best_c = C_GRID[0]
    best_score = -1.0
    prepared_validation = [preprocess_text(text) for text in validation_texts]
    for c_value in C_GRID:
        pipeline = fit_pipeline(train_texts, train_labels, c_value)
        predicted = pipeline.predict(prepared_validation)
        score = float(f1_score(validation_labels, predicted, average="macro", zero_division=0))
        scores[str(c_value)] = round(score, 6)
        if score > best_score:
            best_score = score
            best_c = c_value
    return best_c, scores


def prediction_margins(pipeline: Pipeline, texts: list[str]) -> np.ndarray:
    probabilities = pipeline.predict_proba([preprocess_text(text) for text in texts])
    if probabilities.shape[1] == 1:
        return np.ones(len(texts))
    ordered = np.partition(probabilities, -2, axis=1)
    return ordered[:, -1] - ordered[:, -2]


def uncertainty_margin(pipeline: Pipeline, texts: list[str], labels: list[str]) -> float:
    predicted = pipeline.predict([preprocess_text(text) for text in texts])
    margins = prediction_margins(pipeline, texts)
    errors = margins[np.array(predicted) != np.array(labels)]
    if errors.size == 0:
        return 0.0
    return float(np.quantile(errors, 0.75))


def expected_calibration_error(pipeline: Pipeline, texts: list[str], labels: list[str]) -> float:
    probabilities = pipeline.predict_proba([preprocess_text(text) for text in texts])
    confidence = probabilities.max(axis=1)
    predicted = pipeline.classes_[probabilities.argmax(axis=1)]
    correct = (predicted == np.array(labels)).astype(float)
    edges = np.linspace(0.0, 1.0, CALIBRATION_BINS + 1)
    total = len(texts)
    if total == 0:
        return 1.0
    error = 0.0
    for index in range(CALIBRATION_BINS):
        lower = edges[index]
        upper = edges[index + 1]
        if index == CALIBRATION_BINS - 1:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)
        count = int(mask.sum())
        if count == 0:
            continue
        error += (count / total) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return float(error)


def calibration_accepted(ece: float) -> bool:
    return ece <= CALIBRATION_ECE_LIMIT
