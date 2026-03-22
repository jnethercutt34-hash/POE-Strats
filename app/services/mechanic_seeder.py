"""Parse mechanic markdown files and seed the mechanics + drops tables."""

import json
import logging
import re
from pathlib import Path

from app.database import get_db

logger = logging.getLogger(__name__)

MECHANICS_DIR = Path("data/mechanics")


def parse_mechanic_md(filepath: Path) -> dict:
    """Parse a mechanic markdown file into structured data.

    Expected format:
    - # Name (h1)
    - ## Metadata section with key-value bullet points
    - ## Drops section with a markdown table
    """
    text = filepath.read_text(encoding="utf-8")
    result = {
        "name": "",
        "patch_version": None,
        "scaling_tags": "[]",
        "is_scarab_heavy": False,
        "drops": [],
        "costs": [],
    }

    # Parse name from first h1
    name_match = re.search(r"^# (.+)$", text, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip()

    # Parse metadata section
    metadata_match = re.search(
        r"## Metadata\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    if metadata_match:
        meta_block = metadata_match.group(1)

        pv = re.search(r"\*\*Patch Version:\*\*\s*(.+)", meta_block)
        if pv:
            result["patch_version"] = pv.group(1).strip()

        st = re.search(r"\*\*Scaling Tags:\*\*\s*(\[.+?\])", meta_block)
        if st:
            result["scaling_tags"] = st.group(1).strip()

        sh = re.search(r"\*\*Is Scarab Heavy:\*\*\s*(\w+)", meta_block)
        if sh:
            result["is_scarab_heavy"] = sh.group(1).strip().lower() == "true"

    # Parse drops table
    drops_match = re.search(r"## Drops\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if drops_match:
        drops_block = drops_match.group(1)
        # Find table rows (skip header and separator)
        table_lines = [
            line.strip()
            for line in drops_block.split("\n")
            if line.strip().startswith("|") and not line.strip().startswith("|--")
        ]

        # Skip header row
        for line in table_lines[1:]:
            if line.startswith("|--") or "Item Name" in line:
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]  # strip outer pipes
            if len(cells) >= 4:
                result["drops"].append({
                    "item_name": cells[0],
                    "ninja_type": cells[1],
                    "investment_tier": cells[2].lower(),
                    "base_yield_per_map": float(cells[3]),
                })

    # Parse costs table
    costs_match = re.search(r"## Costs\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if costs_match:
        costs_block = costs_match.group(1)
        table_lines = [
            line.strip()
            for line in costs_block.split("\n")
            if line.strip().startswith("|") and not line.strip().startswith("|--")
        ]

        for line in table_lines[1:]:
            if line.startswith("|--") or "Cost Item" in line:
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 4:
                result["costs"].append({
                    "item_name": cells[0],
                    "ninja_type": cells[1],
                    "investment_tier": cells[2].lower(),
                    "quantity": float(cells[3]),
                })

    return result


async def seed_mechanics():
    """Scan data/mechanics/ for .md files and upsert into DB."""
    if not MECHANICS_DIR.exists():
        logger.warning("Mechanics directory not found: %s", MECHANICS_DIR)
        return {"seeded": 0, "errors": []}

    md_files = sorted(MECHANICS_DIR.glob("*.md"))
    if not md_files:
        logger.warning("No mechanic .md files found in %s", MECHANICS_DIR)
        return {"seeded": 0, "errors": []}

    db = await get_db()
    seeded = 0
    errors = []

    for filepath in md_files:
        try:
            data = parse_mechanic_md(filepath)
            if not data["name"]:
                errors.append(f"{filepath.name}: no name found")
                continue

            logger.info("Seeding mechanic: %s (%d drops)", data["name"], len(data["drops"]))

            # Upsert mechanic
            await db.execute(
                """
                INSERT INTO mechanics (name, patch_version, scaling_tags, is_scarab_heavy)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    patch_version = excluded.patch_version,
                    scaling_tags = excluded.scaling_tags,
                    is_scarab_heavy = excluded.is_scarab_heavy
                """,
                (
                    data["name"],
                    data["patch_version"],
                    data["scaling_tags"],
                    data["is_scarab_heavy"],
                ),
            )

            # Get the mechanic ID
            cursor = await db.execute(
                "SELECT id FROM mechanics WHERE name = ?", (data["name"],)
            )
            row = await cursor.fetchone()
            mechanic_id = row["id"]

            # Clear existing drops for this mechanic (full replace on re-seed)
            await db.execute("DELETE FROM drops WHERE mechanic_id = ?", (mechanic_id,))

            # Insert drops
            for drop in data["drops"]:
                await db.execute(
                    """
                    INSERT INTO drops (mechanic_id, item_name, ninja_type, base_yield_per_map, investment_tier)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        mechanic_id,
                        drop["item_name"],
                        drop["ninja_type"],
                        drop["base_yield_per_map"],
                        drop["investment_tier"],
                    ),
                )

            # Clear existing costs and re-insert
            await db.execute("DELETE FROM costs WHERE mechanic_id = ?", (mechanic_id,))
            for cost in data["costs"]:
                await db.execute(
                    """
                    INSERT INTO costs (mechanic_id, item_name, ninja_type, investment_tier, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        mechanic_id,
                        cost["item_name"],
                        cost["ninja_type"],
                        cost["investment_tier"],
                        cost["quantity"],
                    ),
                )

            await db.commit()
            seeded += 1
            logger.info("✓ %s: %d drops, %d costs inserted", data["name"], len(data["drops"]), len(data["costs"]))

        except Exception as e:
            errors.append(f"{filepath.name}: {e}")
            logger.error("Failed to seed %s: %s", filepath.name, e)

    return {"seeded": seeded, "errors": errors}
