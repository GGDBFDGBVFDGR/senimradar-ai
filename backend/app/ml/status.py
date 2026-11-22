"""Availability of the fraud-analysis model.

Stage 1 does not load a classifier. Returning True without a real inference
implementation is intentionally unsupported: the API must stay unavailable
instead of inventing a risk score.
"""


def text_model_configured() -> bool:
    return False
