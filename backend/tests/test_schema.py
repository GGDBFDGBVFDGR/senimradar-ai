import app.models  # noqa: F401
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateTable

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


def test_tables_compile_for_mysql_utf8mb4():
    configure_mappers()
    dialect = mysql.dialect()
    for table in Base.metadata.tables.values():
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert "ENGINE=InnoDB" in ddl
        assert "utf8mb4" in ddl
        assert "CHAR(36)" in ddl
        assert "gen_random_uuid" not in ddl
