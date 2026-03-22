"""POE MetaTracker & Profit Engine — FastAPI entry point."""

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import NINJA_POLL_INTERVAL_MINUTES, POE_LEAGUE
from app.database import close_db, init_db
from app.routers import economy, mechanics, profit
from app.services.data_retention import run_retention
from app.services.mechanic_seeder import seed_mechanics
from app.services.ninja_poller import poll_ninja

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, schedule poller. Shutdown: cleanup."""
    logger.info("Starting POE MetaTracker — League: %s", POE_LEAGUE)

    # Init database
    await init_db()
    logger.info("Database initialized")

    # Schedule the ninja poller
    scheduler.add_job(
        poll_ninja,
        "interval",
        minutes=NINJA_POLL_INTERVAL_MINUTES,
        id="ninja_poller",
        name="poe.ninja Economy Poller",
    )
    # Schedule daily retention job (runs at midnight)
    scheduler.add_job(
        run_retention,
        "cron",
        hour=0,
        minute=0,
        id="data_retention",
        name="Economy Data Retention",
    )

    scheduler.start()
    logger.info("Scheduler started — polling every %d minutes, retention daily at midnight", NINJA_POLL_INTERVAL_MINUTES)

    # Seed mechanic data from markdown files
    seed_result = await seed_mechanics()
    logger.info("Mechanic seeding: %d seeded, %d errors", seed_result["seeded"], len(seed_result["errors"]))

    # Skip initial poll on startup — use POST /api/economy/poll to trigger manually
    logger.info("Server ready. Use POST /api/economy/poll to trigger initial data fetch.")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="POE MetaTracker",
    description="Real-time PoE economy tracking and mechanic profitability engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(economy.router)
app.include_router(mechanics.router)
app.include_router(profit.router)


@app.get("/")
async def root():
    return {
        "app": "POE MetaTracker",
        "league": POE_LEAGUE,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    from app.database import get_db
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) as count FROM economy_snapshot")
    row = await cursor.fetchone()
    return {
        "status": "ok",
        "league": POE_LEAGUE,
        "economy_snapshots": row["count"],
    }
