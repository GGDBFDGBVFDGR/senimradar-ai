import json
from pathlib import Path

import joblib

from app.ml.indicators import detect_indicators
from app.ml.inference import analyze_message
from app.ml.preprocess import preprocess_text
from training.research import assigned_split, load_research_examples, overlap_report


def test_password_request_is_not_labeled_as_a_code_request():
    indicators = detect_indicators("Откройте страницу и введите пароль от кабинета сегодня.")
    assert "password_request" in indicators
    assert "otp_request" not in indicators


def test_warning_is_not_treated_as_a_request():
    indicators = detect_indicators("Не сообщайте пароль и не переводите деньги по звонку.")
    assert "fraud_warning" in indicators
    assert "password_request" not in indicators
    assert "payment_request" not in indicators


def test_direct_request_is_not_relabeled_as_a_warning():
    indicators = detect_indicators("Никому не говорите, но переведите деньги на эту карту.")
    assert "payment_request" in indicators
    assert "fraud_warning" not in indicators


def test_stage2_artifact_is_preserved():
    artifact_dir = Path(__file__).resolve().parents[1] / "app" / "ml" / "artifacts"
    payload = joblib.load(artifact_dir / "model.joblib")
    card = json.loads((artifact_dir / "model_card.json").read_text(encoding="utf-8"))
    assert payload["model_version"] == "tfidf-logreg-0001"
    assert card["model_version"] == "tfidf-logreg-0001"


def test_research_families_do_not_cross_splits():
    grouped = load_research_examples()
    assert overlap_report(grouped["train"], grouped["test"]) == {"shared_groups": 0, "shared_templates": 0}
    assert overlap_report(grouped["validation"], grouped["test"]) == {"shared_groups": 0, "shared_templates": 0}
    assert overlap_report(grouped["train"], grouped["validation"]) == {"shared_groups": 0, "shared_templates": 0}
    families = {item.group_id for rows in grouped.values() for item in rows}
    assert len(families) >= 3
    assert assigned_split("ru-warn-phone-11") == "test"


def test_displayed_cues_are_contiguous_words(client):
    message = "Служба безопасности банка: карта заблокирована, срочно сообщите код и переведите деньги"
    response = client.post("/api/v1/analysis/text", json={"text": message, "language": "ru"})
    assert response.status_code == 200
    visible = preprocess_text(message)
    for cue in response.json()["cues"]:
        assert cue in visible
        assert " " not in cue or all(len(part) >= 3 for part in cue.split(" "))
        assert not any(len(part) < 3 for part in cue.split(" "))


def test_kazakh_result_stays_unevaluated_after_stage21(client):
    body = analyze_message("Сәлеметсіз бе, шұғыл түрде кодты жіберіңіз және ақша аударыңыз", "kk")
    assert body["risk_level"] == "unknown"
    assert body["language_evaluation"] == "not_evaluated"
    assert body["risk_score"] is None
