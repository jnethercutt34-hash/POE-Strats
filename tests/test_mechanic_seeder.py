"""Tests for the mechanic markdown parser and seeder."""

import pytest
from pathlib import Path
from app.services.mechanic_seeder import parse_mechanic_md, seed_mechanics


SAMPLE_MD = """# TestMechanic

## Metadata
- **Patch Version:** 3.25
- **Scaling Tags:** ["fast", "quantity"]
- **Is Scarab Heavy:** true

## Overview
A test mechanic for unit tests.

## How to Run
1. Step one
2. Step two

## Drops

| Item Name | Ninja Type | Investment Tier | Base Yield Per Map |
|-----------|-----------|-----------------|-------------------|
| Test Fossil | Fossil | low | 2.0 |
| Test Fossil | Fossil | medium | 4.0 |
| Test Fossil | Fossil | high | 6.5 |

## Costs

| Cost Item | Ninja Type | Investment Tier | Quantity |
|-----------|-----------|-----------------|----------|
| Test Scarab | Scarab | high | 1 |
| Orb of Alchemy | Currency | low | 1 |
"""


def test_parse_name():
    """Parser extracts mechanic name from h1."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_MD)
        f.flush()
        result = parse_mechanic_md(Path(f.name))

    assert result["name"] == "TestMechanic"
    assert result["patch_version"] == "3.25"
    assert result["scaling_tags"] == '["fast", "quantity"]'
    assert result["is_scarab_heavy"] is True


def test_parse_drops():
    """Parser extracts drops table correctly."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_MD)
        f.flush()
        result = parse_mechanic_md(Path(f.name))

    assert len(result["drops"]) == 3
    assert result["drops"][0]["item_name"] == "Test Fossil"
    assert result["drops"][0]["ninja_type"] == "Fossil"
    assert result["drops"][0]["investment_tier"] == "low"
    assert result["drops"][0]["base_yield_per_map"] == 2.0
    assert result["drops"][2]["investment_tier"] == "high"
    assert result["drops"][2]["base_yield_per_map"] == 6.5


def test_parse_costs():
    """Parser extracts costs table correctly."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_MD)
        f.flush()
        result = parse_mechanic_md(Path(f.name))

    assert len(result["costs"]) == 2
    assert result["costs"][0]["item_name"] == "Test Scarab"
    assert result["costs"][0]["quantity"] == 1.0


def test_parse_empty_md():
    """Parser handles empty/minimal file gracefully."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Empty\n\n## Metadata\n- **Patch Version:** 3.25\n")
        f.flush()
        result = parse_mechanic_md(Path(f.name))

    assert result["name"] == "Empty"
    assert result["drops"] == []
    assert result["costs"] == []


@pytest.mark.asyncio
async def test_seed_mechanics_from_real_files(db):
    """seed_mechanics should load the actual data/mechanics/*.md files."""
    result = await seed_mechanics()
    assert result["seeded"] >= 6  # At least our original 6
    assert len(result["errors"]) == 0

    # Verify a known mechanic exists
    cursor = await db.execute("SELECT name FROM mechanics WHERE name = 'Delve'")
    row = await cursor.fetchone()
    assert row is not None

    # Verify drops were created
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM drops d
           JOIN mechanics m ON d.mechanic_id = m.id
           WHERE m.name = 'Delve'"""
    )
    row = await cursor.fetchone()
    assert row["cnt"] > 0
