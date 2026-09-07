"""
backend/app/auth/middleware.py — Milestone 6.3

Demo-grade authentication and Role-Based Access Control (RBAC) middleware:
- Seeded admin and driver demo accounts
- Secure HMAC-SHA256 token issuance and validation
- Role verification dependencies (require_admin, require_driver, require_any_user)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = os.environ.get("JWT_SECRET", "abraxas_demo_super_secret_jwt_key_2026")

DEMO_ACCOUNTS: dict[str, dict[str, Any]] = {
    "admin": {
        "id": "admin",
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "name": "Fleet Dispatcher",
        "vehicle_label": None,
    },
    "driver1": {
        "id": "driver1",
        "username": "driver1",
        "password": "driver123",
        "role": "driver",
        "name": "Ramesh Pawar",
        "vehicle_label": "Van-1",
    },
    "driver2": {
        "id": "driver2",
        "username": "driver2",
        "password": "driver223",
        "role": "driver",
        "name": "Suresh Gaikwad",
        "vehicle_label": "Van-2",
    },
    "driver3": {
        "id": "driver3",
        "username": "driver3",
        "password": "driver323",
        "role": "driver",
        "name": "Amit Kulkarni",
        "vehicle_label": "Van-3",
    },
}

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict[str, Any], expires_delta_sec: int = 86400) -> str:
    """
    Create a signed HMAC-SHA256 token containing payload claims.
    """
    payload = data.copy()
    payload["exp"] = time.time() + expires_delta_sec

    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_json).decode("utf-8").rstrip("=")

    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    b64_sig = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    return f"{b64_payload}.{b64_sig}"


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify HMAC-SHA256 token signature and expiration.
    """
    parts = token.strip().split(".")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    b64_payload, b64_sig = parts
    # Pad base64 if needed
    rem_payload = len(b64_payload) % 4
    padded_payload = b64_payload + ("=" * (4 - rem_payload) if rem_payload else "")

    expected_sig = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    rem_sig = len(b64_sig) % 4
    padded_sig = b64_sig + ("=" * (4 - rem_sig) if rem_sig else "")

    try:
        actual_sig = base64.urlsafe_b64decode(padded_sig.encode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature encoding.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature mismatch.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload_bytes = base64.urlsafe_b64decode(padded_payload.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Corrupted token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    exp = payload.get("exp", 0)
    if time.time() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> dict[str, Any]:
    """Dependency to extract and validate the authenticated user from the Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decode_access_token(credentials.credentials)


def require_role(allowed_roles: list[str]) -> Callable:
    """Dependency factory to enforce role-based access control."""

    async def _role_checker(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        user_role = user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: role '{user_role}' lacks required permissions ({allowed_roles}).",
            )
        return user

    return _role_checker


require_admin = require_role(["admin"])
require_driver = require_role(["driver"])
require_any_user = require_role(["admin", "driver"])
