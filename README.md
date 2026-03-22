# POE MetaTracker & Profit Engine

Real-time Path of Exile mechanic profitability tracker. Combines static yield data with live [poe.ninja](https://poe.ninja) prices to rank farming strategies by chaos/hour.

## Features

- **Live Economy Data** — Polls poe.ninja hourly for 20+ item/currency types
- **Profit Calculator** — Revenue (yield × price) minus dynamic costs per mechanic
- **Meta Tier Rankings** — Auto-derived S/A/B/C tiers based on profit/hour
- **Investment Tiers** — Low/Medium/High investment comparisons per mechanic
- **Data Retention** — Auto-aggregates old snapshots, purges stale data
- **Markdown-Driven Mechanics** — Add a mechanic by dropping a `.md` file in `data/mechanics/`

## Quick Start

```bash
# Backend
pip install -r requirements.txt
cp .env.example .env  # Edit POE_LEAGUE
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Trigger initial data fetch
curl -X POST http://localhost:8000/api/economy/poll

# Frontend
cd frontend
npm install
npm run dev
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, aiosqlite |
| Scheduler | APScheduler (async) |
| HTTP Client | httpx (async, rate-limited) |
| Data Processing | pandas |
| Frontend | React 18, Vite, Tailwind CSS |
| Database | SQLite (WAL mode) |

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLite schema + connection
│   ├── routers/             # API endpoints (economy, mechanics, profit)
│   └── services/            # Business logic (poller, seeder, profit engine)
├── data/
│   ├── mechanics/           # Mechanic definitions (markdown)
│   └── yields/              # Yield override data (CSV/JSON)
├── frontend/                # React SPA
└── poe_plan.md              # Original project plan
```

## Mechanics Covered

Blight · Delirium · Delve · Expedition · Harvest · Legion

## API

Interactive docs at `http://localhost:8000/docs` (Swagger UI).

## Roadmap

- [x] Phase 1: Data pipeline (poe.ninja poller, mechanic seeder, yield ingestor)
- [x] Phase 2: Profit engine (per-mechanic profit calc, meta tier derivation)
- [x] Phase 3: Frontend UI (dashboard, mechanic pages, economy view)
- [ ] Phase 4: Synergy calculator (NetworkX atlas tree analysis)
- [ ] Phase 4: Patch impact LLM pipeline
