"""Async poller for poe.ninja economy data (poe1 API endpoints)."""

import asyncio
import logging
from datetime import datetime

import httpx

from app.config import (
    NINJA_CURRENCY_OVERVIEW,
    NINJA_CURRENCY_TYPES,
    NINJA_ITEM_OVERVIEW,
    NINJA_ITEM_TYPES,
    POE_LEAGUE,
)
from app.database import get_db

logger = logging.getLogger(__name__)

# Respect poe.ninja — ~1 request per second
REQUEST_DELAY = 1.2


async def poll_ninja():
    """Fetch latest prices from poe.ninja and store snapshots."""
    logger.info("Starting poe.ninja poll for league: %s", POE_LEAGUE)
    timestamp = datetime.utcnow().isoformat()
    total_items = 0
    errors = 0

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Poll item overviews
        for item_type in NINJA_ITEM_TYPES:
            count = await _poll_item_endpoint(client, item_type, timestamp)
            if count >= 0:
                total_items += count
            else:
                errors += 1
            await asyncio.sleep(REQUEST_DELAY)

        # Poll currency overviews
        for currency_type in NINJA_CURRENCY_TYPES:
            count = await _poll_currency_endpoint(client, currency_type, timestamp)
            if count >= 0:
                total_items += count
            else:
                errors += 1
            await asyncio.sleep(REQUEST_DELAY)

    logger.info(
        "poe.ninja poll complete: %d items stored, %d errors", total_items, errors
    )
    return {"items_stored": total_items, "errors": errors, "timestamp": timestamp}


async def _poll_item_endpoint(
    client: httpx.AsyncClient,
    item_type: str,
    timestamp: str,
) -> int:
    """Poll a poe.ninja item overview endpoint. Returns item count or -1 on error."""
    params = {"league": POE_LEAGUE, "type": item_type}
    try:
        resp = await client.get(NINJA_ITEM_OVERVIEW, params=params)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, Exception) as e:
        logger.warning("Failed to fetch items/%s: %s", item_type, e)
        return -1

    items = data.get("lines", [])
    if not items:
        logger.debug("No items returned for %s", item_type)
        return 0

    db = await get_db()
    rows = []
    for item in items:
        ninja_id = item.get("id")
        item_name = item.get("name", "")
        chaos_value = item.get("chaosValue")
        divine_value = item.get("divineValue")
        rows.append((ninja_id, item_name, item_type, chaos_value, divine_value, timestamp))

    await db.executemany(
        """
        INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    await db.commit()
    logger.info("Stored %d items for type: %s", len(rows), item_type)
    return len(rows)


async def _poll_currency_endpoint(
    client: httpx.AsyncClient,
    currency_type: str,
    timestamp: str,
) -> int:
    """Poll a poe.ninja currency overview endpoint. Returns item count or -1 on error.

    Currency format differs from items:
    - currencyTypeName (not name)
    - chaosEquivalent (not chaosValue)
    - detailsId is a string slug (not integer id)
    """
    params = {"league": POE_LEAGUE, "type": currency_type}
    try:
        resp = await client.get(NINJA_CURRENCY_OVERVIEW, params=params)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, Exception) as e:
        logger.warning("Failed to fetch currency/%s: %s", currency_type, e)
        return -1

    items = data.get("lines", [])
    if not items:
        logger.debug("No currency returned for %s", currency_type)
        return 0

    db = await get_db()
    rows = []
    for item in items:
        # Currency uses detailsId (string slug) instead of numeric id
        ninja_id = item.get("detailsId", "")
        item_name = item.get("currencyTypeName", "")
        chaos_value = item.get("chaosEquivalent")
        divine_value = None  # Currency endpoint doesn't have divine values
        rows.append((ninja_id, item_name, currency_type, chaos_value, divine_value, timestamp))

    await db.executemany(
        """
        INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, divine_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    await db.commit()
    logger.info("Stored %d items for type: %s", len(rows), currency_type)
    return len(rows)


async def get_latest_price(item_name: str) -> dict | None:
    """Get the most recent price for an item."""
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT item_name, ninja_type, chaos_value, divine_value, timestamp
        FROM economy_snapshot
        WHERE item_name = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (item_name,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return {
        "item_name": row["item_name"],
        "ninja_type": row["ninja_type"],
        "chaos_value": row["chaos_value"],
        "divine_value": row["divine_value"],
        "timestamp": row["timestamp"],
    }


async def get_latest_snapshot_summary() -> list[dict]:
    """Get the latest price for every item (most recent snapshot only)."""
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT item_name, ninja_type, chaos_value, divine_value, timestamp
        FROM economy_snapshot
        WHERE timestamp = (SELECT MAX(timestamp) FROM economy_snapshot)
        ORDER BY chaos_value DESC
        LIMIT 50
        """
    )
    rows = await cursor.fetchall()
    return [
        {
            "item_name": row["item_name"],
            "ninja_type": row["ninja_type"],
            "chaos_value": row["chaos_value"],
            "divine_value": row["divine_value"],
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]
