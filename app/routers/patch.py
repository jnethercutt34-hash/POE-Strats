"""Patch notes analysis endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.patch_analyzer import analyze_patch_notes, apply_patch_impacts
from app.database import get_db

router = APIRouter(prefix="/api/patch", tags=["patch"])


class PatchNotesInput(BaseModel):
    """Request body for patch notes analysis."""
    text: str = Field(..., min_length=10, max_length=50000, description="Raw patch notes text")


@router.post("/analyze")
async def analyze(body: PatchNotesInput):
    """Analyze patch notes text for mechanic buffs/nerfs using Gemini LLM.
    
    Token-limited for free tier: input truncated to ~2000 tokens, output capped at 1024 tokens.
    """
    result = await analyze_patch_notes(body.text)

    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])

    # Auto-apply impacts to database
    if result["mechanics"]:
        apply_result = await apply_patch_impacts(result["mechanics"])
        result["applied"] = apply_result["applied"]

    return result


@router.get("/impacts")
async def get_impacts():
    """Get all stored patch impact analyses."""
    db = await get_db()

    # Check if table exists
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='patch_impacts'"
    )
    if not await cursor.fetchone():
        return {"impacts": []}

    cursor = await db.execute(
        """SELECT mechanic_name, impact, severity, summary, affected_drops, analyzed_at
           FROM patch_impacts ORDER BY analyzed_at DESC, severity DESC"""
    )
    rows = await cursor.fetchall()

    import json
    return {
        "impacts": [
            {
                "mechanic": row["mechanic_name"],
                "impact": row["impact"],
                "severity": row["severity"],
                "summary": row["summary"],
                "affected_drops": json.loads(row["affected_drops"]) if row["affected_drops"] else [],
                "analyzed_at": row["analyzed_at"],
            }
            for row in rows
        ]
    }


@router.delete("/impacts")
async def clear_impacts():
    """Clear all stored patch impacts."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='patch_impacts'"
    )
    if await cursor.fetchone():
        await db.execute("DELETE FROM patch_impacts")
        await db.commit()
    return {"cleared": True}
