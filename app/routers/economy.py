"""Economy data endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.services.data_retention import run_retention
from app.services.ninja_poller import get_latest_price, get_latest_snapshot_summary, poll_ninja

router = APIRouter(prefix="/api/economy", tags=["economy"])


@router.get("/")
async def economy_overview():
    """Get top 50 most valuable items from the latest snapshot."""
    items = await get_latest_snapshot_summary()
    return {"count": len(items), "items": items}


@router.get("/item/{item_name}")
async def item_price(item_name: str):
    """Get the latest price for a specific item."""
    price = await get_latest_price(item_name)
    if price is None:
        raise HTTPException(status_code=404, detail=f"No price data for '{item_name}'")
    return price


@router.get("/history/{item_name}")
async def item_price_history(
    item_name: str,
    days: int = Query(7, ge=1, le=30),
):
    """Get price history for an item over the last N days."""
    from app.database import get_db
    db = await get_db()
    cursor = await db.execute(
        """
        SELECT chaos_value, divine_value, timestamp
        FROM economy_snapshot
        WHERE item_name = ?
          AND timestamp >= datetime('now', ? || ' days')
        ORDER BY timestamp ASC
        """,
        (item_name, f"-{days}"),
    )
    rows = await cursor.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No price history for '{item_name}'")

    history = [
        {
            "chaos_value": row["chaos_value"],
            "divine_value": row["divine_value"],
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]

    # Also compute summary stats
    chaos_values = [h["chaos_value"] for h in history if h["chaos_value"] is not None]
    summary = {}
    if chaos_values:
        summary = {
            "current": chaos_values[-1],
            "min": round(min(chaos_values), 2),
            "max": round(max(chaos_values), 2),
            "avg": round(sum(chaos_values) / len(chaos_values), 2),
            "data_points": len(chaos_values),
        }

    return {
        "item_name": item_name,
        "days": days,
        "summary": summary,
        "history": history,
    }


@router.post("/poll")
async def trigger_poll():
    """Manually trigger a poe.ninja poll (for testing)."""
    result = await poll_ninja()
    return result


@router.post("/retention")
async def trigger_retention():
    """Manually run data retention (aggregate old snapshots, purge stale data)."""
    result = await run_retention()
    return result
