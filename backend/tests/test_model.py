import numpy as np
import pytest

from app.ml.preprocess import looks_kazakh, preprocess_text
from training.dataset import Example, extract_message
from training.model import fit_pipeline
from training.split import prepare_splits


def test_kazakh_text_is_not_given_an_evaluated_risk(client):
    message = "Сәлеметсіз бе, шұғыл түрде кодты жіберіңіз және ақша аударыңыз"
    assert looks_kazakh(message)
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": message, "language": "kk"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "unknown"
    assert body["language_evaluation"] == "not_evaluated"
    assert "kazakh_not_evaluated" in body["limitations"]
    assert body["risk_score"] is None
    assert message not in response.text


def test_english_holdout_is_not_shown_as_a_verdict(client):
    message = "Bank security: your card is blocked. Send the one-time code and transfer the money now."
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": message, "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "unknown"
    assert body["language_evaluation"] == "evaluated"
    assert "english_holdout_weak" in body["limitations"]
    assert body["risk_score"] is None
    assert message not in response.text


def test_short_text_is_insufficient(client):
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": "Сәлем", "language": "kk"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient"
    assert body["risk_level"] == "unknown"
    assert "insufficient_text" in body["limitations"]


def test_unicode_kazakh_letters_do_not_crash_preprocessing():
    processed = preprocess_text("Қайырлы күн, әріптес!")
    assert "ә" in processed
    assert "қ" in processed


def test_training_fit_is_reproducible():
    texts = [
        "urgent bank code transfer now",
        "срочно код банка перевод",
        "please confirm the password today",
        "подтвердите пароль сегодня",
        "lunch is at noon near the office",
        "обед будет в офисе после встречи",
        "the parcel is at the desk",
        "книга лежит на столе у окна",
        "check this unusual notice tomorrow",
        "проверьте странное уведомление завтра",
        "your account needs a quick review",
        "нужно спокойно проверить кабинет",
    ]
    labels = [
        "dangerous",
        "dangerous",
        "suspicious",
        "suspicious",
        "safe",
        "safe",
        "safe",
        "needs_check",
        "needs_check",
        "needs_check",
        "suspicious",
        "dangerous",
    ]
    first = fit_pipeline(texts, labels, 1.0, min_df=1)
    second = fit_pipeline(texts, labels, 1.0, min_df=1)
    assert np.allclose(first.named_steps["clf"].coef_, second.named_steps["clf"].coef_)


def test_related_templates_are_not_split_across_train_and_validation():
    rows = []
    for index in range(12):
        rows.append(
            Example(
                example_id=f"case_{index}",
                group_id=f"case_{index}",
                language="en",
                label="safe",
                text=f"ordinary note number {index} for the calendar",
                template=f"ordinary-{index}",
                split_source="train_file",
            )
        )
        rows.append(
            Example(
                example_id=f"case_{index}_ru",
                group_id=f"case_{index}",
                language="ru",
                label="safe",
                text=f"обычная заметка номер {index} для календаря",
                template=f"ordinary-{index}-ru",
                split_source="train_file",
            )
        )
    report = prepare_splits(rows, [])
    train_groups = {item.group_id for item in report.train}
    validation_groups = {item.group_id for item in report.validation}
    assert train_groups.isdisjoint(validation_groups)
    assert len(report.train) + len(report.validation) == len(rows)


def test_message_extractor_reads_the_dataset_wrapper():
    wrapped = (
        "/no_think Analyze this message for scam risk: "
        "Library book is ready at the desk. "
        "Return only the JSON object."
    )
    assert extract_message(wrapped) == "Library book is ready at the desk."


def test_analysis_does_not_insert_a_database_row(client):
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    from app.db.session import engine

    try:
        with engine.connect() as connection:
            before = connection.execute(text("SELECT COUNT(*) FROM analysis_records")).scalar()
    except OperationalError:
        pytest.skip("database unavailable")
    response = client.post(
        "/api/v1/analysis/text",
        json={"text": "Это сообщение не должно сохраниться в базе", "language": "ru"},
    )
    assert response.status_code == 200
    with engine.connect() as connection:
        after = connection.execute(text("SELECT COUNT(*) FROM analysis_records")).scalar()
    assert after == before
