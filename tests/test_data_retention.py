"""Tests for the data retention service."""

import pytest
from app.services.data_retention import run_retention


@pytest.mark.asyncio
async def test_retention_on_empty_db(db):
    """Retention should work fine on an empty database."""
    result = await run_retention()
    assert result["daily_aggregates_created"] == 0
    assert result["raw_snapshots_deleted"] == 0
    assert result["old_data_purged"] == 0


@pytest.mark.asyncio
async def test_retention_aggregates_old_data(db):
    """Snapshots older than 7 days should be aggregated into daily averages."""
    # Insert some "old" snapshots (10 days ago, different times)
    for hour in range(3):
        await db.execute(
            """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, timestamp)
               VALUES (1, 'Test Item', 'Currency', ?, datetime('now', '-10 days', '+' || ? || ' hours'))""",
            (10.0 + hour, str(hour)),
        )
    await db.commit()

    result = await run_retention()
    # Should have created 1 daily aggregate and deleted the 3 raw rows
    assert result["daily_aggregates_created"] >= 1
    assert result["raw_snapshots_deleted"] >= 3


@pytest.mark.asyncio
async def test_retention_purges_very_old_data(db):
    """Snapshots older than 30 days should be purged entirely."""
    await db.execute(
        """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, timestamp)
           VALUES (1, 'Ancient Item', 'Currency', 100.0, datetime('now', '-35 days'))"""
    )
    await db.commit()

    result = await run_retention()
    # The old row gets processed in one or more of the retention steps
    total_removed = result["raw_snapshots_deleted"] + result["old_data_purged"]
    assert total_removed >= 1

    # Verify it's gone (the important thing)
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM economy_snapshot WHERE item_name = 'Ancient Item'"
    )
    row = await cursor.fetchone()
    assert row["cnt"] == 0


@pytest.mark.asyncio
async def test_retention_preserves_recent_data(db):
    """Recent snapshots (< 7 days) should not be touched."""
    await db.execute(
        """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, timestamp)
           VALUES (1, 'Fresh Item', 'Currency', 50.0, datetime('now', '-1 day'))"""
    )
    await db.commit()

    await run_retention()

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM economy_snapshot WHERE item_name = 'Fresh Item'"
    )
    row = await cursor.fetchone()
    assert row["cnt"] == 1
