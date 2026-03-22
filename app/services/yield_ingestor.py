"""Ingest yield data from CSV/JSON files in data/yields/ to update drops table.

Supports two modes:
1. Update existing drops (matched by mechanic name from filename + item_name + investment_tier)
2. Insert new drops for existing mechanics

File naming convention:
- CSV: {mechanic_name}_yields.csv  (e.g., delve_yields.csv)
- JSON: {mechanic_name}_yields.json

CSV columns: item_name, ninja_type, investment_tier, base_yield_per_map [, notes]
JSON format: [{"item_name": ..., "ninja_type": ..., "investment_tier": ..., "base_yield_per_map": ...}, ...]
"""

import json
import logging
from pathlib import Path

import pandas as pd

from app.database import get_db

logger = logging.getLogger(__name__)

YIELDS_DIR = Path("data/yields")


def _mechanic_name_from_filename(filepath: Path) -> str:
    """Extract mechanic name from filename: 'delve_yields.csv' -> 'Delve'."""
    stem = filepath.stem  # e.g., "delve_yields"
    name = stem.replace("_yields", "").replace("_", " ").title()
    return name


def _load_csv(filepath: Path) -> pd.DataFrame:
    """Load a yield CSV file into a DataFrame."""
    df = pd.read_csv(filepath)
    required = {"item_name", "ninja_type", "investment_tier", "base_yield_per_map"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {filepath.name}: {missing}")
    # Normalize
    df["investment_tier"] = df["investment_tier"].str.strip().str.lower()
    df["item_name"] = df["item_name"].str.strip()
    df["ninja_type"] = df["ninja_type"].str.strip()
    df["base_yield_per_map"] = pd.to_numeric(df["base_yield_per_map"], errors="coerce").fillna(0.0)
    return df[["item_name", "ninja_type", "investment_tier", "base_yield_per_map"]]


def _load_json(filepath: Path) -> pd.DataFrame:
    """Load a yield JSON file into a DataFrame."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    required = {"item_name", "ninja_type", "investment_tier", "base_yield_per_map"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing fields in {filepath.name}: {missing}")
    df["investment_tier"] = df["investment_tier"].str.strip().str.lower()
    return df[["item_name", "ninja_type", "investment_tier", "base_yield_per_map"]]


async def ingest_yield_file(filepath: Path) -> dict:
    """Ingest a single yield file, updating/inserting drops for the matched mechanic.
    
    Returns: {"mechanic": str, "updated": int, "inserted": int, "skipped": int}
    """
    mechanic_name = _mechanic_name_from_filename(filepath)
    
    # Load data based on file type
    if filepath.suffix == ".csv":
        df = _load_csv(filepath)
    elif filepath.suffix == ".json":
        df = _load_json(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filepath.suffix}")

    db = await get_db()

    # Find the mechanic
    cursor = await db.execute(
        "SELECT id FROM mechanics WHERE LOWER(name) = LOWER(?)", (mechanic_name,)
    )
    row = await cursor.fetchone()
    if row is None:
        logger.warning("Mechanic '%s' not found in DB — skipping %s", mechanic_name, filepath.name)
        return {"mechanic": mechanic_name, "updated": 0, "inserted": 0, "skipped": len(df), "error": "mechanic not found"}

    mechanic_id = row["id"]
    updated = 0
    inserted = 0
    skipped = 0

    for _, row_data in df.iterrows():
        item_name = row_data["item_name"]
        ninja_type = row_data["ninja_type"]
        investment_tier = row_data["investment_tier"]
        base_yield = float(row_data["base_yield_per_map"])

        if investment_tier not in ("low", "medium", "high"):
            logger.warning("Invalid investment_tier '%s' for %s — skipping", investment_tier, item_name)
            skipped += 1
            continue

        # Try to update existing drop
        cursor = await db.execute(
            """
            UPDATE drops SET base_yield_per_map = ?, ninja_type = ?
            WHERE mechanic_id = ? AND item_name = ? AND investment_tier = ?
            """,
            (base_yield, ninja_type, mechanic_id, item_name, investment_tier),
        )

        if cursor.rowcount > 0:
            updated += 1
        else:
            # Insert new drop
            await db.execute(
                """
                INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mechanic_id, item_name, ninja_type, base_yield, investment_tier),
            )
            inserted += 1

    await db.commit()
    logger.info(
        "Yield ingest for %s: %d updated, %d inserted, %d skipped",
        mechanic_name, updated, inserted, skipped,
    )
    return {"mechanic": mechanic_name, "updated": updated, "inserted": inserted, "skipped": skipped}


async def ingest_all_yields() -> list[dict]:
    """Scan data/yields/ and ingest all CSV/JSON files."""
    if not YIELDS_DIR.exists():
        logger.warning("Yields directory not found: %s", YIELDS_DIR)
        return []

    results = []
    for filepath in sorted(YIELDS_DIR.glob("*")):
        if filepath.suffix in (".csv", ".json"):
            try:
                result = await ingest_yield_file(filepath)
                results.append(result)
            except Exception as e:
                logger.error("Failed to ingest %s: %s", filepath.name, e)
                results.append({"file": filepath.name, "error": str(e)})

    return results
