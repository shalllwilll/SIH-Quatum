import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Determine base directory and look for .env file
BASE_DIR = Path(__file__).resolve().parent.parent
env_file_path = BASE_DIR / ".env"

if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path)

# Verify required environment configuration before importing DB-dependent modules
REQUIRED_ENV_VARS = ["MONGO_URI"]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(
        f"Configuration Error: Missing required environment variable(s): {', '.join(missing_vars)}. "
        f"Please create a .env file based on backend/.env.example or set the environment variables."
    )

# DB import deferred until after env validation above
from app.db import apply_collection_validators, ping_db  # noqa: E402


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    FastAPI lifespan handler.

    On startup:
      - Verifies MongoDB connectivity (fails fast with a clear error if unreachable).
      - Applies $jsonSchema validators to all 5 core collections (idempotent).

    On shutdown:
      - No action required (Motor client manages its own connection pool lifecycle).
    """
    try:
        await ping_db()
    except RuntimeError as exc:
        # Re-raise so uvicorn surfaces the error clearly at startup
        raise RuntimeError(
            f"Startup aborted — MongoDB unreachable: {exc}"
        ) from exc

    await apply_collection_validators()
    yield
    # Shutdown: nothing to clean up; Motor handles connection pool closure


app = FastAPI(
    title="Last-Mile Delivery Routing Engine API",
    description="Backend service for QGA + QPSO hybrid routing optimization platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "ok"}


@app.get("/health/db")
async def health_db():
    """
    Database connectivity health check.

    Returns {"status": "ok", "db": "connected"} on success.
    Returns 503 with an error detail on MongoDB connectivity failure.
    """
    from fastapi import HTTPException

    try:
        await ping_db()
        return {"status": "ok", "db": "connected"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
