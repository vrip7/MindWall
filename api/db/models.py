"""
MindWall — ORM Models
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

SQLAlchemy ORM model definitions for all database entities.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SenderBaseline(Base):
    __tablename__ = "sender_baselines"
    __table_args__ = (
        UniqueConstraint("recipient_email", "sender_email", name="uq_baseline_pair"),
        Index("idx_baselines_lookup", "recipient_email", "sender_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_email: Mapped[str] = mapped_column(String, nullable=False)
    sender_email: Mapped[str] = mapped_column(String, nullable=False)
    avg_word_count: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_sentence_length: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    typical_hours: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    formality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    typical_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Analysis(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        UniqueConstraint("message_uid", "recipient_email", name="uq_analysis_message"),
        Index("idx_analyses_recipient", "recipient_email", "analyzed_at"),
        Index("idx_analyses_score", "manipulation_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_uid: Mapped[str] = mapped_column(String, nullable=False)
    recipient_email: Mapped[str] = mapped_column(String, nullable=False)
    sender_email: Mapped[str] = mapped_column(String, nullable=False)
    sender_display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    prefilter_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    prefilter_signals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manipulation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dimension_scores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="analysis")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_severity", "severity", "acknowledged", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analyses.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="alerts")
