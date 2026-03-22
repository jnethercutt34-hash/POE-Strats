"""Patch Notes LLM Pipeline — Analyzes PoE patch notes for mechanic buffs/nerfs.

Uses Google Gemini (free tier) with strict token limits:
- Model: gemini-2.0-flash (15 RPM, 1M tokens/day on free tier)
- Max input: ~2000 tokens (patch notes excerpt)
- Max output: 1024 tokens (structured JSON response)
- Total per call: ~3000 tokens → can safely run 300+ analyses per day
"""

import json
import logging
from typing import Optional

from app.config import GEMINI_API_KEY
from app.database import get_db

logger = logging.getLogger(__name__)

# Hard limits for free tier safety
MAX_INPUT_CHARS = 8000  # ~2000 tokens
MAX_OUTPUT_TOKENS = 1024
MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """You are a Path of Exile economy analyst. Given patch notes text, identify changes that affect farming mechanic profitability.

For each affected mechanic, return a JSON object with:
- "mechanic": the mechanic name (must be one of: Abyss, Betrayal, Blight, Breach, Delirium, Delve, Essence, Expedition, Harbinger, Harvest, Heist, Incursion, Legion, Ritual, Sanctum)
- "impact": "buff" or "nerf" or "rework"  
- "severity": 1-5 (1=minor, 5=massive)
- "summary": one sentence explaining the change
- "affected_drops": list of specific item names affected (empty list if general)

Return ONLY a JSON array. If no mechanics are affected, return [].
Do NOT include markdown formatting, code fences, or explanation outside the JSON.

Example output:
[{"mechanic": "Harvest", "impact": "nerf", "severity": 3, "summary": "Lifeforce drop rates reduced by 20%", "affected_drops": ["Vivid Crystallised Lifeforce", "Wild Crystallised Lifeforce"]}]"""


def _get_client():
    """Lazy-init Gemini client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env — cannot analyze patch notes")
    
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


async def analyze_patch_notes(patch_text: str) -> dict:
    """Send patch notes to Gemini and return structured buff/nerf analysis.
    
    Args:
        patch_text: Raw patch notes text (will be truncated to MAX_INPUT_CHARS)
    
    Returns:
        {"mechanics": [...], "model": str, "input_chars": int, "output_tokens": int, "truncated": bool}
    """
    truncated = len(patch_text) > MAX_INPUT_CHARS
    if truncated:
        patch_text = patch_text[:MAX_INPUT_CHARS]
        logger.warning("Patch notes truncated to %d chars to stay within token limits", MAX_INPUT_CHARS)

    client = _get_client()

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"{SYSTEM_PROMPT}\n\n---\nPATCH NOTES:\n{patch_text}",
            config={
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.1,  # Low temp for structured output
            },
        )

        raw_text = response.text.strip()
        
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[-1]  # Remove first line
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3].strip()

        mechanics = json.loads(raw_text)

        # Validate structure
        valid_mechanics = {
            "Abyss", "Betrayal", "Blight", "Breach", "Delirium", "Delve",
            "Essence", "Expedition", "Harbinger", "Harvest", "Heist",
            "Incursion", "Legion", "Ritual", "Sanctum",
        }
        validated = []
        for m in mechanics:
            if isinstance(m, dict) and m.get("mechanic") in valid_mechanics:
                validated.append({
                    "mechanic": m["mechanic"],
                    "impact": m.get("impact", "unknown"),
                    "severity": min(5, max(1, int(m.get("severity", 1)))),
                    "summary": str(m.get("summary", ""))[:200],
                    "affected_drops": m.get("affected_drops", []),
                })

        output_tokens = getattr(response, 'usage_metadata', None)
        token_count = output_tokens.candidates_token_count if output_tokens else len(raw_text) // 4

        return {
            "mechanics": validated,
            "model": MODEL,
            "input_chars": len(patch_text),
            "output_tokens": token_count,
            "truncated": truncated,
        }

    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM response as JSON: %s", e)
        return {"mechanics": [], "error": f"Invalid JSON from LLM: {e}", "raw": raw_text[:500]}
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return {"mechanics": [], "error": str(e)}


async def apply_patch_impacts(analysis: list[dict]) -> dict:
    """Apply patch impact results to update mechanic notes in the database.
    
    This doesn't change yields (that requires manual verification), but stores
    the analysis for display in the frontend.
    """
    db = await get_db()
    
    # Ensure patch_impacts table exists
    await db.execute("""
        CREATE TABLE IF NOT EXISTS patch_impacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mechanic_name TEXT NOT NULL,
            impact TEXT NOT NULL,
            severity INTEGER NOT NULL,
            summary TEXT,
            affected_drops TEXT,  -- JSON array
            analyzed_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(mechanic_name, analyzed_at)
        )
    """)

    applied = 0
    for m in analysis:
        await db.execute(
            """INSERT OR REPLACE INTO patch_impacts 
               (mechanic_name, impact, severity, summary, affected_drops)
               VALUES (?, ?, ?, ?, ?)""",
            (
                m["mechanic"],
                m["impact"],
                m["severity"],
                m["summary"],
                json.dumps(m.get("affected_drops", [])),
            ),
        )
        applied += 1

    await db.commit()
    logger.info("Applied %d patch impacts to database", applied)
    return {"applied": applied}
