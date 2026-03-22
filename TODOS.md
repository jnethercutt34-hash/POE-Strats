# TODOS

## Remaining

### Phase 4 — Advanced Features
- [ ] **Synergy Calculator** — Use NetworkX to load Atlas Tree JSON, calculate shortest path between mechanic notables, compare scaling_tags. Endpoint: `GET /api/synergy/{mechanic_a}/{mechanic_b}` | Effort: L | Priority: P2 (requires atlas tree JSON data)

### Data Quality
- [ ] **Validate yield data accuracy** — Current yields are estimates. Cross-reference with community data (e.g., TFT discord, CraftOfExile) | Effort: M | Priority: P2

---

## Completed

### P0 — Infrastructure Hygiene
- [x] **Add .gitignore** — Exclude `data/poe_tracker.db*`, `__pycache__`, `node_modules`, `.env`, `frontend/dist`
- [x] **Proper git history** — Meaningful commit hygiene established
- [x] **Remove tracked artifacts** — Untracked `.env`, `__pycache__/`, `.db` files from git history

### P1 — Core Gaps
- [x] **Add more mechanic .md files** — Added 9 new mechanics: Breach, Ritual, Heist, Betrayal, Incursion, Abyss, Harbinger, Essence, Sanctum (15 total)
- [x] **Frontend API proxy** — Vite dev server proxies `/api` to backend port 8000
- [x] **CORS middleware** — FastAPI CORS middleware added

### P2 — Quality & Reliability
- [x] **Tests** — 19 pytest tests covering profit engine, mechanic seeder, data retention, yield ingestor
- [x] **Error handling on frontend** — useApi hook with retry logic (3 retries, backoff), stale data detection (5min threshold), StaleIndicator component
- [x] **Handle ninja_id mismatch** — Profit engine uses fuzzy LIKE fallback when exact item_name match fails

### P3 — Advanced Features
- [x] **Patch Impact LLM Pipeline** — `POST /api/patch/analyze` sends patch notes to Gemini 2.0 Flash, returns buff/nerf JSON per mechanic. Token-limited for free tier (~3K tokens/call)
