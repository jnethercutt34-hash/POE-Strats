"""SQLite database setup with aiosqlite — raw async SQL for MVP."""

import aiosqlite
from app.config import DATABASE_PATH

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return the singleton database connection."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def close_db():
    global _db
    if _db is not None:
        await _db.close()
        _db = None


async def init_db():
    """Create tables if they don't exist."""
    db = await get_db()
    await db.executescript(SCHEMA_SQL)
    await db.commit()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mechanics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,
    patch_version TEXT,
    meta_tier   TEXT,  -- derived/cached: S, A, B, C
    scaling_tags TEXT DEFAULT '[]',  -- JSON array
    is_scarab_heavy BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS drops (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mechanic_id     INTEGER NOT NULL REFERENCES mechanics(id),
    item_name       TEXT NOT NULL,
    ninja_id        INTEGER,  -- poe.ninja internal ID
    ninja_type      TEXT,     -- e.g. "Fossil", "Currency"
    base_yield_per_map REAL DEFAULT 0.0,
    investment_tier TEXT DEFAULT 'medium' CHECK(investment_tier IN ('low', 'medium', 'high')),
    UNIQUE(mechanic_id, item_name, investment_tier)
);

CREATE TABLE IF NOT EXISTS economy_snapshot (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ninja_id    INTEGER,
    item_name   TEXT NOT NULL,
    ninja_type  TEXT,
    chaos_value REAL,
    divine_value REAL,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now')),
    is_stale    BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS costs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mechanic_id     INTEGER NOT NULL REFERENCES mechanics(id),
    item_name       TEXT NOT NULL,
    ninja_type      TEXT,
    investment_tier TEXT DEFAULT 'medium' CHECK(investment_tier IN ('low', 'medium', 'high')),
    quantity        REAL DEFAULT 1.0,
    UNIQUE(mechanic_id, item_name, investment_tier)
);

CREATE INDEX IF NOT EXISTS idx_economy_item ON economy_snapshot(item_name);
CREATE INDEX IF NOT EXISTS idx_economy_ninja_id ON economy_snapshot(ninja_id);
CREATE INDEX IF NOT EXISTS idx_economy_timestamp ON economy_snapshot(timestamp);
CREATE INDEX IF NOT EXISTS idx_drops_mechanic ON drops(mechanic_id);
CREATE INDEX IF NOT EXISTS idx_costs_mechanic ON costs(mechanic_id);
"""
