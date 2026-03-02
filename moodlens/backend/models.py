"""
models.py
─────────
SQLAlchemy ORM models.

Hierarchy
─────────
Base (DeclarativeBase)
 └── TimestampMixin          – created_at / updated_at on every table
      ├── User               – authentication + subscription state
      ├── JournalEntry       – daily mood entry with AI analysis
      └── DailyStreak        – streak tracking per user
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from moodlens.backend.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class MoodLabel(str, enum.Enum):
    VERY_BAD   = "very_bad"
    BAD        = "bad"
    NEUTRAL    = "neutral"
    GOOD       = "good"
    VERY_GOOD  = "very_good"


# ── Mixins ─────────────────────────────────────────────────────────────────

class TimestampMixin:
    """
    Adds created_at and updated_at columns to any model.
    updated_at is automatically refreshed on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Models ─────────────────────────────────────────────────────────────────

class User(TimestampMixin, Base):
    """
    Represents a registered MoodLens user.

    Attributes
    ──────────
    id              : Primary key (auto-increment)
    email           : Unique email used for login
    username        : Display name shown in the UI
    hashed_password : bcrypt hash – never store plaintext
    is_active       : Soft-disable accounts without deletion
    tier            : FREE or PREMIUM subscription level
    entries_this_month : Monotonic counter reset each billing cycle
    entries         : One-to-many relationship to JournalEntry
    streak          : One-to-one relationship to DailyStreak
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False
    )
    entries_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    entries: Mapped[list[JournalEntry]] = relationship(
        "JournalEntry", back_populates="user", cascade="all, delete-orphan"
    )
    streak: Mapped[DailyStreak | None] = relationship(
        "DailyStreak", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} tier={self.tier}>"


class JournalEntry(TimestampMixin, Base):
    """
    A single journal entry submitted by a user.

    Attributes
    ──────────
    id              : Primary key
    user_id         : FK → users.id
    content         : The raw journal text (max 4 000 chars)
    mood_score      : User's self-reported score 1–10
    mood_label      : Derived enum category
    ai_sentiment    : Raw sentiment score returned by Claude (-1.0 to 1.0)
    ai_summary      : Claude-generated one-sentence summary
    ai_insight      : Claude-generated personalised insight
    ai_coping_tips  : Newline-separated coping suggestions
    is_processed    : False until Claude has analysed the entry
    user            : Back-reference to User
    """

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–10
    mood_label: Mapped[MoodLabel] = mapped_column(Enum(MoodLabel), nullable=False)

    # AI-enriched fields (populated asynchronously after save)
    ai_sentiment: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ai_insight: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_coping_tips: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="entries")

    def __repr__(self) -> str:
        return f"<JournalEntry id={self.id} user_id={self.user_id} score={self.mood_score}>"


class DailyStreak(TimestampMixin, Base):
    """
    Tracks the user's consecutive daily journaling streak.

    Attributes
    ──────────
    id              : Primary key
    user_id         : FK → users.id (unique — one streak record per user)
    current_streak  : Number of consecutive days journaled
    longest_streak  : Historical max streak
    last_entry_date : Date of most recent entry (for streak calculation)
    user            : Back-reference to User
    """

    __tablename__ = "daily_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_entry_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="streak")

    def __repr__(self) -> str:
        return (
            f"<DailyStreak user_id={self.user_id} "
            f"current={self.current_streak} longest={self.longest_streak}>"
        )
