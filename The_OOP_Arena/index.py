"""
CodeQuest — FastAPI Application Entry Point
============================================
All HTTP routes live here. The app is stateless:
  - Frontend holds game state in React state + localStorage
  - Each request sends the full game state and receives the updated state

Vercel Deployment:
  - This file is the ASGI app. Vercel's Python runtime serves it via Mangum.
  - Mangum adapts FastAPI's ASGI interface to AWS Lambda/Vercel's handler format.

Routes:
  POST /api/new-game           — Initialise a game for the chosen hero class
  POST /api/action             — Process a player action (attack/special/defend)
  GET  /api/class-hierarchy    — Return OOP class hierarchy (cached)
  GET  /api/concepts           — Return OOP concepts list (cached)
  GET  /api/health             — Health check
"""

from __future__ import annotations

import random
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.cache import GameCache, cached_static
from api.models import (
    ENEMY_REGISTRY,
    create_enemy,
    create_hero,
    get_class_hierarchy,
)
from api.schemas import (
    ActionRequest,
    ActionResponse,
    ClassHierarchyResponse,
    CodeTrace,
    GameState,
    NewGameRequest,
    NewGameResponse,
)
from api.services import TraceService

# ═══════════════════════════════════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="CodeQuest API",
    description="Turn-based RPG backend that exposes OOP class traces for educational use.",
    version="1.0.0",
)

# CORS — allow the Next.js frontend on all origins in dev; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Mangum handler for Vercel serverless
handler = Mangum(app, lifespan="off")


# ═══════════════════════════════════════════════════════════════════════════════
# Wave Configuration
# ═══════════════════════════════════════════════════════════════════════════════

WAVE_COMPOSITIONS: dict[int, list[str]] = {
    1: ["Goblin", "Goblin"],
    2: ["Goblin", "Goblin", "Troll"],
    3: ["Troll", "Goblin"],
    4: ["Dragon"],
    5: ["Dragon", "Lich"],
}


def _get_wave_enemies(wave: int) -> list[str]:
    """Return the list of enemy type strings for a given wave (with caching)."""
    cached = GameCache.get_wave(wave)
    if cached is not None:
        return cached
    enemy_types = WAVE_COMPOSITIONS.get(wave, ["Goblin"])
    GameCache.set_wave(wave, enemy_types)
    return enemy_types


# ═══════════════════════════════════════════════════════════════════════════════
# Game State Reconstruction
# ═══════════════════════════════════════════════════════════════════════════════

def _reconstruct_hero(hero_dict: dict):
    """Reconstruct a Hero instance from a serialised dict.

    Because we're stateless, the full hero state is re-built from JSON every
    request. Private attributes are set directly after construction.
    """
    hero_class = hero_dict.get("hero_class", "Warrior")
    hero_name = hero_dict.get("name", "Hero")
    hero = create_hero(hero_class, hero_name)

    # Restore all mutable state from the serialised snapshot
    hero._current_hp = hero_dict.get("current_hp", hero._max_hp)
    hero._max_hp = hero_dict.get("max_hp", hero._max_hp)
    hero._mana = hero_dict.get("mana", hero._max_mana)
    hero._max_mana = hero_dict.get("max_mana", hero._max_mana)
    hero._level = hero_dict.get("level", 1)
    hero._experience = hero_dict.get("experience", 0)
    hero._base_damage = hero_dict.get("base_damage", hero._base_damage)
    hero._defense = hero_dict.get("defense", hero._defense)
    hero._status_effects = list(hero_dict.get("status_effects", []))
    hero._alive = hero._current_hp > 0

    # Class-specific extra state
    if hero_class == "Warrior":
        hero._rage_charges = hero_dict.get("rage_charges", 0)
    elif hero_class == "Mage":
        hero._spell_power = hero_dict.get("spell_power", 25)
    elif hero_class == "Archer":
        hero._focus_stacks = hero_dict.get("focus_stacks", 0)

    return hero


