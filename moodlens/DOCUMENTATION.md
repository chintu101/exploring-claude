# MoodLens — Complete Technical Documentation

> AI-powered mental health journal. Track your mood, receive personalised Claude AI insights, and build healthy journaling habits.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [System Diagram](#system-diagram)
3. [Tech Stack](#tech-stack)
4. [Monetisation Model](#monetisation-model)
5. [Project Structure](#project-structure)
6. [Module Reference](#module-reference)
   - [config.py](#configpy)
   - [database.py](#databasepy)
   - [models.py](#modelspy)
   - [schemas.py](#schemaspy)
   - [services/auth_service.py](#servicesauth_servicepy)
   - [services/cache_service.py](#servicescache_servicepy)
   - [services/ai_service.py](#servicesai_servicepy)
   - [utils/helpers.py](#utilshelperspy)
   - [routes/auth.py](#routesauthpy)
   - [routes/journal.py](#routesjournalpy)
   - [routes/analytics.py](#routesanalyticspy)
   - [main.py](#mainpy)
7. [Frontend Architecture](#frontend-architecture)
8. [Caching Strategy](#caching-strategy)
9. [Running the App](#running-the-app)
10. [API Reference](#api-reference)

---

## Architecture Overview

MoodLens follows a clean **3-tier web application** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT BROWSER                          │
│          React SPA (CDN-based, single index.html)            │
│  Components: AuthScreen │ Dashboard │ NewEntry │ History      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS REST (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ /api/auth   │  │ /api/journal │  │ /api/analytics     │  │
│  │  • register │  │  • create    │  │  • summary (cached)│  │
│  │  • login    │  │  • list      │  │  • weekly insight  │  │
│  │  • me       │  │  • get       │  └────────────────────┘  │
│  └─────────────┘  │  • delete    │                          │
│                   └──────────────┘                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    SERVICE LAYER                        │  │
│  │  AuthService │ CacheService (TTLCache) │ AIService      │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy Async ORM                       │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────┬───────────────────────┬─────────────────┘
                    │                       │
                    ▼                       ▼
         ┌──────────────────┐    ┌────────────────────┐
         │  SQLite Database  │    │   Anthropic Claude  │
         │  (moodlens.db)    │    │   API (ai_service)  │
         │  • users          │    │   • entry analysis  │
         │  • journal_entries│    │   • weekly insight  │
         │  • daily_streaks  │    └────────────────────┘
         └──────────────────┘
```

---

## System Diagram

```
User Request Flow
─────────────────
                                      ┌──────────────┐
Browser ──POST /api/journal/──────────► auth_service  │
                                      │ get_current_  │
                                      │ user()        │
                                      └──────┬───────┘
                                             │ User ORM
                                             ▼
                                      ┌──────────────┐
                                      │ journal.py   │
                                      │ create_entry │
                                      │  • tier check│
                                      │  • save entry│
                                      └──────┬───────┘
                                             │ JournalEntry
                                             ▼
                                      ┌──────────────┐
                                      │  ai_service  │
                                      │  analyse_    │
                                      │  entry()     │
                                      │  [+ retry]   │
                                      └──────┬───────┘
                                             │ EntryAnalysis
                                             ▼
                                      ┌──────────────┐
                                      │  cache_svc   │
                                      │ invalidate_  │
                                      │ user()       │
                                      └──────┬───────┘
                                             │
                                             ▼
                                    201 JournalEntryOut
```

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Frontend** | React 18 (CDN) + Recharts | No build step, instant hackathon demo |
| **Styling** | Pure CSS (custom design system) | Full control, no framework lock-in |
| **Backend** | FastAPI 0.115 | Async, auto OpenAPI docs, Pydantic v2 native |
| **ORM** | SQLAlchemy 2.0 (async) | Type-safe, async-first, production-ready |
| **Database** | SQLite + aiosqlite | Zero setup, swap URL for PostgreSQL in prod |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | Industry standard, stateless |
| **Cache** | cachetools TTLCache | In-process, zero infrastructure needed |
| **AI** | Anthropic Claude (claude-haiku) | Fast, cheap, high-quality NLP |
| **Retries** | tenacity | Exponential backoff for API calls |
| **Config** | pydantic-settings | Type-safe env vars, .env file support |

---

## Monetisation Model

```
FREE TIER (Freemium Acquisition)          PREMIUM ($9.99/month)
─────────────────────────────────         ──────────────────────
• 10 journal entries/month                • Unlimited entries
• Basic mood tracking                     • Full AI insights on every entry
• 7-day trend chart                       • 90-day trend charts
• AI analysis (limited)                   • AI weekly narrative insight
• Streak tracking                         • Coping strategy personalisation
                                          • Data export (CSV/PDF)
                                          • Priority API (faster AI)

B2B OPPORTUNITY:
• White-label API for therapy platforms ($500–5k/month)
• HR wellness integrations (per-seat enterprise pricing)
• Aggregate anonymous insights sold to researchers
```

**Revenue projections (conservative):**
- 10,000 free users → 5% conversion → 500 × $9.99 = **$4,995 MRR** at launch
- Year 1 target: 100k users → $50k MRR = **$600k ARR**

---

## Project Structure

```
moodlens/
├── backend/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app + lifespan + routing
│   ├── config.py            ← Pydantic settings (env vars)
│   ├── database.py          ← Async SQLAlchemy engine + session
│   ├── models.py            ← ORM models (User, JournalEntry, DailyStreak)
│   ├── schemas.py           ← Pydantic v2 request/response DTOs
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          ← POST /register, POST /login, GET /me
│   │   ├── journal.py       ← CRUD for journal entries
│   │   └── analytics.py     ← Dashboard data + AI insights (cached)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py  ← JWT + bcrypt + FastAPI dependency
│   │   ├── cache_service.py ← TTLCache wrapper (singleton)
│   │   └── ai_service.py    ← Claude API integration + retry + fallback
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       ← Pure utility functions (no app imports)
├── frontend/
│   └── index.html           ← React SPA (CDN, single file)
├── requirements.txt
├── .env.example
└── DOCUMENTATION.md
```

---

## Module Reference

---

### `config.py`

**Purpose:** Central configuration object loaded from environment variables and `.env` file.

**Class: `Settings(BaseSettings)`**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_name` | `str` | `"MoodLens"` | Application display name |
| `app_version` | `str` | `"1.0.0"` | Semantic version |
| `debug` | `bool` | `False` | Enable SQLAlchemy echo + verbose logging |
| `secret_key` | `str` | (placeholder) | HMAC key for JWT signing |
| `algorithm` | `str` | `"HS256"` | JWT signing algorithm |
| `access_token_expire_minutes` | `int` | `1440` | JWT lifetime (24h) |
| `database_url` | `str` | `sqlite+aiosqlite://` | DB connection string |
| `anthropic_api_key` | `str` | `""` | Claude API key |
| `ai_model` | `str` | `claude-haiku-4-5-20251001` | Claude model |
| `ai_max_tokens` | `int` | `800` | Max tokens per AI response |
| `cache_ttl_seconds` | `int` | `300` | Cache entry lifetime (5 min) |
| `cache_max_size` | `int` | `256` | Max cache entries before LRU eviction |
| `free_tier_monthly_entries` | `int` | `10` | Monthly cap for free users |
| `premium_price_usd` | `float` | `9.99` | Premium subscription price |

**Singleton:** `settings = Settings()` — imported by all modules.

---

### `database.py`

**Purpose:** Async SQLAlchemy engine, session factory, and `create_tables` utility.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_db` | `async () → AsyncGenerator[AsyncSession]` | FastAPI dependency. Yields a session per request. Auto-commits on success, rolls back on exception, always closes. |
| `create_tables` | `async () → None` | Runs `Base.metadata.create_all` — called once on startup. Idempotent. |

**Classes:**

| Class | Parent | Description |
|-------|--------|-------------|
| `Base` | `DeclarativeBase` | All ORM models inherit from this |

**Module-level objects:**

| Name | Type | Description |
|------|------|-------------|
| `engine` | `AsyncEngine` | Shared async SQLite engine |
| `AsyncSessionFactory` | `async_sessionmaker` | Session factory used by `get_db` |

---

### `models.py`

**Purpose:** SQLAlchemy ORM models defining the database schema.

#### Class Hierarchy

```
Base (DeclarativeBase)
 └── TimestampMixin          [adds created_at, updated_at]
      ├── User
      ├── JournalEntry
      └── DailyStreak
```

#### `TimestampMixin`

| Attribute | Type | Description |
|-----------|------|-------------|
| `created_at` | `datetime` | Auto-set on INSERT by the database |
| `updated_at` | `datetime` | Auto-updated on every UPDATE |

#### `User`

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `int` | Primary key (auto-increment) |
| `email` | `str` | Unique login email (indexed) |
| `username` | `str` | Display name (max 64 chars) |
| `hashed_password` | `str` | bcrypt hash — never plaintext |
| `is_active` | `bool` | Soft-disable without deleting |
| `tier` | `SubscriptionTier` | `FREE` or `PREMIUM` |
| `entries_this_month` | `int` | Counter for free-tier enforcement |
| `entries` | `list[JournalEntry]` | One-to-many relationship |
| `streak` | `DailyStreak \| None` | One-to-one relationship |

#### `JournalEntry`

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `int` | Primary key |
| `user_id` | `int` | FK → users.id (CASCADE DELETE) |
| `content` | `str` | Raw journal text (max 4000 chars) |
| `mood_score` | `int` | Self-reported 1–10 score |
| `mood_label` | `MoodLabel` | Derived enum from score |
| `ai_sentiment` | `float \| None` | Claude sentiment score (-1.0 to 1.0) |
| `ai_summary` | `str \| None` | One-sentence AI summary |
| `ai_insight` | `str \| None` | Personalised AI reflection |
| `ai_coping_tips` | `str \| None` | Newline-separated suggestions |
| `is_processed` | `bool` | False until AI analysis completes |
| `user` | `User` | Back-reference to owning user |

#### `DailyStreak`

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `int` | Primary key |
| `user_id` | `int` | FK → users.id (UNIQUE — one per user) |
| `current_streak` | `int` | Consecutive days journaled |
| `longest_streak` | `int` | All-time best streak |
| `last_entry_date` | `datetime \| None` | UTC datetime of last entry |
| `user` | `User` | Back-reference to User |

#### Enums

| Enum | Values |
|------|--------|
| `SubscriptionTier` | `FREE`, `PREMIUM` |
| `MoodLabel` | `VERY_BAD`, `BAD`, `NEUTRAL`, `GOOD`, `VERY_GOOD` |

---

### `schemas.py`

**Purpose:** Pydantic v2 DTOs for request validation and response serialisation.

| Schema | Direction | Description |
|--------|-----------|-------------|
| `UserRegister` | Request | email, username, password |
| `UserLogin` | Request | email, password |
| `Token` | Response | access_token, token_type |
| `UserOut` | Response | Safe user profile (no password) |
| `JournalEntryCreate` | Request | content (10–4000), mood_score (1–10) |
| `JournalEntryOut` | Response | Full entry with all AI fields |
| `JournalEntryBrief` | Response | Lightweight summary for list views |
| `PaginatedEntries` | Response | items, total, page, page_size, has_next |
| `MoodDataPoint` | Response | date, mood_score, ai_sentiment |
| `MoodDistribution` | Response | Count per mood label |
| `StreakInfo` | Response | current, longest, last_entry_date |
| `AnalyticsSummary` | Response | Full dashboard payload |
| `MessageResponse` | Response | Generic success/error message |

---

### `services/auth_service.py`

**Purpose:** JWT creation/validation, password hashing, and the `get_current_user` FastAPI dependency.

**Class: `AuthService`**

All methods are static — no instance state.

| Method | Signature | Description |
|--------|-----------|-------------|
| `hash_password` | `(plain: str) → str` | bcrypt hash of password |
| `verify_password` | `(plain: str, hashed: str) → bool` | bcrypt verify |
| `create_access_token` | `(user_id: int, email: str) → str` | Sign JWT with expiry |
| `decode_token` | `(token: str) → dict` | Verify + decode JWT; raises 401 on failure |

**FastAPI Dependency:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_current_user` | `async (credentials, db) → User` | Extracts Bearer token, decodes it, loads User from DB. Raises 401/403/404 as appropriate. |

---

### `services/cache_service.py`

**Purpose:** In-process TTL cache for analytics queries. Prevents repeated DB aggregation on dashboard refreshes.

**Class: `CacheService`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `_cache` | `TTLCache` | Underlying cachetools cache (maxsize + TTL from settings) |

| Method | Signature | Description |
|--------|-----------|-------------|
| `_key` | `(namespace, user_id) → str` | Build namespaced key e.g. `"analytics_summary:42"` |
| `get` | `(namespace, user_id) → Any \| None` | Return cached value or None |
| `set` | `(namespace, user_id, value) → None` | Store value (auto-expires after TTL) |
| `invalidate` | `(namespace, user_id) → None` | Delete a specific entry |
| `invalidate_user` | `(user_id) → None` | Delete ALL entries for a user (called after new entry) |
| `clear` | `() → None` | Flush entire cache (testing) |

**Singleton:** `cache = CacheService()`

---

### `services/ai_service.py`

**Purpose:** Claude API integration with retry logic, structured JSON parsing, and graceful fallback.

**Dataclasses:**

| Class | Attributes | Description |
|-------|-----------|-------------|
| `EntryAnalysis` | sentiment, summary, insight, coping_tips | Result of single-entry analysis |
| `WeeklyInsight` | insight | Multi-sentence weekly narrative |

**Class: `AIService`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `_model` | `str` | Claude model string from settings |
| `_client` | `anthropic.Anthropic \| None` | API client (None if no key) |

| Method | Signature | Description |
|--------|-----------|-------------|
| `analyse_entry` | `async (content, mood_score) → EntryAnalysis` | Main public method. Returns mock if no API key. |
| `generate_weekly_insight` | `async (entries_text) → WeeklyInsight` | Weekly AI narrative. Returns fallback if no key. |
| `_call_entry_analysis` | `async (content, mood_score) → EntryAnalysis` | **Private.** Calls Claude with `@retry` (3 attempts, exponential backoff). |
| `_call_weekly_insight` | `async (entries_text) → WeeklyInsight` | **Private.** Calls Claude with retry. |
| `_build_entry_prompt` | `(content, mood_score) → str` | Constructs the Claude prompt for entry analysis |
| `_build_weekly_prompt` | `(entries_text) → str` | Constructs the weekly insight prompt |
| `_parse_entry_analysis` | `(raw: str) → EntryAnalysis` | Strips markdown fences, parses JSON, applies fallback on failure |
| `_fallback_entry_analysis` | `() → EntryAnalysis` | Generic fallback when parsing fails |
| `_mock_entry_analysis` | `(mood_score) → EntryAnalysis` | Deterministic mock for no-API-key mode |

**Singleton:** `ai_service = AIService()`

---

### `utils/helpers.py`

**Purpose:** Pure stateless utility functions. No imports from other app modules (except models for enums).

| Function | Signature | Description |
|----------|-----------|-------------|
| `score_to_mood_label` | `(score: int) → MoodLabel` | Map 1–10 → MoodLabel enum |
| `calculate_streak` | `(current, longest, last_entry_date) → (int, int)` | Compute new streak values. Handles yesterday=+1, today=no change, gap=reset to 1. |
| `format_entries_for_ai` | `(entries: list) → str` | Format up to 7 JournalEntry ORM objects as a Claude-ready string (truncated for token limits) |

---

### `routes/auth.py`

**Prefix:** `/api/auth`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/register` | `POST` | None | Create account. Returns JWT. Raises 409 on duplicate email. |
| `/login` | `POST` | None | Authenticate. Returns JWT. Raises 401 on wrong credentials. |
| `/me` | `GET` | Bearer | Return current user's profile as `UserOut`. |

---

### `routes/journal.py`

**Prefix:** `/api/journal`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | `POST` | Bearer | Create entry. Enforces free-tier limit (402). Runs AI analysis. Updates streak. Invalidates cache. |
| `/` | `GET` | Bearer | Paginated entry list (`?page=1&page_size=10`). Returns `PaginatedEntries`. |
| `/{id}` | `GET` | Bearer | Full entry detail with AI fields. Raises 404 if not found or not owned. |
| `/{id}` | `DELETE` | Bearer | Delete entry. Invalidates cache. |

**Business logic in `create_entry`:**
1. Check free-tier limit (402 if exceeded)
2. Persist entry with `mood_label` derived from `score_to_mood_label`
3. Await `ai_service.analyse_entry()` → update AI fields
4. Increment `entries_this_month` on User
5. Call `calculate_streak()` → update or create `DailyStreak`
6. Call `cache.invalidate_user()` so dashboard reflects new data

---

### `routes/analytics.py`

**Prefix:** `/api/analytics`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/summary` | `GET` | Bearer | Full `AnalyticsSummary` (cached 5 min). Aggregates trend, distribution, streak, averages, AI weekly insight. |

**Caching namespaces:**
- `"analytics_summary"` — full dashboard payload
- `"weekly_insight"` — AI narrative (separate cache so it survives summary refresh)

**Private helper:**
- `_get_weekly_insight(user_id, entries)` — returns cached or freshly generated insight

---

### `main.py`

**Purpose:** FastAPI application factory with lifespan, CORS, error handling, static file serving, and SPA catch-all.

| Component | Description |
|-----------|-------------|
| `lifespan` | Async context manager: calls `create_tables()` on startup, logs on shutdown |
| `app` | FastAPI instance with OpenAPI at `/api/docs` |
| `CORSMiddleware` | Allows all origins (tighten in production) |
| `global_exception_handler` | Catches unhandled exceptions, returns 500 with safe message (no stack trace leak) |
| `/api/health` | Lightweight health check |
| `StaticFiles("/static")` | Serves `frontend/` directory |
| `/{full_path:path}` | SPA catch-all → returns `frontend/index.html` |

---

## Frontend Architecture

The frontend is a single-file React 18 SPA loaded from CDN (no build step required).

### Component Tree

```
App
 ├── AuthScreen          ← shown when no JWT in localStorage
 │    └── form (login/register)
 └── AppShell (authenticated)
      ├── Sidebar
      │    └── nav-items (Dashboard, New Entry, History)
      └── MainContent
           ├── Dashboard
           │    ├── stats-grid (4 StatCards)
           │    ├── AreaChart (mood trend)
           │    ├── PieChart (distribution)
           │    └── InsightBox (AI weekly)
           ├── NewEntry
           │    ├── MoodSlider (range 1–10)
           │    ├── textarea
           │    └── EntryResult (shown after save)
           │         ├── InsightBox
           │         ├── SentimentBar
           │         └── CopingTips
           └── History
                ├── EntryCard[] (paginated)
                └── EntryDetailModal (on click)
```

### State Management

All state is local React state (`useState`) — no Redux/Zustand needed at this scale.

| Component | Key State | Description |
|-----------|-----------|-------------|
| `App` | `token`, `user`, `page` | JWT from localStorage, user profile, current view |
| `Dashboard` | `analytics`, `loading` | Dashboard data fetched on mount |
| `NewEntry` | `content`, `moodScore`, `result` | Form state + AI result |
| `History` | `entries`, `page`, `detailEntry` | Paginated list + modal |

---

## Caching Strategy

```
Request: GET /api/analytics/summary
         │
         ▼
    cache.get("analytics_summary", user_id)
         │
    HIT ─┤──────────────────────────► Return cached AnalyticsSummary
         │
    MISS─┤
         ▼
    DB query (up to 90 entries)
    + aggregate trend/distribution
    + fetch/generate AI weekly insight
         │
         ▼
    cache.set("analytics_summary", user_id, result)   [TTL=5min]
         │
         ▼
    Return AnalyticsSummary

─────────────────────────────────────────────────────────────

POST /api/journal/  ──► cache.invalidate_user(user_id)
                        (clears analytics_summary + weekly_insight)
```

This ensures:
- **Dashboard loads fast** on repeated refreshes (no DB hit)
- **Fresh data** after every new journal entry
- **No Redis needed** — in-process cache works for single-instance deployments

---

## Running the App

### Prerequisites
- Python 3.13+
- pip

### Setup

```bash
# 1. Clone and enter the directory
cd moodlens

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY (optional — app runs with mocks without it)

# 5. Start the server
uvicorn backend.main:app --reload --port 8000
```

### Access

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | React SPA (main app) |
| `http://localhost:8000/api/docs` | Interactive OpenAPI docs (Swagger UI) |
| `http://localhost:8000/api/health` | Health check |

---

## API Reference

### Authentication

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

### Endpoints Summary

```
POST   /api/auth/register          Register new account
POST   /api/auth/login             Login, receive JWT
GET    /api/auth/me                Get current user profile

POST   /api/journal/               Create journal entry (AI-analysed)
GET    /api/journal/               List entries (paginated)
GET    /api/journal/{id}           Get single entry
DELETE /api/journal/{id}           Delete entry

GET    /api/analytics/summary      Full dashboard analytics (cached)

GET    /api/health                 Health check
```

### Error Codes

| Code | Meaning |
|------|---------|
| 400 | Validation error |
| 401 | Missing / invalid / expired JWT |
| 402 | Free-tier entry limit reached |
| 403 | Account inactive |
| 404 | Resource not found |
| 409 | Email already registered |
| 500 | Internal server error |

---

*Documentation generated for MoodLens v1.0.0 — Built for hackathon demonstration*
