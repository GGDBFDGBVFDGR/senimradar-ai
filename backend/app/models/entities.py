import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class User(Base):
    """Anonymous identity placeholder. Passwords are intentionally absent."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    settings: Mapped["UserSettings | None"] = relationship(back_populates="user", uselist=False)
    analyses: Mapped[list["AnalysisRecord"]] = relationship(back_populates="user")


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        CheckConstraint("locale IN ('ru', 'kk', 'en')", name="ck_user_settings_locale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    locale: Mapped[str] = mapped_column(String(8), nullable=False, server_default=text("'ru'"))
    history_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    allow_third_party_ai: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="settings")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
        CheckConstraint(
            "status IN ('unconfigured', 'active', 'retired')",
            name="ck_model_versions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    analyses: Mapped[list["AnalysisRecord"]] = relationship(back_populates="model_version")


class AnalysisRecord(Base):
    """Analysis metadata only. Raw messages and files are not columns of this table."""

    __tablename__ = "analysis_records"
    __table_args__ = (
        CheckConstraint(
            "input_type IN ('text', 'screenshot', 'url', 'voice')",
            name="ck_analysis_records_input_type",
        ),
        CheckConstraint(
            "risk_level IS NULL OR risk_level IN ('low', 'medium', 'high', 'unknown')",
            name="ck_analysis_records_risk_level",
        ),
        CheckConstraint(
            "content_language IS NULL OR content_language IN ('ru', 'kk', 'en', 'unknown')",
            name="ck_analysis_records_language",
        ),
        Index("ix_analysis_records_user_id", "user_id"),
        Index("ix_analysis_records_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    input_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_consent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User | None] = relationship(back_populates="analyses")
    model_version: Mapped[ModelVersion | None] = relationship(back_populates="analyses")
    threats: Mapped[list["DetectedThreat"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    indicators: Mapped[list["AnalysisIndicator"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list["AnalysisRecommendation"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class DetectedThreat(Base):
    __tablename__ = "detected_threats"
    __table_args__ = (
        UniqueConstraint("analysis_id", "threat_code", name="uq_detected_threats_analysis_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    threat_code: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    analysis: Mapped[AnalysisRecord] = relationship(back_populates="threats")


class AnalysisIndicator(Base):
    __tablename__ = "analysis_indicators"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "indicator_code",
            name="uq_analysis_indicators_analysis_code",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    analysis: Mapped[AnalysisRecord] = relationship(back_populates="indicators")


class AnalysisRecommendation(Base):
    __tablename__ = "analysis_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "recommendation_code",
            name="uq_analysis_recommendations_analysis_code",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_code: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    analysis: Mapped[AnalysisRecord] = relationship(back_populates="recommendations")


class AuditEvent(Base):
    """Operational events. The metadata column must not contain submitted content."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_created_at", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
