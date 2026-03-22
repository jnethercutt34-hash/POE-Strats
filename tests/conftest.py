"""Shared test fixtures — in-memory SQLite database for isolated tests."""

import asyncio
import os
import pytest
import pytest_asyncio

# Force test database path BEFORE any app imports
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["POE_LEAGUE"] = "TestLeague"

from app.database import get_db, init_db, close_db, _db


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for all async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Init a fresh in-memory DB for each test, tear down after."""
    import app.database as db_mod

    # Reset the singleton so each test gets a fresh connection
    db_mod._db = None

    await init_db()
    yield
    await close_db()


@pytest_asyncio.fixture
async def db():
    """Provide the active DB connection."""
    return await get_db()


@pytest_asyncio.fixture
async def seeded_db(db):
    """DB with a single test mechanic, drops, costs, and economy data."""
    # Insert a mechanic
    await db.execute(
        """INSERT INTO mechanics (name, patch_version, scaling_tags, is_scarab_heavy)
           VALUES ('TestMech', '3.25', '["quantity"]', 1)"""
    )

    cursor = await db.execute("SELECT id FROM mechanics WHERE name = 'TestMech'")
    row = await cursor.fetchone()
    mech_id = row["id"]

    # Insert drops at medium tier
    await db.execute(
        """INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
           VALUES (?, 'Chaos Orb', 'Currency', 5.0, 'medium')""",
        (mech_id,),
    )
    await db.execute(
        """INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
           VALUES (?, 'Exalted Orb', 'Currency', 0.1, 'medium')""",
        (mech_id,),
    )

    # Insert costs at medium tier
    await db.execute(
        """INSERT INTO costs (mechanic_id, item_name, ninja_type, investment_tier, quantity)
           VALUES (?, 'Scarab of Testing', 'Scarab', 'medium', 1)""",
        (mech_id,),
    )

    # Insert economy snapshots
    await db.execute(
        """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp)
           VALUES (1, 'Chaos Orb', 'Currency', 1.0, NULL, '2026-03-22T12:00:00')"""
    )
    await db.execute(
        """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp)
           VALUES (2, 'Exalted Orb', 'Currency', 15.0, 0.1, '2026-03-22T12:00:00')"""
    )
    await db.execute(
        """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp)
           VALUES (3, 'Scarab of Testing', 'Scarab', 10.0, NULL, '2026-03-22T12:00:00')"""
    )

    await db.commit()
    return db
