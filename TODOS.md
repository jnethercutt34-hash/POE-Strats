# TODOS

## Active

### Phase 4 — Advanced Features
- [ ] **Synergy Calculator** — Use NetworkX to load Atlas Tree JSON, calculate shortest path between mechanic notables, compare scaling_tags. Endpoint: `GET /api/synergy/{mechanic_a}/{mechanic_b}` | Effort: L | Priority: P2
- [ ] **Patch Impact LLM Pipeline** — Script that takes patch notes text, passes to LLM with system prompt, returns buff/nerf JSON per mechanic | Effort: L | Priority: P3

### Infrastructure
- [ ] **Add .gitignore** — Exclude `data/poe_tracker.db*`, `__pycache__`, `node_modules`, `.env`, `frontend/dist` | Effort: S | Priority: P0
- [ ] **Proper git history** — Current repo has single "cc" commit. Establish meaningful commit hygiene going forward | Effort: S | Priority: P0
- [ ] **Add more mechanic .md files** — Only 6 mechanics defined. PoE has 15+ farmable mechanics (Breach, Ritual, Heist, Betrayal, Incursion, Abyss, Harbinger, etc.) | Effort: M | Priority: P1
- [ ] **Frontend API proxy** — Vite dev server should proxy `/api` to backend port 8000 to avoid CORS issues | Effort: S | Priority: P1
- [ ] **CORS middleware** — Add FastAPI CORS middleware for frontend dev | Effort: S | Priority: P1
- [ ] **Error handling on frontend** — useApi hook has basic error handling, but no retry logic or stale data indicators | Effort: S | Priority: P2
- [ ] **Tests** — Zero test coverage. Add pytest for backend services (profit engine, seeder, poller) | Effort: M | Priority: P2

### Data Quality
- [ ] **Validate yield data accuracy** — Current yields are estimates. Cross-reference with community data (e.g., TFT discord, CraftOfExile) | Effort: M | Priority: P2
- [ ] **Handle ninja_id mismatch** — Drops table stores item_name for price lookup; if poe.ninja renames an item, joins break silently | Effort: S | Priority: P2

## Completed
_(none yet — fresh TODOS)_
