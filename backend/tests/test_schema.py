import app.models  # noqa: F401
from sqlalchemy.orm import configure_mappers

from app.db.base import Base

EXPECTED_TABLES = {
    "users",
    "user_settings",
    "model_versions",
    "analysis_records",
    "detected_threats",
    "analysis_indicators",
    "analysis_recommendations",
    "audit_events",
}

FORBIDDEN_CONTENT_COLUMNS = {
    "text",
    "raw_text",
    "content",
    "message",
    "body",
    "screenshot",
    "image",
    "audio",
    "recording",
    "password",
    "otp",
    "secret",
}


def test_schema_contains_planned_tables():
    configure_mappers()
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_analysis_records_do_not_store_raw_submissions():
    columns = set(Base.metadata.tables["analysis_records"].columns.keys())
    assert columns.isdisjoint(FORBIDDEN_CONTENT_COLUMNS)
    assert "history_consent" in columns
    assert "risk_score" in columns
