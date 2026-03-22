import os
from dotenv import load_dotenv

load_dotenv()

POE_LEAGUE = os.getenv("POE_LEAGUE", "Phrecia")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/poe_tracker.db")
NINJA_POLL_INTERVAL_MINUTES = int(os.getenv("NINJA_POLL_INTERVAL_MINUTES", "60"))

# poe.ninja API base URLs (updated to new poe1 endpoints)
NINJA_BASE_URL = "https://poe.ninja/poe1/api/economy/stash/current"
NINJA_ITEM_OVERVIEW = f"{NINJA_BASE_URL}/item/overview"
NINJA_CURRENCY_OVERVIEW = f"{NINJA_BASE_URL}/currency/overview"

# Item types to poll from poe.ninja
NINJA_ITEM_TYPES = [
    "DivinationCard", "Fossil", "Resonator", "Essence",
    "UniqueWeapon", "UniqueArmour", "UniqueAccessory",
    "UniqueFlask", "UniqueJewel", "SkillGem", "BaseType",
    "Artifact", "Oil", "Incubator", "Scarab", "Memory",
    "DeliriumOrb", "Invitation",
]
NINJA_CURRENCY_TYPES = [
    "Currency", "Fragment",
]
