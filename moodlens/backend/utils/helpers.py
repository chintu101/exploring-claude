"""
utils/helpers.py
────────────────
Pure utility functions with no external dependencies on the app.

Functions
─────────
score_to_mood_label      – Convert 1–10 score to MoodLabel enum
calculate_streak         – Determine new streak values from a sorted date list
format_entries_for_ai    – Prepare journal text for the weekly insight prompt
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from moodlens.backend.models import MoodLabel


def score_to_mood_label(score: int) -> MoodLabel:
    """
    Derive a MoodLabel from a numeric mood score (1–10).

    Mapping
    ───────
    1–2  → VERY_BAD
    3–4  → BAD
    5–6  → NEUTRAL
    7–8  → GOOD
    9–10 → VERY_GOOD
    """
    if score <= 2:
        return MoodLabel.VERY_BAD
    elif score <= 4:
        return MoodLabel.BAD
    elif score <= 6:
        return MoodLabel.NEUTRAL
    elif score <= 8:
        return MoodLabel.GOOD
    else:
        return MoodLabel.VERY_GOOD


def calculate_streak(
    current_streak: int,
    longest_streak: int,
    last_entry_date: Optional[datetime],
) -> tuple[int, int]:
    """
    Compute the updated streak values after a new journal entry today.

    Parameters
    ──────────
    current_streak  : The user's existing streak count
    longest_streak  : The user's all-time best streak
    last_entry_date : UTC datetime of the previous entry (or None)

    Returns
    ───────
    (new_current_streak, new_longest_streak)

    Logic
    ─────
    • If last entry was yesterday  → increment streak
    • If last entry was today      → no change (idempotent)
    • Otherwise (gap > 1 day)      → reset streak to 1
    """
    today: date = datetime.now(timezone.utc).date()

    if last_entry_date is None:
        new_current = 1
    else:
        last_date = last_entry_date.astimezone(timezone.utc).date()
        delta = (today - last_date).days

        if delta == 0:
            # Already journaled today — streak unchanged
            new_current = current_streak
        elif delta == 1:
            # Yesterday — extend streak
            new_current = current_streak + 1
        else:
            # Streak broken
            new_current = 1

    new_longest = max(longest_streak, new_current)
    return new_current, new_longest


def format_entries_for_ai(entries: list) -> str:
    """
    Format a list of JournalEntry ORM objects into a string for the AI weekly prompt.

    Parameters
    ──────────
    entries : List of JournalEntry instances (most recent first)

    Returns
    ───────
    Formatted multi-entry string, truncated to avoid token limits.
    """
    MAX_CHARS_PER_ENTRY = 500
    MAX_ENTRIES = 7

    lines: list[str] = []
    for entry in entries[:MAX_ENTRIES]:
        date_str = entry.created_at.strftime("%A, %b %d")
        content_preview = entry.content[:MAX_CHARS_PER_ENTRY]
        if len(entry.content) > MAX_CHARS_PER_ENTRY:
            content_preview += "..."
        lines.append(f"[{date_str} – Mood {entry.mood_score}/10]\n{content_preview}")

    return "\n\n---\n\n".join(lines)
