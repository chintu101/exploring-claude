"""
routes/analytics.py
───────────────────
Analytics and insights endpoints.

Endpoints
─────────
GET /analytics/summary   – Full dashboard payload (cached 5 min)
GET /analytics/insight   – AI weekly insight (cached separately)

Architecture note
─────────────────
All heavy aggregation lives here, not in the journal routes.
Results are TTL-cached per user so repeated dashboard refreshes
never hit the database unnecessarily.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import JournalEntry, MoodLabel, User
from backend.schemas import (
    AnalyticsSummary,
    MoodDataPoint,
    MoodDistribution,
    StreakInfo,
)
from backend.services.ai_service import ai_service
from backend.services.auth_service import get_current_user
from backend.services.cache_service import cache
from backend.utils.helpers import format_entries_for_ai

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Cache namespace constants
_NS_SUMMARY = "analytics_summary"
_NS_INSIGHT = "weekly_insight"


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Full dashboard analytics (cached)",
)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
    """
    Return aggregated mood data for the dashboard.

    Cached per user for ``settings.cache_ttl_seconds``.
    Cache is invalidated whenever a new journal entry is created.

    Returns
    ───────
    AnalyticsSummary containing:
    - 30-day mood trend (daily averages)
    - Mood label distribution
    - Streak info
    - Average mood score
    - Total entry count
    - AI weekly insight (cached separately)
    """
    # ── Cache hit? ─────────────────────────────────────────────────────────
    cached = cache.get(_NS_SUMMARY, current_user.id)
    if cached is not None:
        return cached

    # ── Fetch last 30 days of entries ──────────────────────────────────────
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == current_user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(90)  # Fetch 90 to have enough for trend + weekly AI
    )
    entries: list[JournalEntry] = list(result.scalars().all())

    # ── Trend: daily average mood (last 30 entries) ────────────────────────
    daily_scores: dict[str, list[float]] = defaultdict(list)
    daily_sentiments: dict[str, list[float]] = defaultdict(list)

    for entry in entries:
        day_key = entry.created_at.strftime("%Y-%m-%d")
        daily_scores[day_key].append(entry.mood_score)
        if entry.ai_sentiment is not None:
            daily_sentiments[day_key].append(entry.ai_sentiment)

    trend: list[MoodDataPoint] = [
        MoodDataPoint(
            date=day,
            mood_score=round(sum(scores) / len(scores), 2),
            ai_sentiment=(
                round(sum(daily_sentiments[day]) / len(daily_sentiments[day]), 3)
                if daily_sentiments[day]
                else None
            ),
        )
        for day, scores in sorted(daily_scores.items())
    ]

    # ── Distribution ───────────────────────────────────────────────────────
    dist_counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        dist_counts[entry.mood_label.value] += 1

    distribution = MoodDistribution(
        very_bad=dist_counts[MoodLabel.VERY_BAD.value],
        bad=dist_counts[MoodLabel.BAD.value],
        neutral=dist_counts[MoodLabel.NEUTRAL.value],
        good=dist_counts[MoodLabel.GOOD.value],
        very_good=dist_counts[MoodLabel.VERY_GOOD.value],
    )

    # ── Streak ─────────────────────────────────────────────────────────────
    streak_info = StreakInfo(
        current_streak=current_user.streak.current_streak if current_user.streak else 0,
        longest_streak=current_user.streak.longest_streak if current_user.streak else 0,
        last_entry_date=current_user.streak.last_entry_date if current_user.streak else None,
    )

    # ── Averages ───────────────────────────────────────────────────────────
    total_entries = len(entries)
    avg_mood = (
        round(sum(e.mood_score for e in entries) / total_entries, 2)
        if total_entries > 0
        else 0.0
    )

    # ── AI weekly insight (fetched from its own cache) ─────────────────────
    weekly_insight = await _get_weekly_insight(current_user.id, entries)

    # ── Assemble + cache ───────────────────────────────────────────────────
    summary = AnalyticsSummary(
        trend=trend,
        distribution=distribution,
        streak=streak_info,
        average_mood=avg_mood,
        total_entries=total_entries,
        ai_weekly_insight=weekly_insight,
    )
    cache.set(_NS_SUMMARY, current_user.id, summary)
    return summary


async def _get_weekly_insight(user_id: int, entries: list[JournalEntry]) -> str | None:
    """
    Return the cached weekly insight, generating it if absent.

    Kept as a private async helper to keep the main route clean.
    """
    cached_insight = cache.get(_NS_INSIGHT, user_id)
    if cached_insight:
        return cached_insight

    if not entries:
        return "Start journaling to receive personalised weekly insights!"

    recent_entries = [e for e in entries if e.is_processed][:7]
    if not recent_entries:
        return "Your AI insights will appear here once your entries are processed."

    entries_text = format_entries_for_ai(recent_entries)
    insight_obj = await ai_service.generate_weekly_insight(entries_text)
    cache.set(_NS_INSIGHT, user_id, insight_obj.insight)
    return insight_obj.insight
