"""
routes/journal.py
─────────────────
Journal entry endpoints.

Endpoints
─────────
POST   /journal/         – Create a new entry (AI analysis triggered async)
GET    /journal/         – Paginated list of the user's entries
GET    /journal/{id}     – Fetch a single entry by ID
DELETE /journal/{id}     – Delete an entry

Business rules
──────────────
• Free tier users are capped at settings.free_tier_monthly_entries entries/month.
• Creating an entry invalidates the user's analytics cache.
• AI analysis is performed synchronously (fast model); UI shows a skeleton
  while ``is_processed`` is False.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.models import DailyStreak, JournalEntry, SubscriptionTier, User
from backend.schemas import (
    JournalEntryCreate,
    JournalEntryOut,
    PaginatedEntries,
    JournalEntryBrief,
    MessageResponse,
)
from backend.services.ai_service import ai_service
from backend.services.auth_service import get_current_user
from backend.services.cache_service import cache
from backend.utils.helpers import calculate_streak, score_to_mood_label

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post(
    "/",
    response_model=JournalEntryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new journal entry",
)
async def create_entry(
    payload: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JournalEntryOut:
    """
    Create and analyse a new journal entry.

    Flow
    ────
    1. Enforce free-tier limit
    2. Persist the entry with mood label
    3. Call Claude API for sentiment + insight
    4. Update the entry with AI results
    5. Update streak
    6. Invalidate analytics cache

    Raises
    ──────
    402 – Free tier limit reached
    """
    # ── Tier enforcement ───────────────────────────────────────────────────
    if (
        current_user.tier == SubscriptionTier.FREE
        and current_user.entries_this_month >= settings.free_tier_monthly_entries
    ):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Free tier limit of {settings.free_tier_monthly_entries} entries/month reached. "
                "Upgrade to Premium for unlimited journaling."
            ),
        )

    # ── Create entry ───────────────────────────────────────────────────────
    entry = JournalEntry(
        user_id=current_user.id,
        content=payload.content,
        mood_score=payload.mood_score,
        mood_label=score_to_mood_label(payload.mood_score),
    )
    db.add(entry)
    await db.flush()  # Get entry.id

    # ── AI Analysis ───────────────────────────────────────────────────────
    analysis = await ai_service.analyse_entry(payload.content, payload.mood_score)
    entry.ai_sentiment = analysis.sentiment
    entry.ai_summary = analysis.summary
    entry.ai_insight = analysis.insight
    entry.ai_coping_tips = analysis.coping_tips
    entry.is_processed = True

    # ── Update monthly counter ─────────────────────────────────────────────
    current_user.entries_this_month += 1

    # ── Update streak ──────────────────────────────────────────────────────
    if current_user.streak is None:
        streak = DailyStreak(user_id=current_user.id, current_streak=1, longest_streak=1)
        db.add(streak)
    else:
        from datetime import datetime, timezone
        new_current, new_longest = calculate_streak(
            current_user.streak.current_streak,
            current_user.streak.longest_streak,
            current_user.streak.last_entry_date,
        )
        current_user.streak.current_streak = new_current
        current_user.streak.longest_streak = new_longest
        current_user.streak.last_entry_date = datetime.now(timezone.utc)

    # ── Invalidate cache ───────────────────────────────────────────────────
    cache.invalidate_user(current_user.id)

    await db.flush()
    return JournalEntryOut.model_validate(entry)


@router.get(
    "/",
    response_model=PaginatedEntries,
    summary="List journal entries (paginated)",
)
async def list_entries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedEntries:
    """
    Return a paginated list of the authenticated user's entries, newest first.
    """
    offset = (page - 1) * page_size

    # Total count (for pagination metadata)
    count_result = await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.user_id == current_user.id)
    )
    total: int = count_result.scalar_one()

    # Fetch page
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == current_user.id)
        .order_by(JournalEntry.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    entries = result.scalars().all()

    return PaginatedEntries(
        items=[JournalEntryBrief.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get(
    "/{entry_id}",
    response_model=JournalEntryOut,
    summary="Get a single entry by ID",
)
async def get_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JournalEntryOut:
    """
    Fetch the full detail of a single journal entry.

    Raises
    ──────
    404 – Entry not found or belongs to another user
    """
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id,
        )
    )
    entry: JournalEntry | None = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found.")
    return JournalEntryOut.model_validate(entry)


@router.delete(
    "/{entry_id}",
    response_model=MessageResponse,
    summary="Delete a journal entry",
)
async def delete_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Permanently delete a journal entry.

    Raises
    ──────
    404 – Entry not found or belongs to another user
    """
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id,
        )
    )
    entry: JournalEntry | None = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found.")

    await db.delete(entry)
    cache.invalidate_user(current_user.id)
    return MessageResponse(message="Entry deleted successfully.")
