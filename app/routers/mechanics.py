"""Mechanics endpoints."""

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.services.mechanic_seeder import seed_mechanics
from app.services.yield_ingestor import ingest_all_yields

router = APIRouter(prefix="/api/mechanics", tags=["mechanics"])


@router.get("/")
async def list_mechanics():
    """List all mechanics with current meta tier."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, name, patch_version, meta_tier, scaling_tags, is_scarab_heavy FROM mechanics"
    )
    rows = await cursor.fetchall()
    return {
        "count": len(rows),
        "mechanics": [dict(row) for row in rows],
    }


@router.get("/{name}")
async def get_mechanic(name: str):
    """Get mechanic detail with associated drops."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, name, patch_version, meta_tier, scaling_tags, is_scarab_heavy FROM mechanics WHERE name = ?",
        (name,),
    )
    mechanic = await cursor.fetchone()
    if mechanic is None:
        raise HTTPException(status_code=404, detail=f"Mechanic '{name}' not found")

    cursor = await db.execute(
        "SELECT item_name, ninja_type, base_yield_per_map, investment_tier FROM drops WHERE mechanic_id = ?",
        (mechanic["id"],),
    )
    drops = await cursor.fetchall()

    return {
        **dict(mechanic),
        "drops": [dict(d) for d in drops],
    }


@router.post("/seed")
async def trigger_seed():
    """Re-seed mechanics from markdown files (for testing/updates)."""
    result = await seed_mechanics()
    return result


@router.post("/ingest-yields")
async def trigger_yield_ingest():
    """Ingest yield data from CSV/JSON files in data/yields/."""
    results = await ingest_all_yields()
    return {"files_processed": len(results), "results": results}
