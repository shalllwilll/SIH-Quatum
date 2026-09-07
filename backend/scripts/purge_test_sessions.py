"""
backend/scripts/purge_test_sessions.py — Milestone 4.3

Developer maintenance script: purges test routing sessions from MongoDB
to keep dev database clean between integration runs.

Usage:
    backend/.venv/bin/python -m backend.scripts.purge_test_sessions
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path if running as script
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.db import get_db  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


async def purge_sessions():
    db = get_db()
    res = await db.routing_sessions.delete_many({"seeded": False})
    log.info("Purged %d non-seeded routing sessions.", res.deleted_count)


if __name__ == "__main__":
    asyncio.run(purge_sessions())
