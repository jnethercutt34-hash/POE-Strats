"""Profitability engine — calculates real-time profit per mechanic.

Joins drop yields × live economy prices, subtracts dynamic costs.
"""

import logging
from typing import Optional

from app.database import get_db

logger = logging.getLogger(__name__)

DEFAULT_MAPS_PER_HOUR = 12
BASE_MAP_COST_CHAOS = 2.0  # Approximate cost of a map + alch (not looked up)


async def calculate_profit(
    mechanic_name: str,
    investment_tier: str = "medium",
    maps_per_hour: float = DEFAULT_MAPS_PER_HOUR,
) -> Optional[dict]:
    """Calculate profitability for a mechanic at a given investment tier.
    
    Returns a dict with revenue, costs, profit, breakdown, or None if mechanic not found.
    """
    db = await get_db()

    # 1. Find the mechanic
    cursor = await db.execute(
        "SELECT id, name, meta_tier, scaling_tags FROM mechanics WHERE LOWER(name) = LOWER(?)",
        (mechanic_name,),
    )
    mechanic = await cursor.fetchone()
    if mechanic is None:
        return None

    mechanic_id = mechanic["id"]

    # 2. Get drops for this mechanic at the specified investment tier
    cursor = await db.execute(
        """
        SELECT item_name, ninja_type, base_yield_per_map
        FROM drops
        WHERE mechanic_id = ? AND investment_tier = ?
        """,
        (mechanic_id, investment_tier),
    )
    drops = await cursor.fetchall()

    # 3. Look up latest prices for each drop item
    revenue_breakdown = []
    missing_prices = []
    total_revenue = 0.0

    for drop in drops:
        item_name = drop["item_name"]
        base_yield = drop["base_yield_per_map"]

        # Get the most recent price for this item
        price_cursor = await db.execute(
            """
            SELECT chaos_value FROM economy_snapshot
            WHERE item_name = ? AND ninja_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (item_name, drop["ninja_type"]),
        )
        price_row = await price_cursor.fetchone()

        if price_row is None or price_row["chaos_value"] is None:
            missing_prices.append(item_name)
            continue

        chaos_value = price_row["chaos_value"]
        item_revenue = base_yield * chaos_value
        total_revenue += item_revenue

        revenue_breakdown.append({
            "item_name": item_name,
            "yield_per_map": base_yield,
            "chaos_value": round(chaos_value, 2),
            "revenue_per_map": round(item_revenue, 2),
        })

    # Sort breakdown by revenue descending
    revenue_breakdown.sort(key=lambda x: x["revenue_per_map"], reverse=True)

    # 4. Calculate dynamic costs
    cursor = await db.execute(
        """
        SELECT item_name, ninja_type, quantity
        FROM costs
        WHERE mechanic_id = ? AND investment_tier = ?
        """,
        (mechanic_id, investment_tier),
    )
    cost_items = await cursor.fetchall()

    cost_breakdown = []
    total_cost = BASE_MAP_COST_CHAOS  # Start with base map cost
    cost_breakdown.append({
        "item_name": "Base Map Cost",
        "quantity": 1,
        "chaos_value": BASE_MAP_COST_CHAOS,
        "total_cost": BASE_MAP_COST_CHAOS,
        "source": "fixed",
    })

    for cost in cost_items:
        item_name = cost["item_name"]
        quantity = cost["quantity"]

        # Look up live price
        price_cursor = await db.execute(
            """
            SELECT chaos_value FROM economy_snapshot
            WHERE item_name = ? AND ninja_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (item_name, cost["ninja_type"]),
        )
        price_row = await price_cursor.fetchone()

        if price_row is None or price_row["chaos_value"] is None:
            # Use 0 if we can't find the price — flag it
            cost_breakdown.append({
                "item_name": item_name,
                "quantity": quantity,
                "chaos_value": 0,
                "total_cost": 0,
                "source": "missing",
            })
            missing_prices.append(f"(cost) {item_name}")
            continue

        chaos_value = price_row["chaos_value"]
        item_cost = quantity * chaos_value
        total_cost += item_cost

        cost_breakdown.append({
            "item_name": item_name,
            "quantity": quantity,
            "chaos_value": round(chaos_value, 2),
            "total_cost": round(item_cost, 2),
            "source": "live",
        })

    # 5. Calculate final numbers
    profit_per_map = total_revenue - total_cost
    profit_per_hour = profit_per_map * maps_per_hour

    return {
        "mechanic": mechanic["name"],
        "investment_tier": investment_tier,
        "maps_per_hour": maps_per_hour,
        "total_revenue_chaos": round(total_revenue, 2),
        "total_cost_chaos": round(total_cost, 2),
        "profit_per_map": round(profit_per_map, 2),
        "profit_per_hour": round(profit_per_hour, 2),
        "meta_tier": mechanic["meta_tier"],
        "revenue_breakdown": revenue_breakdown,
        "cost_breakdown": cost_breakdown,
        "missing_prices": missing_prices,
    }


async def calculate_all_profits(
    investment_tier: str = "medium",
    maps_per_hour: float = DEFAULT_MAPS_PER_HOUR,
) -> list[dict]:
    """Calculate profit for ALL mechanics and return sorted by profit/hour.
    
    Used for meta tier ranking and the overview dashboard.
    """
    db = await get_db()
    cursor = await db.execute("SELECT name FROM mechanics ORDER BY name")
    mechanics = await cursor.fetchall()

    results = []
    for mech in mechanics:
        profit = await calculate_profit(mech["name"], investment_tier, maps_per_hour)
        if profit:
            results.append({
                "mechanic": profit["mechanic"],
                "investment_tier": profit["investment_tier"],
                "profit_per_map": profit["profit_per_map"],
                "profit_per_hour": profit["profit_per_hour"],
                "total_revenue_chaos": profit["total_revenue_chaos"],
                "total_cost_chaos": profit["total_cost_chaos"],
                "missing_prices": len(profit["missing_prices"]),
            })

    # Sort by profit per hour descending
    results.sort(key=lambda x: x["profit_per_hour"], reverse=True)

    # Assign meta tiers based on ranking
    n = len(results)
    for i, r in enumerate(results):
        if n <= 1:
            r["meta_tier"] = "S"
        elif i < n * 0.1:
            r["meta_tier"] = "S"
        elif i < n * 0.25:
            r["meta_tier"] = "A"
        elif i < n * 0.5:
            r["meta_tier"] = "B"
        else:
            r["meta_tier"] = "C"

    # Persist meta tiers to the database
    for r in results:
        await db.execute(
            "UPDATE mechanics SET meta_tier = ? WHERE LOWER(name) = LOWER(?)",
            (r["meta_tier"], r["mechanic"]),
        )
    await db.commit()
    logger.info("Meta tiers updated: %s", {r["mechanic"]: r["meta_tier"] for r in results})

    return results
