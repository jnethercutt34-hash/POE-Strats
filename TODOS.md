# TODOS

## Active

### Phase 4 — Advanced Features
- [ ] **Synergy Calculator** — Use NetworkX to load Atlas Tree JSON, calculate shortest path between mechanic notables, compare scaling_tags. Endpoint: `GET /api/synergy/{mechanic_a}/{mechanic_b}` | Effort: L | Priority: P2
- [x] **Patch Impact LLM Pipeline** — POST /api/patch/analyze takes patch notes text, sends to Gemini 2.0 Flash with structured prompt, returns buff/nerf JSON per mechanic. Token-limited for free tier (~3K tokens/call). | Effort: L | Priority: P3 ✅

### Infrastructure
- [x] **Add .gitignore** — Exclude `data/poe_tracker.db*`, `__pycache__`, `node_modules`, `.env`, `frontend/dist` | Effort: S | Priority: P0 ✅
- [x] **Proper git history** — Meaningful commit hygiene established | Effort: S | Priority: P0 ✅
- [x] **Add more mechanic .md files** — Added 9 new mechanics: Breach, Ritual, Heist, Betrayal, Incursion, Abyss, Harbinger, Essence, Sanctum (15 total) | Effort: M | Priority: P1 ✅
- [x] **Frontend API proxy** — Vite dev server proxies `/api` to backend port 8000 | Effort: S | Priority: P1 ✅
- [x] **CORS middleware** — FastAPI CORS middleware added | Effort: S | Priority: P1 ✅
- [x] **Error handling on frontend** — useApi hook now has retry logic (3 retries, backoff), stale data detection (5min threshold), and StaleIndicator component | Effort: S | Priority: P2 ✅
- [x] **Tests** — 19 pytest tests covering profit engine, mechanic seeder, data retention, yield ingestor | Effort: M | Priority: P2 ✅

### Data Quality
- [ ] **Validate yield data accuracy** — Current yields are estimates. Cross-reference with community data (e.g., TFT discord, CraftOfExile) | Effort: M | Priority: P2
- [x] **Handle ninja_id mismatch** — Profit engine now uses fuzzy LIKE fallback when exact item_name match fails | Effort: S | Priority: P2 ✅

## Remaining
- [ ] **Synergy Calculator** — NetworkX atlas tree pathing, `GET /api/synergy/{a}/{b}` | Effort: L | Priority: P2 (requires atlas tree JSON data)
- [ ] **Validate yield data accuracy** — Cross-reference yields with community data | Effort: M | Priority: P2

## Completed
- [x] P0: .gitignore, git hygiene, removed tracked artifacts
- [x] P1: 9 new mechanics (15 total), CORS middleware, Vite proxy
- [x] P2: 19 pytest tests, frontend retry/stale logic, fuzzy price matching
- [x] P3: Gemini-powered patch notes analyzer