def _reconstruct_enemies(enemy_dicts: list[dict]) -> list:
    """Reconstruct a list of Enemy instances from serialised dicts."""
    enemies = []
    for edict in enemy_dicts:
        if not edict.get("is_alive", True):
            continue
        enemy_type = edict.get("enemy_type", "Goblin")
        wave_level = edict.get("wave_level", 1)
        enemy = create_enemy(enemy_type, wave_level)
        # Restore mutable state
        enemy._current_hp = edict.get("current_hp", enemy._max_hp)
        enemy._max_hp = edict.get("max_hp", enemy._max_hp)
        enemy._base_damage = edict.get("base_damage", enemy._base_damage)
        enemy._defense = edict.get("defense", enemy._defense)
        enemy._status_effects = list(edict.get("status_effects", []))
        enemy._alive = enemy._current_hp > 0
        # Dragon-specific
        if enemy_type == "Dragon":
            enemy._fire_charges = edict.get("fire_charges", 3)
        if enemy._alive:
            enemies.append(enemy)
    return enemies


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "codequest-api", "version": "1.0.0"}


@app.get("/api/class-hierarchy", response_model=ClassHierarchyResponse)
async def get_hierarchy() -> ClassHierarchyResponse:
    """Return the full OOP class hierarchy tree.

    Result is cached in-process (TTL 1 hour) to avoid recomputing every request.
    """
    cached = GameCache.get_static("hierarchy")
    if cached:
        return ClassHierarchyResponse(**cached)

    hierarchy = get_class_hierarchy()
    concepts = TraceService.list_concepts()
    result = ClassHierarchyResponse(hierarchy=hierarchy, concepts=concepts)
    GameCache.set_static("hierarchy", result.model_dump())
    return result


@app.get("/api/concepts")
async def get_concepts() -> list[dict]:
    """Return all OOP concepts demonstrated in CodeQuest."""
    cached = GameCache.get_static("concepts")
    if cached:
        return cached
    concepts = TraceService.list_concepts()
    GameCache.set_static("concepts", concepts)
    return concepts


