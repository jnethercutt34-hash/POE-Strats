"""Tests for the profitability engine."""

import pytest
from app.services.profit_engine import calculate_profit, calculate_all_profits


@pytest.mark.asyncio
async def test_calculate_profit_returns_none_for_unknown(db):
    """Unknown mechanic should return None."""
    result = await calculate_profit("NonExistentMechanic")
    assert result is None


@pytest.mark.asyncio
async def test_calculate_profit_basic(seeded_db):
    """Basic profit calculation with known data."""
    result = await calculate_profit("TestMech", investment_tier="medium", maps_per_hour=10)

    assert result is not None
    assert result["mechanic"] == "TestMech"
    assert result["investment_tier"] == "medium"

    # Revenue: Chaos Orb (5.0 * 1.0 = 5.0) + Exalted Orb (0.1 * 15.0 = 1.5) = 6.5
    assert result["total_revenue_chaos"] == 6.5

    # Costs: base_map (2.0) + Scarab of Testing (1 * 10.0 = 10.0) = 12.0
    assert result["total_cost_chaos"] == 12.0

    # Profit per map: 6.5 - 12.0 = -5.5
    assert result["profit_per_map"] == -5.5

    # Profit per hour: -5.5 * 10 = -55.0
    assert result["profit_per_hour"] == -55.0

    # Revenue breakdown should be sorted descending
    assert len(result["revenue_breakdown"]) == 2
    assert result["revenue_breakdown"][0]["item_name"] == "Chaos Orb"


@pytest.mark.asyncio
async def test_calculate_profit_missing_prices(db):
    """Mechanic with drops but no economy data should report missing prices."""
    await db.execute(
        """INSERT INTO mechanics (name, patch_version, scaling_tags, is_scarab_heavy)
           VALUES ('EmptyMech', '3.25', '[]', 0)"""
    )
    cursor = await db.execute("SELECT id FROM mechanics WHERE name = 'EmptyMech'")
    mech_id = (await cursor.fetchone())["id"]
    await db.execute(
        """INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
           VALUES (?, 'Unknown Item', 'Currency', 10.0, 'medium')""",
        (mech_id,),
    )
    await db.commit()

    result = await calculate_profit("EmptyMech")
    assert result is not None
    assert "Unknown Item" in result["missing_prices"]
    assert result["total_revenue_chaos"] == 0.0


@pytest.mark.asyncio
async def test_calculate_all_profits(seeded_db):
    """calculate_all_profits should return a list with meta tiers."""
    results = await calculate_all_profits(investment_tier="medium", maps_per_hour=10)
    assert len(results) >= 1
    assert all("meta_tier" in r for r in results)
    # With only 1 mechanic, it should be S tier
    assert results[0]["meta_tier"] == "S"


@pytest.mark.asyncio
async def test_meta_tier_distribution(db):
    """With multiple mechanics, tiers should distribute S/A/B/C correctly."""
    # Create 10 mechanics with varying profit
    for i in range(10):
        name = f"Mech{i}"
        await db.execute(
            """INSERT INTO mechanics (name, patch_version, scaling_tags, is_scarab_heavy)
               VALUES (?, '3.25', '[]', 0)""",
            (name,),
        )
        cursor = await db.execute("SELECT id FROM mechanics WHERE name = ?", (name,))
        mech_id = (await cursor.fetchone())["id"]

        # Each mechanic has 1 drop with increasing yield -> different profit
        await db.execute(
            """INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
               VALUES (?, 'Chaos Orb', 'Currency', ?, 'medium')""",
            (mech_id, float(i + 1) * 10),
        )

    # Add economy price for Chaos Orb
    await db.execute(
        """INSERT INTO economy_snapshot (ninja_id, item_name, ninja_type, chaos_value, timestamp)
           VALUES (1, 'Chaos Orb', 'Currency', 1.0, '2026-03-22T12:00:00')"""
    )
    await db.commit()

    results = await calculate_all_profits(investment_tier="medium")
    assert len(results) == 10
    tiers = [r["meta_tier"] for r in results]
    assert "S" in tiers
    assert "C" in tiers
