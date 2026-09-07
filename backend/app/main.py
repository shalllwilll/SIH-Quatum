"""
backend/app/main.py — FastAPI Application Entrypoint

Configures:
- Lifespan management (MongoDB connectivity check and $jsonSchema application)
- CORS locked to known frontend origins (admin: 5173, driver: 5174)
- Consistent error response formatting ({"error": "...", "detail": "..."})
- Core REST API routers: Auth, Warehouses, Parcels, Vehicles, Routing Sessions, Delivery Events, Driver
"""

from __future__ import annotations

import http
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from app.routers import (  # noqa: E402
    analytics_router,
    auth_router,
    delivery_events_router,
    driver_router,
    parcels_router,
    routing_sessions_router,
    vehicles_router,
    warehouses_router,
    websocket_router,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    FastAPI lifespan handler.

    On startup:
      - Verifies MongoDB connectivity (fails fast with a clear error if unreachable).
      - Applies $jsonSchema validators to all 5 core collections (idempotent).

    On shutdown:
      - Motor handles connection pool closure.
    """
    try:
        await ping_db()
    except RuntimeError as exc:
        raise RuntimeError(
            f"Startup aborted — MongoDB unreachable: {exc}"
        ) from exc

    await apply_collection_validators()
    yield


app = FastAPI(
    title="Last-Mile Delivery Routing Engine API",
    description="Backend service for QGA + QPSO hybrid routing optimization platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration locked to known frontend origins (spec §10)
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Consistent error response formatting
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTP exceptions into consistent error response shape."""
    status_phrase = (
        http.HTTPStatus(exc.status_code).phrase
        if exc.status_code in http.HTTPStatus._value2member_map_
        else "HTTP Error"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": status_phrase, "detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors into consistent error response shape."""
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": jsonable_encoder(exc.errors())},
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"])
async def health_db():
    """Database connectivity health check."""
    try:
        await ping_db()
        return {"status": "ok", "db": "connected"}
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


# Registered Routers
app.include_router(auth_router)
app.include_router(warehouses_router)
app.include_router(parcels_router)
app.include_router(vehicles_router)
app.include_router(routing_sessions_router)
app.include_router(delivery_events_router)
app.include_router(driver_router)
app.include_router(analytics_router)
app.include_router(websocket_router)
