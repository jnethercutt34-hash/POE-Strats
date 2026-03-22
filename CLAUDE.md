# POE MetaTracker — Project Context

## What This Is
A full-stack Path of Exile economy tracker that calculates real-time mechanic profitability by joining static yield data with live poe.ninja prices. Users see which PoE mechanics (Delve, Harvest, Legion, etc.) are most profitable right now.

## Tech Stack
- **Backend:** Python 3.12+, FastAPI, aiosqlite, APScheduler, httpx, pandas
- **Frontend:** React 18 + Vite + Tailwind CSS + React Router + Lucide icons
- **Database:** SQLite (WAL mode) at `data/poe_tracker.db`
- **Data Source:** poe.ninja API (polled hourly)

## Architecture

```
app/
├── main.py              # FastAPI entrypoint, lifespan (scheduler, DB init, seeding)
├── config.py            # Env vars: POE_LEAGUE, DB path, ninja URLs, item types
├── database.py          # Singleton aiosqlite connection, schema DDL
├── routers/
│   ├── economy.py       # /api/economy/* — price lookup, history, manual poll/retention
│   ├── mechanics.py     # /api/mechanics/* — list/detail, seed, yield ingest
│   └── profit.py        # /api/profit/* — profitability ranking + per-mechanic breakdown
└── services/
    ├── ninja_poller.py  # Async poe.ninja fetcher (items + currency), 1.2s rate limit
    ├── mechanic_seeder.py # Parses data/mechanics/*.md → DB (mechanics, drops, costs)
    ├── yield_ingestor.py  # Reads data/yields/*.csv|json → updates drops table
    ├── data_retention.py  # Aggregates snapshots >7d to daily avg, purges >30d
    └── profit_engine.py   # Revenue (yield×price) - costs, meta tier derivation (S/A/B/C)

data/
├── mechanics/           # Markdown files defining each mechanic (drops, costs, metadata)
│   ├── blight.md, delirium.md, delve.md, expedition.md, harvest.md, legion.md
└── yields/              # CSV/JSON yield override files (delve_yields.csv, harvest_yields.csv)

frontend/                # React SPA (Vite)
├── src/
│   ├── App.jsx          # Routes: /, /mechanics, /mechanics/:name, /economy
│   ├── pages/           # Dashboard, MechanicsList, MechanicDetail, Economy
│   ├── components/      # Navbar, ProfitCard, TierBadge, InvestmentToggle
│   └── hooks/useApi.js  # Generic fetch hook
```

## Database Schema (4 tables)
- **mechanics** — id, name, patch_version, meta_tier (S/A/B/C), scaling_tags (JSON), is_scarab_heavy
- **drops** — mechanic_id FK, item_name, ninja_id, ninja_type, base_yield_per_map, investment_tier (low/medium/high)
- **economy_snapshot** — ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp, is_stale
- **costs** — mechanic_id FK, item_name, ninja_type, investment_tier, quantity

## Key Patterns
- **Mechanic data is markdown-driven**: Add a new mechanic by creating `data/mechanics/{name}.md` with Metadata, Drops, and Costs sections. Server seeds on startup.
- **Profit = (Σ yield×price) - (base_map_cost + Σ cost_qty×cost_price)** per map, ×maps/hr for hourly
- **Meta tiers auto-derived**: Top 10% = S, 10-25% = A, 25-50% = B, rest = C. Persisted after each calculation.
- **Currency vs Item API differences**: Currency uses `currencyTypeName` + `chaosEquivalent` + `detailsId` (string). Items use `name` + `chaosValue` + `id` (int).
- **Rate limiting**: 1.2s delay between poe.ninja requests. Polling interval configurable via env var (default 60min).
- **Data retention**: Cron at midnight — aggregate >7d snapshots to daily averages, purge >30d.

## Running
```bash
# Backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Or: run_server.bat

# Frontend
cd frontend && npm install && npm run dev
```

## Environment Variables (.env)
- `POE_LEAGUE` — Current league name (changes every ~3 months). Currently: `Mirage`
- `DATABASE_PATH` — SQLite path (default: `data/poe_tracker.db`)
- `NINJA_POLL_INTERVAL_MINUTES` — Poll frequency (default: 60)

## API Quick Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/mechanics/` | List all mechanics with meta tier |
| GET | `/api/mechanics/{name}` | Mechanic detail + drops |
| POST | `/api/mechanics/seed` | Re-seed from markdown files |
| POST | `/api/mechanics/ingest-yields` | Ingest yield CSVs |
| GET | `/api/economy/` | Top 50 items by value |
| GET | `/api/economy/item/{name}` | Latest price for item |
| GET | `/api/economy/history/{name}?days=7` | Price history |
| POST | `/api/economy/poll` | Manual poe.ninja poll |
| POST | `/api/economy/retention` | Manual retention run |
| GET | `/api/profit/?investment=medium&maps_per_hour=12` | All mechanics ranked |
| GET | `/api/profit/{name}?investment=medium` | Detailed profit breakdown |

## Current State (as of 2026-03-22)
- **Phase 1 (Data Pipeline):** ✅ Complete — ninja poller, mechanic seeder, yield ingestor, data retention all working
- **Phase 2 (Profit Engine):** ✅ Complete — profit calculation with revenue/cost breakdown, meta tier derivation
- **Phase 3 (Frontend):** ✅ Scaffolded — Dashboard, MechanicsList, MechanicDetail, Economy pages built with Tailwind dark theme
- **Phase 4 (Advanced):** ❌ Not started — Synergy calculator (NetworkX), Patch impact LLM pipeline
- **6 mechanics defined:** Blight, Delirium, Delve, Expedition, Harvest, Legion
- **Single commit history** — "cc" (14729db)
