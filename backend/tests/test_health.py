"""
Test suite for the GET /health endpoint.

Milestone 0.2 — CI Sanity & Code Quality Baseline
"""

import os

from fastapi.testclient import TestClient

# Ensure MONGO_URI is set before importing the app module, so the startup
# environment validation in main.py does not raise during test collection.
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/test_db")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_returns_200():
    """GET /health must respond with HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body():
    """GET /health must return exactly {"status": "ok"}."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_health_content_type():
    """GET /health must return JSON content."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
