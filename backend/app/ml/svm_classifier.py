"""Linear SVM whose margins can be ranked. The softmax is not a calibrated probability."""

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.svm import LinearSVC
from sklearn.utils.validation import check_is_fitted


class MarginSoftmaxSVM(BaseEstimator, ClassifierMixin):
    def __init__(self, c_value: float = 1.0) -> None:
        self.c_value = c_value

    def fit(self, features, labels):
        estimator = LinearSVC(
            C=self.c_value,
            class_weight="balanced",
            dual="auto",
            max_iter=5000,
            random_state=42,
        )
        estimator.fit(features, labels)
        self.svc_ = estimator
        self.classes_ = estimator.classes_
        self.coef_ = estimator.coef_
        self.intercept_ = estimator.intercept_
        return self

    def decision_function(self, features):
        check_is_fitted(self, "svc_")
        return self.svc_.decision_function(features)

    def predict(self, features):
        check_is_fitted(self, "svc_")
        return self.svc_.predict(features)

    def predict_proba(self, features):
        scores = np.asarray(self.decision_function(features), dtype=float)
        if scores.ndim == 1:
            scores = np.column_stack([-scores, scores])
        scores = scores - scores.max(axis=1, keepdims=True)
        shifted = np.exp(scores)
        return shifted / shifted.sum(axis=1, keepdims=True)
