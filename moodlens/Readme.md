# 🔮 MoodLens — AI Mental Health Journal

> Track your mood, receive personalised AI insights, and build healthy journaling habits — powered by Claude AI.

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📸 Features

- **Mood Tracking** — Log daily entries with a 1–10 mood score and free-form journaling
- **AI Analysis** — Claude AI analyses each entry for sentiment, generates personal insights and coping strategies
- **Dashboard** — Live mood trend charts, distribution breakdown, and streak tracking
- **Weekly Insights** — AI-generated narrative summarising your emotional patterns over the week
- **Streak System** — Gamified daily journaling streaks to build healthy habits
- **Freemium Model** — 10 entries/month free, unlimited on Premium ($9.99/mo)
- **Offline-safe** — Works fully in demo mode without an API key (mock AI responses)

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 (CDN), Recharts, Pure CSS |
| Backend | FastAPI 0.115, Python 3.13 |
| Database | SQLite + SQLAlchemy 2.0 async |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| AI | Anthropic Claude (claude-haiku) |
| Cache | cachetools TTLCache (in-process, 5 min TTL) |
| Config | pydantic-settings (.env) |

---

## 📁 Project Structure

```
moodlens/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── config.py            # Environment config (pydantic-settings)
│   ├── database.py          # Async SQLAlchemy engine + session
│   ├── models.py            # ORM models: User, JournalEntry, DailyStreak
│   ├── schemas.py           # Pydantic v2 request/response DTOs
│   ├── routes/
│   │   ├── auth.py          # POST /register, POST /login, GET /me
│   │   ├── journal.py       # CRUD for journal entries
│   │   └── analytics.py     # Dashboard data + AI insights (cached)
│   ├── services/
│   │   ├── auth_service.py  # JWT + bcrypt + FastAPI dependency
│   │   ├── cache_service.py # TTLCache singleton wrapper
│   │   └── ai_service.py    # Claude API + retry + fallback
│   └── utils/
│       └── helpers.py       # Pure utility functions
├── frontend/
│   └── index.html           # React SPA (single file, no build step)
├── requirements.txt
├── .env.example
├── DOCUMENTATION.md
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- pip

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-username/moodlens.git
cd moodlens

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
```

### Configure `.env`

Open `.env` and set at minimum:

```env
SECRET_KEY=your-long-random-secret-key-here
```

To enable real AI features, add your Anthropic API key:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> 💡 No API key? The app runs in **demo mode** with mock AI responses — all other features work fully.

### Run

```bash
uvicorn backend.main:app --reload --port 8000
```

Then open **http://localhost:8000** in your browser.

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ Yes | — | JWT signing key (min 32 chars) |
| `ANTHROPIC_API_KEY` | ❌ No | `""` | Claude API key for AI features |
| `AI_MODEL` | ❌ No | `claude-haiku-4-5-20251001` | Claude model to use |
| `DEBUG` | ❌ No | `false` | Enable verbose logging |
| `DATABASE_URL` | ❌ No | `sqlite+aiosqlite:///./moodlens.db` | DB connection string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ No | `1440` | JWT lifetime (24h) |
| `CACHE_TTL_SECONDS` | ❌ No | `300` | Analytics cache lifetime |
| `FREE_TIER_MONTHLY_ENTRIES` | ❌ No | `10` | Monthly cap for free users |

---

## 📡 API Reference

Interactive docs available at **http://localhost:8000/api/docs** when the server is running.

### Auth
```
POST   /api/auth/register     Create account → returns JWT
POST   /api/auth/login        Login → returns JWT
GET    /api/auth/me           Get current user profile
```

### Journal
```
POST   /api/journal/          Submit new entry (AI-analysed)
GET    /api/journal/          Paginated entry list
GET    /api/journal/{id}      Get single entry
DELETE /api/journal/{id}      Delete entry
```

### Analytics
```
GET    /api/analytics/summary Full dashboard payload (cached 5 min)
```

### System
```
GET    /api/health            Health check
```

---

## 💰 Monetisation

| Tier | Price | Entries | AI Features |
|------|-------|---------|-------------|
| Free | $0 | 10/month | Basic analysis |
| Premium | $9.99/month | Unlimited | Full insights + weekly narrative |

**Additional revenue streams:**
- White-label API for therapy platforms
- Enterprise HR wellness integrations
- Anonymised aggregate research data

---

## 🏛️ Architecture

```
Browser (React SPA)
       │  REST/JSON
       ▼
FastAPI Backend
  ├── Routes (auth / journal / analytics)
  ├── Services (AuthService / CacheService / AIService)
  └── SQLAlchemy Async ORM
       ├── SQLite (dev) / PostgreSQL (prod)
       └── Anthropic Claude API
```

For detailed class/function documentation see [`DOCUMENTATION.md`](./DOCUMENTATION.md).

---

## 🔄 Switching to PostgreSQL

Simply update `DATABASE_URL` in your `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/moodlens
```

Install the driver:
```bash
pip install asyncpg
```

No other code changes needed.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

no license 

---

<p align="center">Built with ❤️ and Claude AI</p>
