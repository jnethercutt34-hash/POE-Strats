"""Tests for the yield ingestor service."""

import pytest
import tempfile
from pathlib import Path

from app.services.yield_ingestor import (
    _mechanic_name_from_filename,
    _load_csv,
    ingest_yield_file,
)


def test_mechanic_name_from_filename():
    """Filename -> mechanic name extraction."""
    assert _mechanic_name_from_filename(Path("delve_yields.csv")) == "Delve"
    assert _mechanic_name_from_filename(Path("harvest_yields.json")) == "Harvest"


def test_load_csv_valid():
    """Valid CSV should parse correctly."""
    csv_content = "item_name,ninja_type,investment_tier,base_yield_per_map\nTest Item,Currency,medium,5.0\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        f.flush()
        df = _load_csv(Path(f.name))

    assert len(df) == 1
    assert df.iloc[0]["item_name"] == "Test Item"
    assert df.iloc[0]["base_yield_per_map"] == 5.0


def test_load_csv_missing_columns():
    """CSV missing required columns should raise ValueError."""
    csv_content = "item_name,ninja_type\nTest,Currency\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        f.flush()
        with pytest.raises(ValueError, match="Missing columns"):
            _load_csv(Path(f.name))


@pytest.mark.asyncio
async def test_ingest_yield_file_unknown_mechanic(db):
    """Ingesting yields for a mechanic not in DB should skip gracefully."""
    csv_content = "item_name,ninja_type,investment_tier,base_yield_per_map\nTest,Currency,medium,5.0\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, prefix="unknown_yields", encoding="utf-8") as f:
        f.write(csv_content)
        f.flush()
        result = await ingest_yield_file(Path(f.name))

    assert result["skipped"] == 1 or "error" in result


@pytest.mark.asyncio
async def test_ingest_yield_file_updates_existing(db):
    """Ingest should update existing drops and insert new ones."""
    # Seed a mechanic
    await db.execute(
        """INSERT INTO mechanics (name, patch_version, scaling_tags, is_scarab_heavy)
           VALUES ('Delve', '3.25', '[]', 0)"""
    )
    cursor = await db.execute("SELECT id FROM mechanics WHERE name = 'Delve'")
    mech_id = (await cursor.fetchone())["id"]

    # Insert an existing drop
    await db.execute(
        """INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
           VALUES (?, 'Pristine Fossil', 'Fossil', 2.0, 'medium')""",
        (mech_id,),
    )
    await db.commit()

    # Create a yield CSV with a known filename (not random tempfile prefix)
    import os
    tmp_dir = tempfile.mkdtemp()
    csv_path = Path(tmp_dir) / "delve_yields.csv"
    csv_content = "item_name,ninja_type,investment_tier,base_yield_per_map\nPristine Fossil,Fossil,medium,9.9\nNew Fossil,Fossil,medium,3.0\n"
    csv_path.write_text(csv_content, encoding="utf-8")

    result = await ingest_yield_file(csv_path)

    assert result["updated"] == 1
    assert result["inserted"] == 1

    # Verify the update took effect
    cursor = await db.execute(
        "SELECT base_yield_per_map FROM drops WHERE item_name = 'Pristine Fossil' AND investment_tier = 'medium'"
    )
    row = await cursor.fetchone()
    assert row["base_yield_per_map"] == 9.9
