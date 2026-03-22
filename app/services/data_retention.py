"""Economy data retention — aggregate old snapshots and purge stale data.

Policy (from plan):
- Snapshots older than 7 days: aggregate into daily averages
- Raw data older than 30 days: purge entirely
"""

import logging
from app.database import get_db

logger = logging.getLogger(__name__)


async def run_retention():
    """Run the full retention pipeline: aggregate then purge."""
    db = await get_db()

    # 1. Aggregate snapshots older than 7 days into daily averages
    #    Insert daily averages for data between 7-30 days old that hasn't been aggregated
    aggregated = await db.execute(
        """
        INSERT OR IGNORE INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp, is_stale)
        SELECT 
            ninja_id,
            item_name,
            ninja_type,
            ROUND(AVG(chaos_value), 2),
            ROUND(AVG(divine_value), 2),
            DATE(timestamp) || 'T00:00:00',  -- daily aggregate timestamp
            0
        FROM economy_snapshot
        WHERE timestamp < datetime('now', '-7 days')
          AND timestamp >= datetime('now', '-30 days')
          AND TIME(timestamp) != '00:00:00'  -- skip already-aggregated rows
        GROUP BY item_name, ninja_type, DATE(timestamp)
        """
    )
    agg_count = aggregated.rowcount

    # 2. Delete raw (non-aggregated) snapshots older than 7 days
    deleted_raw = await db.execute(
        """
        DELETE FROM economy_snapshot
        WHERE timestamp < datetime('now', '-7 days')
          AND TIME(timestamp) != '00:00:00'
        """
    )
    raw_count = deleted_raw.rowcount

    # 3. Purge everything older than 30 days
    deleted_old = await db.execute(
        """
        DELETE FROM economy_snapshot
        WHERE timestamp < datetime('now', '-30 days')
        """
    )
    old_count = deleted_old.rowcount

    await db.commit()

    result = {
        "daily_aggregates_created": agg_count,
        "raw_snapshots_deleted": raw_count,
        "old_data_purged": old_count,
    }
    logger.info("Retention complete: %s", result)
    return result
