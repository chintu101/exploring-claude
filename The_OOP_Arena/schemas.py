"""
CodeQuest — Pydantic v2 Schemas
================================
All API request and response types. Pydantic validates incoming JSON and
serialises outgoing data. Using model_config for Pydantic v2 compatibility.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS (incoming from frontend)
# ═══════════════════════════════════════════════════════════════════════════════

class NewGameRequest(BaseModel):
    """Request to start a new game session."""

    hero_class: str = Field(
        ...,
        description="One of: Warrior, Mage, Archer",
        examples=["Warrior"],
    )
    hero_name: str = Field(
        default="Hero",
        min_length=1,
        max_length=20,
        description="Player's chosen name for their hero",
    )

    @field_validator("hero_class")
    @classmethod
    def validate_hero_class(cls, v: str) -> str:
        valid = {"Warrior", "Mage", "Archer"}
        if v not in valid:
            raise ValueError(f"hero_class must be one of {valid}. Got: {v!r}")
        return v

    @field_validator("hero_name")
    @classmethod
    def sanitise_hero_name(cls, v: str) -> str:
        """Strip whitespace and replace non-alphanumeric chars."""
        import re
        cleaned = re.sub(r"[^a-zA-Z0-9 _-]", "", v.strip())
        return cleaned or "Hero"


class ActionRequest(BaseModel):
    """Request to perform an action in a running battle.

    The full game_state is sent back with each request because the backend
    is stateless (serverless functions have no persistent memory).
    """

    action: str = Field(
        ...,
        description="One of: basic_attack, special_ability, defend",
        examples=["basic_attack"],
    )
    game_state: dict = Field(
        ...,
        description="The current serialised game state from the frontend",
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid = {"basic_attack", "special_ability", "defend"}
        if v not in valid:
            raise ValueError(f"action must be one of {valid}. Got: {v!r}")
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# CODE TRACE SCHEMAS (the educational component)
# ═══════════════════════════════════════════════════════════════════════════════

class TraceStep(BaseModel):
    """One step in the code execution trace.

    Displayed in the CodeTrace panel, animated sequentially.
    """

    class_name: str = Field(..., description="The class this method belongs to")
    method_name: str = Field(..., description="Name of the method being called")
    code_line: str = Field(..., description="Key line of code from the method")
    description: str = Field(..., description="Plain-English explanation of what's happening")
    inheritance_chain: list[str] = Field(
        default_factory=list,
        description="Full chain from root to this class (e.g. ['Entity','Character','Hero','Warrior'])",
    )
    concept: str = Field(
        default="",
        description="OOP concept being demonstrated (e.g. 'Polymorphism', 'super()')",
    )


class CodeTrace(BaseModel):
    """Full code trace for one game action."""

    steps: list[TraceStep] = Field(default_factory=list)
    action_key: str = Field(..., description="Machine key matching ActionResult.action")
    summary: str = Field(..., description="One-sentence summary of OOP concepts demonstrated")


# ═══════════════════════════════════════════════════════════════════════════════
# GAME STATE SCHEMAS (shared between frontend and backend)
# ═══════════════════════════════════════════════════════════════════════════════

class CharacterSnapshot(BaseModel):
    """Serialised snapshot of a Character's current state."""

    name: str
    class_name: str
    current_hp: int
    max_hp: int
    base_damage: int
    defense: int
    speed: int
    is_alive: bool
    hp_ratio: float
    status_effects: list[str] = Field(default_factory=list)

    # Hero-specific (None for enemies)
    hero_class: Optional[str] = None
    mana: Optional[int] = None
    max_mana: Optional[int] = None
    mana_ratio: Optional[float] = None
    level: Optional[int] = None
    experience: Optional[int] = None
    xp_to_next: Optional[int] = None
    rage_charges: Optional[int] = None
    spell_power: Optional[int] = None
    crit_chance: Optional[float] = None
    focus_stacks: Optional[int] = None

    # Enemy-specific (None for heroes)
    enemy_type: Optional[str] = None
    xp_reward: Optional[int] = None
    wave_level: Optional[int] = None
    fire_charges: Optional[int] = None


class GameState(BaseModel):
    """Complete, serialisable game state.

    This is passed back and forth between frontend and backend.
    The backend is stateless — it receives this, mutates it, and returns it.
    """

    hero: dict = Field(..., description="Hero snapshot dict")
    enemies: list[dict] = Field(default_factory=list, description="Enemy snapshot dicts")
    wave: int = Field(default=1, ge=1, le=5)
    turn: int = Field(default=1, ge=1)
    phase: str = Field(
        default="player_turn",
        description="One of: hero_select, player_turn, enemy_turn, wave_complete, victory, defeat",
    )
    battle_log: list[str] = Field(default_factory=list)
    score: int = Field(default=0, ge=0)
    levelled_up: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS (outgoing to frontend)
# ═══════════════════════════════════════════════════════════════════════════════

class ActionResponse(BaseModel):
    """Response to an action request."""

    game_state: GameState
    action_result: dict = Field(..., description="The ActionResult from this action")
    code_trace: CodeTrace
    enemy_action_result: Optional[dict] = Field(
        None,
        description="Enemy's counter-action (only present when it was the enemy's turn)",
    )
    enemy_code_trace: Optional[CodeTrace] = None
    levelled_up: bool = False
    status_messages: list[str] = Field(default_factory=list)


class NewGameResponse(BaseModel):
    """Response to a new game request."""

    game_state: GameState
    message: str = "New game started! Good luck, hero."


class ClassHierarchyResponse(BaseModel):
    """Response with the full OOP class hierarchy for the ClassExplorer."""

    hierarchy: dict
    concepts: list[dict] = Field(
        default_factory=list,
        description="OOP concepts demonstrated in this project",
    )
