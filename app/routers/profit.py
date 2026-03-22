"""Profitability endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.services.profit_engine import calculate_all_profits, calculate_profit

router = APIRouter(prefix="/api/profit", tags=["profit"])


@router.get("/")
async def profit_overview(
    investment: str = Query("medium", regex="^(low|medium|high)$"),
    maps_per_hour: float = Query(12.0, gt=0, le=60),
):
    """Get profitability ranking for all mechanics."""
    results = await calculate_all_profits(investment, maps_per_hour)
    return {
        "investment_tier": investment,
        "maps_per_hour": maps_per_hour,
        "count": len(results),
        "mechanics": results,
    }


@router.get("/{mechanic_name}")
async def mechanic_profit(
    mechanic_name: str,
    investment: str = Query("medium", regex="^(low|medium|high)$"),
    maps_per_hour: float = Query(12.0, gt=0, le=60),
):
    """Get detailed profitability breakdown for a specific mechanic."""
    result = await calculate_profit(mechanic_name, investment, maps_per_hour)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Mechanic '{mechanic_name}' not found")
    return result
