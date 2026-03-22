# Path of Exile: MetaTracker & Profit Engine
**Project Type:** Full-Stack Web Application
**Core Purpose:** Bridge the gap between static mechanic guides and live economy data to calculate real-time profitability and map synergies.

## 1. Tech Stack
* **Backend:** Python, FastAPI (Lightweight, async, great for API polling)
* **Database:** SQLite (MVP) -> PostgreSQL (Production)
* **Frontend:** React 18 + Vite + Tailwind CSS + React Router + Lucide icons (fresh scaffold, no legacy code)
* **Data Processing:** `pandas` (CSV/Sheet ingestion), `httpx` (async poe.ninja API calls), `NetworkX` (Atlas Tree graphing)

## 2. Database Schema (Draft)
Create the following relational structure:
* `Mechanics`: `id`, `name`, `patch_version`, `meta_tier` (derived/cached from profitability, not manually set), `scaling_tags` (JSON array, e.g., `["fast", "quantity"]`), `is_scarab_heavy`.
* `Drops`: `id`, `mechanic_id`, `item_name`, `ninja_id` (poe.ninja internal ID for reliable joins), `ninja_type` (e.g., "Fossil", "Currency"), `base_yield_per_map`, `investment_tier` (enum: "low", "medium", "high" — yields vary by scarab/investment level).
* `EconomySnapshot`: `id`, `ninja_id`, `item_name`, `chaos_value`, `divine_value`, `timestamp`. **Retention:** aggregate snapshots older than 7 days into daily averages; purge raw data older than 30 days.
* `Synergies`: Computed/cached view (not persisted) — depends on atlas tree data that changes per patch. Cache with `patch_version` key, recompute on new patches.

### 2.1 Configuration
* **League name** stored as env var (`POE_LEAGUE`) — changes every ~3 months.
* **poe.ninja polling:** handle downtime gracefully with stale-data flags and fallback to last known values.

## 3. API Endpoints
* `GET /api/mechanics` — list all mechanics with current meta tier
* `GET /api/mechanics/{name}` — detail view with drops
* `GET /api/economy/{item_name}` — price history
* `GET /api/profit/{mechanic_name}?investment=low|medium|high` — profitability with investment tiers
* `GET /api/synergy/{mechanic_a}/{mechanic_b}` — pairwise synergy comparison

## 4. Execution Phases

### Phase 1: The Data Pipeline & Base API (MVP)
**Goal:** Build the engine that fetches and stores live economy data and static baseline yields.
1. **Init FastAPI:** Setup the basic FastAPI server and SQLite database connection.
2. **poe.ninja Integration:** Write an async script (`ninja_poller.py`) to hit `https://poe.ninja/api/data/itemoverview` and `currencyoverview`. Parse the JSON to update the `EconomySnapshot` table (store `ninja_id` for each item). Set this on a 1-hour cron schedule. Include error handling for API downtime (stale-data flag, fallback to last known values).
3. **Database Seeding:** Ingest the `delve_mechanic.md` and `harvest_mechanic.md` files to populate the `Mechanics` and `Drops` tables.
4. **The Yield Ingestor:** Write a script using `pandas` to read local CSV/JSON yield files from the `data/yields/` directory. Map the columns to update the `base_yield_per_map` in the `Drops` table, with `investment_tier` differentiation. Yield data is maintained in-repo for reliability (no external Google Sheets dependency).

### Phase 2: The Profitability Engine
**Goal:** Calculate live returns based on the baseline yields and live prices.
1. **Calculation Endpoint:** Create `GET /api/profit/{mechanic_name}?investment=low|medium|high`.
2. **Logic:** - Fetch the `base_yield_per_map` for all items linked to the mechanic (filtered by investment tier).
   - Fetch the latest `chaos_value` for those items from `EconomySnapshot` (joined via `ninja_id`).
   - Calculate `Expected Return` (Yield * Value).
   - Subtract the current cost of Scarabs/Map Device options.
   - Return a structured JSON response with `total_profit_chaos`, `profit_per_hour`, and a breakdown of the highest value drops.
3. **Meta Tier Derivation:** Auto-calculate `meta_tier` (S/A/B/C) based on `profit_per_hour` rankings across all mechanics. Cache and update after each economy snapshot.

### Phase 3: The Frontend UI (The Guide Lexicon)
**Goal:** Display the data cleanly to the user.
1. **Module Layout:** Build a dynamic page component that takes a `mechanic_name` parameter.
2. **Header:** Display Mechanic Name, current Meta Tier (S, A, B), and the Live Profit per Hour (pulled from Phase 2).
3. **The Variable Engine:** Add input fields allowing users to override the `base_yield_per_map` (e.g., "I only average 2,000 Yellow Lifeforce"). Hook these inputs to instantly recalculate the Profit per Hour.
4. **Evergreen Content:** Display the static "How to Run" text (e.g., Delve Voltaxic Generator upgrade order).

### Phase 4: Advanced Modules
**Goal:** Add the "Synergy" and "Patch Note" features.
1. **The Synergy Calculator:** Use `NetworkX` to load the official PoE Atlas Tree JSON. Write a function that calculates the shortest path between Mechanic A's notables and Mechanic B's notables. Compare `scaling_tags`. Expose this via `GET /api/synergy/{mechanic_a}/{mechanic_b}`.
2. **Patch Impact LLM Pipeline:** Create a script that takes a raw text block of patch notes, passes it to an LLM API with a rigid system prompt, and returns a JSON object detailing "Buff/Nerf" status for specific mechanics to update the database.

## 5. Claude Code Starting Instructions
When executing this plan, begin strictly with **Phase 1, Step 1 & 2**. 
Do not write the frontend until the FastAPI backend successfully returns a live poe.ninja price in the terminal.
