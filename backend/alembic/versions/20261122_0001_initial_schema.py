"""Initial SenimRadar schema for MySQL. Raw submitted content is intentionally not stored.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MYSQL_KW = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}
UUID_DEFAULT = sa.text("(UUID())")
TIMESTAMP = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        **MYSQL_KW,
    )
    op.create_table(
        "user_settings",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=False),
        sa.Column("locale", sa.String(length=8), server_default=sa.text("'ru'"), nullable=False),
        sa.Column("history_enabled", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("allow_third_party_ai", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.CheckConstraint("locale IN ('ru', 'kk', 'en')", name="ck_user_settings_locale"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_settings_user_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_user_settings"),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
        **MYSQL_KW,
    )
    op.create_table(
        "model_versions",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.CheckConstraint(
            "status IN ('unconfigured', 'active', 'retired')",
            name="ck_model_versions_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_model_versions"),
        sa.UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
        **MYSQL_KW,
    )
    op.create_table(
        "analysis_records",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=True),
        sa.Column("model_version_id", sa.CHAR(length=36), nullable=True),
        sa.Column("input_type", sa.String(length=32), nullable=False),
        sa.Column("content_language", sa.String(length=16), nullable=True),
        sa.Column("risk_level", sa.String(length=16), nullable=True),
        sa.Column("risk_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("history_consent", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.CheckConstraint(
            "input_type IN ('text', 'screenshot', 'url', 'voice')",
            name="ck_analysis_records_input_type",
        ),
        sa.CheckConstraint(
            "risk_level IS NULL OR risk_level IN ('low', 'medium', 'high', 'unknown')",
            name="ck_analysis_records_risk_level",
        ),
        sa.CheckConstraint(
            "content_language IS NULL OR content_language IN ('ru', 'kk', 'en', 'unknown')",
            name="ck_analysis_records_language",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_analysis_records_user_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name="fk_analysis_records_model_version_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_records"),
        **MYSQL_KW,
    )
    op.create_index("ix_analysis_records_user_id", "analysis_records", ["user_id"])
    op.create_index("ix_analysis_records_created_at", "analysis_records", ["created_at"])
    op.create_table(
        "detected_threats",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("analysis_id", sa.CHAR(length=36), nullable=False),
        sa.Column("threat_code", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analysis_records.id"],
            name="fk_detected_threats_analysis_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_detected_threats"),
        sa.UniqueConstraint("analysis_id", "threat_code", name="uq_detected_threats_analysis_code"),
        **MYSQL_KW,
    )
    op.create_table(
        "analysis_indicators",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("analysis_id", sa.CHAR(length=36), nullable=False),
        sa.Column("indicator_code", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analysis_records.id"],
            name="fk_analysis_indicators_analysis_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_indicators"),
        sa.UniqueConstraint("analysis_id", "indicator_code", name="uq_analysis_indicators_analysis_code"),
        **MYSQL_KW,
    )
    op.create_table(
        "analysis_recommendations",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("analysis_id", sa.CHAR(length=36), nullable=False),
        sa.Column("recommendation_code", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analysis_records.id"],
            name="fk_analysis_recommendations_analysis_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_analysis_recommendations"),
        sa.UniqueConstraint(
            "analysis_id",
            "recommendation_code",
            name="uq_analysis_recommendations_analysis_code",
        ),
        **MYSQL_KW,
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.CHAR(length=36), server_default=UUID_DEFAULT, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=TIMESTAMP, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        **MYSQL_KW,
    )
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_table("analysis_recommendations")
    op.drop_table("analysis_indicators")
    op.drop_table("detected_threats")
    op.drop_index("ix_analysis_records_created_at", table_name="analysis_records")
    op.drop_index("ix_analysis_records_user_id", table_name="analysis_records")
    op.drop_table("analysis_records")
    op.drop_table("model_versions")
    op.drop_table("user_settings")
    op.drop_table("users")
