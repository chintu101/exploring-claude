# CodeQuest — The OOP Arena
## Full Technical Documentation

> **Purpose:** Learn Object-Oriented Programming interactively. Every battle action triggers a live "Code Trace" that shows exactly which class fired, which method was called, and how inheritance chains resolved the logic.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Tech Stack](#3-tech-stack)
4. [OOP Concepts Demonstrated](#4-oop-concepts-demonstrated)
5. [Backend — Python Class Reference](#5-backend--python-class-reference)
   - 5.1 [Entity (ABC)](#51-entity-abc)
   - 5.2 [Character (ABC)](#52-character-abc)
   - 5.3 [Hero (ABC)](#53-hero-abc)
   - 5.4 [Warrior](#54-warrior)
   - 5.5 [Mage](#55-mage)
   - 5.6 [Archer](#56-archer)
   - 5.7 [Enemy (ABC)](#57-enemy-abc)
   - 5.8 [Goblin](#58-goblin)
   - 5.9 [Troll](#59-troll)
   - 5.10 [Dragon](#510-dragon)
   - 5.11 [Lich](#511-lich)
   - 5.12 [ActionResult (dataclass)](#512-actionresult-dataclass)
   - 5.13 [TraceService](#513-traceservice)
   - 5.14 [GameCache](#514-gamecache)
6. [Backend — Pydantic Schemas](#6-backend--pydantic-schemas)
7. [Backend — API Routes](#7-backend--api-routes)
8. [Frontend — TypeScript Types](#8-frontend--typescript-types)
9. [Frontend — React Components](#9-frontend--react-components)
   - 9.1 [HeroSelector](#91-heroselector)
   - 9.2 [BattleArena](#92-battlearena)
   - 9.3 [CodeTrace](#93-codetrace)
   - 9.4 [ClassExplorer](#94-classexplorer)
10. [Frontend — Hooks](#10-frontend--hooks)
    - 10.1 [useGameState](#101-usegamestate)
11. [Deployment Guide](#11-deployment-guide)
12. [Local Development](#12-local-development)
13. [Monetisation Strategy](#13-monetisation-strategy)

---

## 1. Project Overview

CodeQuest is a **turn-based browser RPG** where:

- The player picks a hero (Warrior, Mage, or Archer) and fights waves of monsters.
- Every action (attack, special ability, defend) triggers a **real-time Code Trace** panel that shows the Python class hierarchy involved: which `__init__` ran, which parent `calculate_base_damage()` was called via `super()`, and which concept (inheritance, polymorphism, encapsulation) was exercised.
- A **Class Explorer** sidebar lets players browse the full inheritance tree and read about each OOP concept at any time.

The educational hook: combat is the motivation, but understanding *why* the Mage hits harder with full mana is the lesson (method override + mana-scaled `calculate_base_damage()`).

---

## 2. Architecture Diagram

```
Browser
  │
  ├─ HeroSelector  ──► POST /api/new-game ──────────────────────────────┐
  │                                                                       │
  ├─ BattleArena   ──► POST /api/action  ──────────────────────────────┐ │
  │                                                                     │ │
  ├─ CodeTrace      (displays TraceStep[] returned in action response)  │ │
  │                                                                     │ │
  └─ ClassExplorer ──► GET  /api/class-hierarchy (TTL-cached 1 h) ─────┘ │
                   ──► GET  /api/concepts        (TTL-cached 1 h)        │
                                                                          │
FastAPI (Mangum → Vercel Serverless)                                      │
  │                                                                        │
  ├─ POST /api/new-game                                                    │
  │     create_hero() → create_enemy() → GameState JSON ─────────────────►┘
  │
  ├─ POST /api/action
  │     deserialise GameState from body
  │     → hero.perform_action()
  │     → TraceService.get_trace(action_key)
  │     → enemy.decide_action() + counter-attack
  │     → status ticks
  │     → check win / loss / wave complete
  │     → serialise new GameState + CodeTrace → JSON
  │
  ├─ POST /api/next-wave
  │     spawn next wave enemies (30% scaling per wave)
  │
  ├─ GET /api/class-hierarchy  ── GameCache (TTLCache 3600 s)
  └─ GET /api/concepts         ── GameCache (TTLCache 3600 s)

State store: stateless — full GameState JSON travels in every request body.
No database required.
```

---

## 3. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | Next.js 14 (App Router) | RSC + client components, Vercel-native |
| Styling | Tailwind CSS 3.4 | Utility-first, zero runtime CSS-in-JS overhead |
| Language (FE) | TypeScript 5.5 | Type-safe API contracts, great DX |
| Backend | FastAPI 0.111 | Async, automatic OpenAPI docs, Pydantic-native |
| Serverless adapter | Mangum 0.17 | Wraps ASGI app for Vercel/Lambda |
| Validation | Pydantic v2 | 5–10× faster than v1, strict typing |
| Caching | cachetools 5.3 (TTLCache) | Zero-dependency, in-memory, TTL-aware |
| Runtime (BE) | Python 3.12 / 3.13 | Modern async, pattern matching, `tomllib` |
| Deployment | Vercel | Automatic Next.js builds + Python serverless |

---

## 4. OOP Concepts Demonstrated

| Concept | Where It Appears |
|---------|-----------------|
| **Abstraction** | `Entity`, `Character`, `Hero`, `Enemy` are ABCs — you can't instantiate them directly |
| **Encapsulation** | All attributes prefixed `_` (private); exposed read-only via `@property` |
| **Inheritance** | 3-level chain: `Warrior → Hero → Character → Entity`; each layer adds behaviour |
| **Polymorphism** | `calculate_base_damage()` and `special_ability()` produce different results per subclass even when called through the same `Hero` reference |
| **Method override** | `Mage.basic_attack()` replaces the parent's attack logic entirely |
| **`super()`** | `Warrior.calculate_base_damage()` calls `super()` to get base damage then adds rage bonus |
| **Abstract methods** | `Hero.special_ability()` is `@abstractmethod` — any concrete hero *must* implement it |
| **Factory pattern** | `create_hero('Warrior', 'Arthur')` and `create_enemy('Dragon')` decouple object creation from callers |
| **Dataclasses** | `ActionResult` is a `@dataclass` — shows Python's built-in structured data pattern |

---

## 5. Backend — Python Class Reference

### 5.1 `Entity` (ABC)

**File:** `api/models.py`  
**Inherits:** `ABC` (from `abc`)  
**Role:** Root of the entire class hierarchy. Defines the minimum contract every game object must fulfil.

#### Attributes

| Name | Type | Access | Description |
|------|------|--------|-------------|
| `_name` | `str` | private | Display name of the entity |
| `_max_hp` | `int` | private | Maximum hit-points |
| `_current_hp` | `int` | private | Current hit-points (0 = dead) |

#### Properties (public read-only)

| Property | Returns | Description |
|----------|---------|-------------|
| `name` | `str` | Exposes `_name` |
| `max_hp` | `int` | Exposes `_max_hp` |
| `current_hp` | `int` | Exposes `_current_hp` |
| `is_alive` | `bool` | `_current_hp > 0` |
| `hp_percentage` | `float` | `_current_hp / _max_hp * 100` |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(name, max_hp)` | Sets `_name`, `_max_hp`, `_current_hp = max_hp` |
| `take_damage` | `(amount: int) → int` | Clamps damage ≥ 0, subtracts from `_current_hp` (floor 0), returns actual damage dealt |
| `heal` | `(amount: int) → int` | Clamps ≥ 0, adds to `_current_hp` (ceil `_max_hp`), returns actual HP restored |
| `to_dict` | `() → dict` | **Abstract.** Every subclass must serialise itself to a plain dict |

---

### 5.2 `Character` (ABC)

**File:** `api/models.py`  
**Inherits:** `Entity`  
**Role:** Adds combat statistics and status-effect logic.

#### Additional Attributes

| Name | Type | Description |
|------|------|-------------|
| `_damage` | `int` | Base damage value |
| `_defense` | `int` | Flat damage reduction |
| `_speed` | `int` | Determines turn order (higher = first) |
| `_mana` | `int` | Current mana pool |
| `_max_mana` | `int` | Maximum mana |
| `_status_effects` | `list[dict]` | Active effects: `{name, duration, value}` |
| `_experience` | `int` | (Heroes only) XP accumulator |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(name, max_hp, damage, defense, speed, max_mana)` | Calls `super().__init__()`, sets all stats |
| `apply_status` | `(name, duration, value) → None` | Appends effect dict to `_status_effects` |
| `tick_status_effects` | `() → list[str]` | Decrements durations, applies burn/bleed damage, removes expired effects; returns log lines |
| `has_status` | `(name: str) → bool` | Checks if a named effect is currently active |
| `calculate_base_damage` | `() → int` | **Virtual.** Base implementation returns `_damage`; subclasses override to modify |
| `to_dict` | `() → dict` | Extends `Entity.to_dict()` with combat stats and status list |

---

### 5.3 `Hero` (ABC)

**File:** `api/models.py`  
**Inherits:** `Character`  
**Role:** Player character base class. Adds mana economy, XP, and enforces `special_ability` contract.

#### Additional Attributes

| Name | Type | Description |
|------|------|-------------|
| `_experience` | `int` | Total XP earned (displayed in UI) |
| `_level` | `int` | Derived from XP; every 100 XP = 1 level |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(name, max_hp, damage, defense, speed, max_mana)` | Calls `super().__init__()` |
| `basic_attack` | `(target: Enemy) → ActionResult` | Calls `calculate_base_damage()`, subtracts `target.defense`, deals damage; returns `ActionResult` |
| `special_ability` | `(target: Enemy) → ActionResult` | **Abstract.** Must be implemented by every concrete hero |
| `defend` | `() → ActionResult` | Applies `defending` status for 1 turn (+5 defense), restores 10 mana |
| `gain_experience` | `(amount: int) → None` | Adds XP, recalculates `_level = xp // 100 + 1` |
| `spend_mana` | `(amount: int) → bool` | Returns `True` and deducts mana if sufficient; else `False` |
| `restore_mana` | `(amount: int) → None` | Adds mana up to `_max_mana` |

---

### 5.4 `Warrior`

**File:** `api/models.py`  
**Inherits:** `Hero → Character → Entity`  
**Archetype:** Tank / Berserker — highest HP and defense, damage scales with missing HP.

#### Stats

| Stat | Value |
|------|-------|
| `max_hp` | 150 |
| `damage` | 20 |
| `defense` | 8 |
| `speed` | 6 |
| `max_mana` | 50 |

#### Overrides

| Method | Override logic |
|--------|----------------|
| `calculate_base_damage` | Calls `super().calculate_base_damage()` for base, adds `rage_bonus = int((1 - hp_pct) * 15)` — more missing HP = more rage |
| `special_ability` | **Whirlwind Strike** (20 mana): deals 150% of `calculate_base_damage()`. Returns `ActionResult` with action key `"whirlwind_strike"` |

**Teaches:** `super()` chaining, stat-based conditional logic.

---

### 5.5 `Mage`

**File:** `api/models.py`  
**Inherits:** `Hero → Character → Entity`  
**Archetype:** Glass cannon — lowest HP, highest mana, magic bypasses physical armor.

#### Stats

| Stat | Value |
|------|-------|
| `max_hp` | 80 |
| `damage` | 12 |
| `defense` | 3 |
| `speed` | 8 |
| `max_mana` | 200 |

#### Overrides

| Method | Override logic |
|--------|----------------|
| `basic_attack` | **Full override** — magic bolt bypasses `target.defense`; damage = `calculate_base_damage()` directly. Demonstrates complete method replacement. |
| `calculate_base_damage` | `spell_power = _damage + (_mana / _max_mana) * 10` — mana level amplifies every cast |
| `special_ability` | **Fireball** (40 mana): 200% spell_power, 40% chance to apply `Burning` status (3 turns, 5 dmg/turn) |

**Teaches:** Full method override, attribute-scaling formula, status effects.

---

### 5.6 `Archer`

**File:** `api/models.py`  
**Inherits:** `Hero → Character → Entity`  
**Archetype:** Speed / Critical — fastest hero, crit system with stacking focus.

#### Stats

| Stat | Value |
|------|-------|
| `max_hp` | 100 |
| `damage` | 15 |
| `defense` | 5 |
| `speed` | 12 |
| `max_mana` | 80 |

#### Additional Attributes

| Name | Type | Description |
|------|------|-------------|
| `_focus_stacks` | `int` | Accumulate on basic attacks (max 5); boost crit rate |

#### Overrides

| Method | Override logic |
|--------|----------------|
| `calculate_base_damage` | Crit roll: `crit_chance = 0.15 + focus_stacks * 0.08`. On crit → 180% damage and reset focus. On miss → +1 focus stack |
| `special_ability` | **Rain of Arrows** (30 mana): guaranteed crit + applies `Bleeding` (2 turns, 4 dmg/turn), resets focus |

**Teaches:** State accumulation pattern, probabilistic logic, compound bonuses.

---

### 5.7 `Enemy` (ABC)

**File:** `api/models.py`  
**Inherits:** `Character`  
**Role:** AI opponent base class. Adds wave-scaling and AI decision logic.

#### Additional Attributes

| Name | Type | Description |
|------|------|-------------|
| `_xp_reward` | `int` | XP granted to hero on kill |
| `_wave_scale` | `float` | Multiplier applied to stats per wave (1.0 base) |
| `_enemy_type` | `str` | String tag for frontend icon lookup |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `decide_action` | `(target: Hero) → ActionResult` | **Virtual.** Default: basic attack. Subclasses override for special behaviour |
| `scale_for_wave` | `(wave: int) → None` | Applies `(wave - 1) * 0.3` multiplier to `_max_hp`, `_current_hp`, `_damage`. Keeps enemies challenging |
| `special_ability` | `(target: Hero) → ActionResult` | **Abstract.** Each enemy type has a named signature move |

---

### 5.8 `Goblin`

**File:** `api/models.py`  
**Inherits:** `Enemy → Character → Entity`  
**Role:** Wave 1 fodder — low HP, fast, glass jaw.

| Stat | Value |
|------|-------|
| `max_hp` | 40 |
| `damage` | 8 |
| `defense` | 2 |
| `speed` | 10 |
| `xp_reward` | 25 |

**Special — Frenzy:** Three rapid hits at 60% damage each. Action key: `"goblin_frenzy"`.

---

### 5.9 `Troll`

**File:** `api/models.py`  
**Inherits:** `Enemy → Character → Entity`  
**Role:** Tank — high HP, slow, regenerates.

| Stat | Value |
|------|-------|
| `max_hp` | 120 |
| `damage` | 14 |
| `defense` | 6 |
| `speed` | 4 |
| `xp_reward` | 60 |

#### Overrides

| Method | Logic |
|--------|-------|
| `decide_action` | If `hp_percentage < 50%`: heal 20 HP first (Regeneration), then call `super().decide_action()`. Demonstrates partial override + `super()` delegation |

**Special — Ground Slam:** High-damage AoE taunt. Action key: `"ground_slam"`.  
**Teaches:** Conditional `super()` delegation.

---

### 5.10 `Dragon`

**File:** `api/models.py`  
**Inherits:** `Enemy → Character → Entity`  
**Role:** Wave boss — massive HP, Fire Breath limited charges.

| Stat | Value |
|------|-------|
| `max_hp` | 200 |
| `damage` | 22 |
| `defense` | 10 |
| `speed` | 7 |
| `xp_reward` | 120 |

**Additional Attribute:** `_breath_charges = 3`  
**Special — Fire Breath:** 180% damage + Burning; consumes 1 charge. Falls back to basic attack when charges depleted. Action key: `"fire_breath"`.

---

### 5.11 `Lich`

**File:** `api/models.py`  
**Inherits:** `Enemy → Character → Entity`  
**Role:** Undead spellcaster — high intelligence, life-steal.

| Stat | Value |
|------|-------|
| `max_hp` | 160 |
| `damage` | 18 |
| `defense` | 5 |
| `speed` | 9 |
| `xp_reward` | 150 |

**Special — Soul Drain:** Deals 120% damage and heals the Lich for 50% of damage dealt. Action key: `"soul_drain"`.

---

### 5.12 `ActionResult` (dataclass)

**File:** `api/models.py`

```python
@dataclass
class ActionResult:
    action_key: str          # Maps to TraceService trace library
    actor_name: str          # Who performed the action
    target_name: str         # Who received it
    damage_dealt: int        # Net damage after defense
    heal_amount: int         # HP restored (if any)
    mana_cost: int           # Mana spent
    log_entry: str           # Human-readable battle log line
    status_applied: str      # Status effect name if triggered
    critical: bool           # Was it a critical hit?
    success: bool            # Did the action succeed (enough mana, etc.)?
```

Used as the universal return type of every combat method so the API layer has a consistent interface to serialise.

---

### 5.13 `TraceService`

**File:** `api/services.py`  
**Role:** Pure-static service. Maps `action_key` strings → ordered lists of `TraceStep` objects that the CodeTrace UI animates one-by-one.

#### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `_TRACE_LIBRARY` | `dict[str, list[TraceStep]]` | Maps every possible action key to its educational trace sequence |

#### Methods (all `@staticmethod`)

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_trace` | `(action_key: str) → CodeTrace` | Looks up `_TRACE_LIBRARY[action_key]`, wraps in `CodeTrace` object. Falls back to `"enemy_basic_attack"` if key unknown |
| `list_concepts` | `() → list[dict]` | Returns 8 concept definitions used by the ClassExplorer "OOP Concepts" tab |

#### Trace Keys

`basic_attack`, `magic_bolt`, `whirlwind_strike`, `fireball`, `rain_of_arrows`, `defend`, `goblin_frenzy`, `ground_slam`, `fire_breath`, `soul_drain`, `enemy_basic_attack`, `status_tick`, `special_failed`

---

### 5.14 `GameCache`

**File:** `api/cache.py`  
**Role:** Wraps two `cachetools.TTLCache` instances — one for static data (class hierarchy, concepts) and one for in-flight wave data.

#### Class Attributes

| Attribute | Type | TTL | Max entries | Description |
|-----------|------|-----|------------|-------------|
| `_static_cache` | `TTLCache` | 3600 s | 50 | Class hierarchy JSON, concept list |
| `_wave_cache` | `TTLCache` | 600 s | 20 | Pre-computed wave enemy sets |

#### Methods (all `@staticmethod`)

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_static` | `(key: str) → Any \| None` | Returns cached value or `None` |
| `set_static` | `(key, value) → None` | Stores in static cache |
| `get_wave` | `(key: str) → Any \| None` | Returns wave cache value or `None` |
| `set_wave` | `(key, value) → None` | Stores in wave cache |
| `clear_all` | `() → None` | Flushes both caches (useful in tests) |
| `stats` | `() → dict` | Returns `{static_size, static_maxsize, wave_size, wave_maxsize}` |

#### Decorator

`@cached_static(key)` — wraps a function so its return value is stored and retrieved from the static cache automatically.

---

## 6. Backend — Pydantic Schemas

**File:** `api/schemas.py`

| Schema | Direction | Fields |
|--------|-----------|--------|
| `NewGameRequest` | Request | `hero_class: str`, `hero_name: str` |
| `ActionRequest` | Request | `game_state: GameState`, `action: str`, `target_index: int = 0` |
| `TraceStep` | Response | `class_name`, `method_name`, `code_line`, `description`, `inheritance_chain: list[str]`, `concept` |
| `CodeTrace` | Response | `action_key`, `steps: list[TraceStep]`, `title`, `summary` |
| `CharacterSnapshot` | Both | `name`, `hero_class \| enemy_type`, `current_hp`, `max_hp`, `current_mana`, `max_mana`, `defense`, `speed`, `status_effects`, `is_alive` |
| `GameState` | Both | `hero: CharacterSnapshot`, `enemies: list[CharacterSnapshot]`, `wave: int`, `phase: str`, `battle_log: list[str]`, `turn: int` |
| `ActionResponse` | Response | `game_state: GameState`, `player_trace: CodeTrace`, `enemy_trace: CodeTrace \| None`, `action_result: dict` |
| `NewGameResponse` | Response | `game_state: GameState`, `hero_classes: list[str]` |
| `ClassHierarchyResponse` | Response | `hierarchy: ClassNode`, `total_classes: int` |

---

## 7. Backend — API Routes

**File:** `api/index.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/health` | None | Liveness probe — returns `{status: "ok", version}` |
| `GET` | `/api/class-hierarchy` | None | Full OOP tree (TTL-cached 1 h) |
| `GET` | `/api/concepts` | None | 8 OOP concept definitions (TTL-cached 1 h) |
| `POST` | `/api/new-game` | None | Creates hero + wave-1 enemies, returns initial `GameState` |
| `POST` | `/api/action` | None | Processes one full turn: player action → code trace → enemy counter → status ticks → win/loss check |
| `POST` | `/api/next-wave` | None | Spawns next wave with 30% scaling, returns updated `GameState` |

All routes validate input through Pydantic schemas. All 4xx/5xx errors return `{detail: str}` JSON.

---

## 8. Frontend — TypeScript Types

**File:** `src/types/game.ts`

| Type | Kind | Description |
|------|------|-------------|
| `HeroClass` | Union | `"Warrior" \| "Mage" \| "Archer"` |
| `EnemyType` | Union | `"Goblin" \| "Troll" \| "Dragon" \| "Lich"` |
| `GamePhase` | Union | `"player_turn" \| "enemy_turn" \| "wave_complete" \| "victory" \| "defeat"` |
| `PlayerAction` | Union | `"basic_attack" \| "special_ability" \| "defend"` |
| `CharacterSnapshot` | Interface | Mirrors Pydantic schema — UI state for each combatant |
| `GameState` | Interface | Full game state (serialised + deserialised each turn) |
| `TraceStep` | Interface | One animated step in the CodeTrace panel |
| `CodeTrace` | Interface | Array of `TraceStep` + metadata |
| `ActionResponse` | Interface | Full response from `POST /api/action` |
| `ClassNode` | Interface | Recursive tree node for ClassExplorer |
| `OopConcept` | Interface | `{id, name, definition, code_example, hero_example}` |
| `HeroMeta` | Interface | Static UI config per hero (icon, description, colour) |

Constants exported: `HERO_META`, `ENEMY_ICONS`, `CLASS_COLORS`

---

## 9. Frontend — React Components

### 9.1 `HeroSelector`

**File:** `src/components/HeroSelector.tsx`  
**Role:** Full-screen hero selection. Shown when `gameState === null`.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `onStart` | `(heroClass, heroName) => Promise<void>` | Calls `useGameState.startNewGame` |
| `isLoading` | `boolean` | Disables start button during API call |
| `error` | `string \| null` | Displays inline error |
| `onClearError` | `() => void` | Clears error banner |

#### Sub-components

- **`HeroCard`** — displays stat bars, special description, passive, OOP highlight for each of the 3 heroes
- Renders hero name `<input>` and validates non-empty before enabling Start button.

---

### 9.2 `BattleArena`

**File:** `src/components/BattleArena.tsx`  
**Role:** Core combat UI — HP bars, action buttons, battle log.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `gameState` | `GameState` | Current game state |
| `lastActionResult` | `object \| null` | Last action metadata for animations |
| `isLoading` | `boolean` | Shows skeleton overlay during API call |
| `error` | `string \| null` | Error toast |
| `onAction` | `(action, targetIndex?) => Promise<void>` | Dispatches player action |
| `onAdvanceWave` | `() => Promise<void>` | Advances to next wave |
| `onReset` | `() => void` | Returns to hero selection |
| `onClearError` | `() => void` | Clears error |

#### Sub-components

| Sub-component | Description |
|---------------|-------------|
| `ResourceBar` | Wave counter + XP display |
| `HeroCard` | HP/mana/XP bars, status badges, class-specific extra stat (rage/spell-power/focus) |
| `EnemyCard` | Enemy HP bar, TARGET badge on index 0 |
| `ActionButtons` | Attack / Special / Defend buttons with mana cost badges; disabled on enemy_turn |
| `BattleLog` | Scrollable last-20 log entries with fade-in animation |

Phase states render: `player_turn` → action buttons, `wave_complete` → advance prompt, `victory` / `defeat` → end screens.

---

### 9.3 `CodeTrace`

**File:** `src/components/CodeTrace.tsx`  
**Role:** Animated step-by-step trace of which class methods fired during the last action.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `playerTrace` | `CodeTrace \| null` | Trace for player's action |
| `enemyTrace` | `CodeTrace \| null` | Trace for enemy's counter-action |

#### Behaviour

- Animates `TraceStep` cards sequentially (600 ms interval) using `useEffect` + `useState` index counter.
- Hero / Enemy toggle tab shown when both traces are present.
- Each `TraceStepCard` shows: class badge (colour-coded by class), method name, `<pre>` code line, description, inheritance chain, OOP concept badge.
- `InheritanceChain` sub-component renders `Warrior → Hero → Character → Entity` with colour badges and `→` separators.
- Empty state shows instructions on how to trigger a trace.

---

### 9.4 `ClassExplorer`

**File:** `src/components/ClassExplorer.tsx`  
**Role:** Static educational panel — browse the full class hierarchy and read OOP concept definitions.

#### Props: None (fetches its own data)

#### Tabs

| Tab | Content |
|-----|---------|
| **Hierarchy** | Interactive collapsible tree. Click a node to see: full inheritance chain, abstract/concrete badge, description, all methods listed |
| **OOP Concepts** | Accordion list — 8 concepts each with a prose definition, Python code example, and in-game hero example |

#### Data fetching

- Calls `GET /api/class-hierarchy` and `GET /api/concepts` on mount.
- Caches both in `sessionStorage` so repeat panel opens skip the network call.
- Shows a skeleton loader while fetching.
- `findNode(tree, id)` recursive helper traverses the `ClassNode` tree.

---

## 10. Frontend — Hooks

### 10.1 `useGameState`

**File:** `src/hooks/useGameState.ts`  
**Role:** Single source of truth for all game state. All API calls go through here.

#### State

| State | Type | Description |
|-------|------|-------------|
| `gameState` | `GameState \| null` | Full current game state; `null` = hero selection screen |
| `activeTrace` | `CodeTrace \| null` | Player trace from last action |
| `enemyTrace` | `CodeTrace \| null` | Enemy trace from last action |
| `isLoading` | `boolean` | True during any in-flight API call |
| `error` | `string \| null` | Last error message |
| `lastActionResult` | `object \| null` | Raw action result dict for animation triggers |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `startNewGame` | `(heroClass, heroName) => Promise<void>` | POST `/api/new-game`, sets `gameState` |
| `performAction` | `(action, targetIndex?) => Promise<void>` | POST `/api/action`, updates all state |
| `advanceWave` | `() => Promise<void>` | POST `/api/next-wave` |
| `clearError` | `() => void` | Sets `error = null` |
| `resetGame` | `() => void` | Clears all state + localStorage |

#### Persistence

`gameState` is synced to `localStorage` key `"codequest_game_state"` on every update and restored on mount. This means the player can refresh the page and resume their run.

#### Request management

Every API call creates an `AbortController`. If the component unmounts mid-call the request is aborted to prevent stale state updates.

---

## 11. Deployment Guide

### One-time Vercel setup

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Link your repo
cd codequest
vercel link

# 3. Deploy
vercel --prod
```

Vercel reads `vercel.json` and automatically:
- Builds the Next.js frontend via `@vercel/next`
- Deploys `api/index.py` as a Python 3.12 serverless function
- Routes `/api/*` → Python, everything else → Next.js

### Environment variables (Vercel Dashboard → Settings → Environment Variables)

| Variable | Example | Required |
|----------|---------|----------|
| `NEXT_PUBLIC_API_URL` | *(leave blank — same origin)* | No |
| `FASTAPI_DEV_URL` | `http://127.0.0.1:8000` | Local dev only |

---

## 12. Local Development

### Backend (FastAPI)

```bash
# From project root
pip install -r requirements.txt

# Start dev server (hot-reload)
uvicorn api.index:app --reload --port 8000
```

API explorer available at: `http://localhost:8000/docs`

### Frontend (Next.js)

```bash
# From project root
npm install
npm run dev
```

App available at: `http://localhost:3000`

The `next.config.js` rewrite rule proxies `/api/*` → `http://127.0.0.1:8000` in development, so the frontend just hits relative URLs and everything works.

### Type checking

```bash
npm run type-check   # tsc --noEmit
```

---

## 13. Monetisation Strategy

| Channel | Model | Target | Est. Revenue |
|---------|-------|--------|-------------|
| **Bootcamp licensing** | $50–200 / seat / month | Coding bootcamps using CodeQuest as OOP curriculum | Primary |
| **Dungeon Packs** | $9.99 one-time or $2.99/month | New enemy sets demonstrating new patterns (design patterns, SOLID) | Secondary |
| **University white-label** | $500–2000 / semester / cohort | CS departments replacing dry textbook examples | High-value |
| **Freemium SaaS** | Free (Wave 1–3) / Pro (all waves + custom hero) | Individual learners | Volume |
| **API access** | $0.001 / trace request | Bootcamps embedding the trace engine in their own tools | Long-tail |

**Net positive to society:** OOP is the foundational pattern behind every major framework (React, Django, Spring, iOS). An engaging game that makes abstract concepts like inheritance visceral and memorable reduces the dropout rate in introductory programming courses — a measurable educational outcome.