@app.post("/api/new-game", response_model=NewGameResponse)
async def new_game(req: NewGameRequest) -> NewGameResponse:
    """Initialise a new game for the chosen hero class.

    Creates the hero and the first wave of enemies, then returns the initial
    game state for the frontend to render.
    """
    try:
        hero = create_hero(req.hero_class, req.hero_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    wave = 1
    enemy_types = _get_wave_enemies(wave)
    enemies = [create_enemy(etype, wave) for etype in enemy_types]

    game_state = GameState(
        hero=hero.to_dict(),
        enemies=[e.to_dict() for e in enemies],
        wave=wave,
        turn=1,
        phase="player_turn",
        battle_log=[
            f"⚔️  A {req.hero_class} named {req.hero_name} enters the dungeon!",
            f"Wave 1 begins — {', '.join(e.name for e in enemies)} appear!",
        ],
        score=0,
    )
    return NewGameResponse(
        game_state=game_state,
        message=f"New game started! {req.hero_class} {req.hero_name} enters the dungeon.",
    )


@app.post("/api/action", response_model=ActionResponse)
async def process_action(req: ActionRequest) -> ActionResponse:
    """Process one player action and return the updated game state + code trace.

    Flow:
      1. Deserialise game state from request
      2. Reconstruct Hero and Enemy objects from dicts
      3. Execute the player's chosen action
      4. Generate the code trace for the action
      5. Execute enemy counter-actions
      6. Tick status effects (bleeding, burning)
      7. Check win/lose/wave-advance conditions
      8. Re-serialise updated state and return
    """
    gs_data = req.game_state
    try:
        gs = GameState(**gs_data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid game state: {exc}")

    # ── Reconstruct objects ──
    hero = _reconstruct_hero(gs.hero)
    enemies = _reconstruct_enemies(gs.enemies)
    status_messages: list[str] = []

    if not hero.is_alive:
        raise HTTPException(status_code=400, detail="Hero is dead. Start a new game.")
    if not enemies:
        raise HTTPException(status_code=400, detail="No enemies remaining. Wave already complete.")

    target_enemy = enemies[0]   # Always target the first living enemy

    # ── Execute player action ──
    action_result = None
    hero_trace: CodeTrace

    if req.action == "basic_attack":
        action_result = hero.basic_attack(target_enemy)
        # Archer might crit — adjust trace key
        trace_key = "basic_attack_crit" if action_result.is_crit else "basic_attack"
        hero_trace = TraceService.get_trace(trace_key, hero.hero_class)

    elif req.action == "special_ability":
        action_result = hero.special_ability(target_enemy)
        hero_trace = TraceService.get_trace(action_result.action, hero.hero_class)

    elif req.action == "defend":
        action_result = hero.defend()
        hero_trace = TraceService.get_trace("defend", hero.hero_class)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")

    gs.battle_log.append(action_result.message)

    # Remove dead enemies
    living_enemies = [e for e in enemies if e.is_alive]
    levelled_up = False

    # Award XP if an enemy was killed
    if target_enemy not in living_enemies:
        xp_gained = target_enemy.xp_reward
        levelled_up = hero.gain_experience(xp_gained)
        gs.score += xp_gained * 10
        gs.battle_log.append(f"💫 {target_enemy.name} defeated! +{xp_gained} XP")
        if levelled_up:
            gs.battle_log.append(f"🌟 LEVEL UP! {hero.name} is now level {hero.level}!")

    # ── Enemy counter-attacks (if any enemies remain) ──
    enemy_action_result = None
    enemy_trace: CodeTrace | None = None

    if living_enemies and req.action != "defend":
        counter_enemy = living_enemies[0]
        enemy_action_result = counter_enemy.decide_action(hero)
        enemy_trace = TraceService.get_enemy_trace(enemy_action_result.action)
        gs.battle_log.append(enemy_action_result.message)

    # ── Status effect ticks ──
    for effect_msg in hero.tick_status_effects():
        gs.battle_log.append(effect_msg)
        status_messages.append(effect_msg)
    for e in living_enemies:
        for effect_msg in e.tick_status_effects():
            gs.battle_log.append(effect_msg)

    living_enemies = [e for e in living_enemies if e.is_alive]

    # ── Check game phase ──
    if not hero.is_alive:
        gs.phase = "defeat"
        gs.battle_log.append("💀 You have been defeated... Start again, brave hero.")
    elif not living_enemies:
        # All enemies in this wave defeated
        if gs.wave >= 5:
            gs.phase = "victory"
            gs.score += 1000
            gs.battle_log.append("🏆 VICTORY! You have conquered the dungeon!")
        else:
            gs.phase = "wave_complete"
            gs.battle_log.append(f"✅ Wave {gs.wave} complete! Prepare for wave {gs.wave + 1}...")
    else:
        gs.phase = "player_turn"

    gs.turn += 1
    gs.hero = hero.to_dict()
    gs.enemies = [e.to_dict() for e in living_enemies]
    gs.levelled_up = levelled_up

    # Trim battle log to last 20 entries to avoid bloat
    if len(gs.battle_log) > 20:
        gs.battle_log = gs.battle_log[-20:]

    return ActionResponse(
        game_state=gs,
        action_result=action_result.__dict__,
        code_trace=hero_trace,
        enemy_action_result=enemy_action_result.__dict__ if enemy_action_result else None,
        enemy_code_trace=enemy_trace,
        levelled_up=levelled_up,
        status_messages=status_messages,
    )


@app.post("/api/next-wave")
async def next_wave(body: dict) -> dict:
    """Advance to the next wave. Called after wave_complete phase."""
    try:
        gs = GameState(**body.get("game_state", {}))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid game state: {exc}")

    if gs.phase != "wave_complete":
        raise HTTPException(status_code=400, detail="Current wave is not yet complete.")

    next_wave_num = gs.wave + 1
    if next_wave_num > 5:
        raise HTTPException(status_code=400, detail="Already on the final wave.")

    enemy_types = _get_wave_enemies(next_wave_num)
    enemies = [create_enemy(etype, next_wave_num) for etype in enemy_types]

    # Restore hero mana between waves
    hero = _reconstruct_hero(gs.hero)
    hero._mana = min(hero._max_mana, hero._mana + hero._max_mana // 2)
    # Clear harmful status effects
    hero._status_effects = [e for e in hero._status_effects if e not in ("bleeding", "burning")]

    gs.wave = next_wave_num
    gs.turn = 1
    gs.phase = "player_turn"
    gs.hero = hero.to_dict()
    gs.enemies = [e.to_dict() for e in enemies]
    gs.battle_log.append(f"🌊 Wave {next_wave_num} begins! {', '.join(e.name for e in enemies)} appear!")

    return {"game_state": gs.model_dump()}
