"""
services/ai_service.py
───────────────────────
Claude API integration for sentiment analysis and insight generation.

Design principles
─────────────────
• ``AIService`` is a thin wrapper – it never touches the database.
• All prompts are encapsulated in private methods for easy tuning.
• ``tenacity`` retry logic handles transient API failures gracefully.
• If the API key is not configured a deterministic fallback response
  is returned so the app remains fully functional for offline demos.
• Structured JSON is extracted from Claude's response using a robust
  parser that tolerates markdown code fences.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.config import settings

logger = logging.getLogger(__name__)


# ── Data classes (returned to callers) ────────────────────────────────────

@dataclass
class EntryAnalysis:
    """
    Result of analysing a single journal entry.

    Attributes
    ──────────
    sentiment   : Float from -1.0 (very negative) to 1.0 (very positive)
    summary     : One-sentence summary of the entry
    insight     : Personalised, empathetic reflection
    coping_tips : Newline-separated actionable suggestions
    """
    sentiment: float
    summary: str
    insight: str
    coping_tips: str


@dataclass
class WeeklyInsight:
    """
    AI-generated weekly summary across multiple entries.

    Attributes
    ──────────
    insight : Multi-sentence narrative about the user's mood patterns
    """
    insight: str


# ── Service ────────────────────────────────────────────────────────────────

class AIService:
    """
    Wrapper around the Anthropic Claude API.

    Attributes
    ──────────
    _client : ``anthropic.Anthropic`` instance (or ``None`` if no key)
    _model  : Model string from settings
    """

    def __init__(self) -> None:
        self._model: str = settings.ai_model
        if settings.anthropic_api_key:
            self._client: Optional[anthropic.Anthropic] = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            )
        else:
            self._client = None
            logger.warning(
                "ANTHROPIC_API_KEY not set. AI features will return mock responses."
            )

    # ── Public methods ─────────────────────────────────────────────────────

    async def analyse_entry(self, content: str, mood_score: int) -> EntryAnalysis:
        """
        Analyse a journal entry and return sentiment + insight.

        Parameters
        ──────────
        content    : The user's journal text
        mood_score : Self-reported score 1–10

        Returns
        ───────
        EntryAnalysis dataclass
        """
        if not self._client:
            return self._mock_entry_analysis(mood_score)

        try:
            return await self._call_entry_analysis(content, mood_score)
        except Exception as exc:
            logger.error("AI entry analysis failed: %s", exc)
            return self._mock_entry_analysis(mood_score)

    async def generate_weekly_insight(self, entries_text: str) -> WeeklyInsight:
        """
        Generate a weekly mood pattern insight from recent journal entries.

        Parameters
        ──────────
        entries_text : Concatenated recent entries (passed by analytics service)

        Returns
        ───────
        WeeklyInsight dataclass
        """
        if not self._client:
            return WeeklyInsight(
                insight=(
                    "You've been consistently journaling this week — that's a great habit! "
                    "Your entries show a mix of emotions. Keep reflecting and remember that "
                    "acknowledging your feelings is the first step toward wellbeing."
                )
            )

        try:
            return await self._call_weekly_insight(entries_text)
        except Exception as exc:
            logger.error("AI weekly insight failed: %s", exc)
            return WeeklyInsight(insight="Unable to generate insight at this time.")

    # ── Private API callers ────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(anthropic.APIConnectionError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _call_entry_analysis(self, content: str, mood_score: int) -> EntryAnalysis:
        """Call Claude to analyse a single entry. Retries on connection errors."""
        prompt = self._build_entry_prompt(content, mood_score)

        message = self._client.messages.create(  # type: ignore[union-attr]
            model=self._model,
            max_tokens=settings.ai_max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return self._parse_entry_analysis(raw)

    @retry(
        retry=retry_if_exception_type(anthropic.APIConnectionError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _call_weekly_insight(self, entries_text: str) -> WeeklyInsight:
        """Call Claude to generate a weekly insight. Retries on connection errors."""
        prompt = self._build_weekly_prompt(entries_text)

        message = self._client.messages.create(  # type: ignore[union-attr]
            model=self._model,
            max_tokens=settings.ai_max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        return WeeklyInsight(insight=raw.strip())

    # ── Prompt builders ────────────────────────────────────────────────────

    @staticmethod
    def _build_entry_prompt(content: str, mood_score: int) -> str:
        return f"""You are MoodLens, a compassionate mental wellness AI assistant.

Analyse the following journal entry and respond ONLY with a valid JSON object.

Journal entry (mood score {mood_score}/10):
\"\"\"
{content}
\"\"\"

Respond with ONLY this JSON (no markdown fences, no extra text):
{{
  "sentiment": <float between -1.0 and 1.0>,
  "summary": "<one sentence summary, max 120 chars>",
  "insight": "<2-3 sentence empathetic reflection tailored to this person>",
  "coping_tips": "<3 actionable tips separated by newlines, relevant to this entry>"
}}"""

    @staticmethod
    def _build_weekly_prompt(entries_text: str) -> str:
        return f"""You are MoodLens, a compassionate mental wellness AI assistant.

Review these recent journal entries and write a warm, encouraging 3–4 sentence 
weekly insight that identifies emotional patterns, celebrates wins, and offers 
gentle guidance. Be specific, not generic. Do not use bullet points.

Recent entries:
{entries_text}

Respond with only the insight text, nothing else."""

    # ── Response parsers ───────────────────────────────────────────────────

    @staticmethod
    def _parse_entry_analysis(raw: str) -> EntryAnalysis:
        """
        Parse JSON from Claude's response.

        Strips markdown fences if present, then loads JSON.
        Falls back to defaults if parsing fails.
        """
        # Strip ```json ... ``` or ``` ... ``` fences
        cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            return EntryAnalysis(
                sentiment=float(data.get("sentiment", 0.0)),
                summary=str(data.get("summary", "Journal entry recorded.")),
                insight=str(data.get("insight", "Keep journaling — it's a great habit.")),
                coping_tips=str(data.get("coping_tips", "Take a short walk.\nDrink water.\nBreathe deeply.")),
            )
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("Failed to parse AI response: %s | raw: %s", exc, raw[:200])
            return AIService._fallback_entry_analysis()

    @staticmethod
    def _fallback_entry_analysis() -> EntryAnalysis:
        return EntryAnalysis(
            sentiment=0.0,
            summary="Journal entry recorded and saved.",
            insight="Thank you for taking the time to reflect. Journaling is a powerful tool for self-awareness.",
            coping_tips="Take a few deep breaths.\nGo for a short walk.\nReach out to someone you trust.",
        )

    @staticmethod
    def _mock_entry_analysis(mood_score: int) -> EntryAnalysis:
        """Deterministic mock used when no API key is configured."""
        sentiment = (mood_score - 5.5) / 4.5  # normalise 1-10 → -1.0 to 1.0
        return EntryAnalysis(
            sentiment=round(sentiment, 2),
            summary="Your entry has been saved. AI analysis requires an API key.",
            insight=(
                "This is a demo mode response. Configure ANTHROPIC_API_KEY to "
                "unlock personalised AI insights tailored to your journal entries."
            ),
            coping_tips=(
                "Practice mindful breathing for 5 minutes.\n"
                "Write down three things you are grateful for.\n"
                "Connect with a friend or family member today."
            ),
        )


# Singleton instance
ai_service = AIService()
