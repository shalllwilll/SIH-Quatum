import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

# Determine base directory and look for .env file
BASE_DIR = Path(__file__).resolve().parent.parent
env_file_path = BASE_DIR / ".env"

if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path)

# Verify required environment configuration
REQUIRED_ENV_VARS = ["MONGO_URI"]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(
        f"Configuration Error: Missing required environment variable(s): {', '.join(missing_vars)}. "
        f"Please create a .env file based on backend/.env.example or set the environment variables."
    )

app = FastAPI(
    title="Last-Mile Delivery Routing Engine API",
    description="Backend service for QGA + QPSO hybrid routing optimization platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "ok"}
