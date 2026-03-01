"""
schemas.py
──────────
Pydantic v2 request/response schemas (DTOs).

Organised into three groups:
  • Auth    – registration, login, token
  • Journal – create, read, paginated list
  • Analytics – mood trends, streak, insights
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.models import MoodLabel, SubscriptionTier


# ═══════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    """Payload to create a new account."""
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Payload to authenticate and receive a JWT."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT access token returned after successful auth."""
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """Safe public representation of a User (no password hash)."""
    id: int
    email: EmailStr
    username: str
    tier: SubscriptionTier
    entries_this_month: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════
# Journal
# ═══════════════════════════════════════════════════════════════════════════

class JournalEntryCreate(BaseModel):
    """Payload to submit a new journal entry."""
    content: str = Field(..., min_length=10, max_length=4000)
    mood_score: int = Field(..., ge=1, le=10)

    @field_validator("mood_score")
    @classmethod
    def derive_mood_label_preview(cls, v: int) -> int:
        """Validate mood_score range (label derived server-side)."""
        return v


class JournalEntryOut(BaseModel):
    """Full journal entry including AI-enriched fields."""
    id: int
    content: str
    mood_score: int
    mood_label: MoodLabel
    ai_sentiment: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_insight: Optional[str] = None
    ai_coping_tips: Optional[str] = None
    is_processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class JournalEntryBrief(BaseModel):
    """Lightweight summary used in paginated list responses."""
    id: int
    mood_score: int
    mood_label: MoodLabel
    ai_summary: Optional[str] = None
    is_processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedEntries(BaseModel):
    """Paginated list of journal entries."""
    items: list[JournalEntryBrief]
    total: int
    page: int
    page_size: int
    has_next: bool


# ═══════════════════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════════════════

class MoodDataPoint(BaseModel):
    """Single point on the mood trend chart."""
    date: str           # ISO date string "YYYY-MM-DD"
    mood_score: float
    ai_sentiment: Optional[float] = None


class MoodDistribution(BaseModel):
    """Count of entries per mood label for pie/bar chart."""
    very_bad: int = 0
    bad: int = 0
    neutral: int = 0
    good: int = 0
    very_good: int = 0


class StreakInfo(BaseModel):
    """User's journaling streak data."""
    current_streak: int
    longest_streak: int
    last_entry_date: Optional[datetime] = None


class AnalyticsSummary(BaseModel):
    """Full analytics payload returned to the dashboard."""
    trend: list[MoodDataPoint]
    distribution: MoodDistribution
    streak: StreakInfo
    average_mood: float
    total_entries: int
    ai_weekly_insight: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Generic
# ═══════════════════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    """Generic success/error message wrapper."""
    message: str
    detail: Optional[str] = None
