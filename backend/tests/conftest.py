"""
backend/tests/conftest.py — Global test fixtures and configuration.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env if exists
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Set safe test defaults
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/logistics_test_db")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only_1234567890")
os.environ.setdefault("APP_ENV", "test")
