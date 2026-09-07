"""
backend/app/routers/auth.py — Milestone 6.3

Demo authentication endpoints:
- POST /auth/login (authenticate admin/driver)
- GET /auth/me (return current authenticated profile)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.middleware import DEMO_ACCOUNTS, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """User credentials payload."""

    username: str = Field(..., min_length=1, description="Username (e.g. 'admin', 'driver1')")
    password: str = Field(..., min_length=1, description="Password")


class UserProfile(BaseModel):
    """Authenticated user profile representation."""

    id: str
    username: str
    role: str
    name: str
    vehicle_label: str | None = None


class LoginResponse(BaseModel):
    """Login response with access token and user metadata."""

    access_token: str
    token_type: str = "bearer"
    user: UserProfile


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Authenticate admin or driver with demo credentials."""
    account = DEMO_ACCOUNTS.get(req.username.strip().lower())
    if not account or account["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": account["id"],
        "username": account["username"],
        "role": account["role"],
        "name": account["name"],
        "vehicle_label": account["vehicle_label"],
    }
    token = create_access_token(token_data)

    user_profile = UserProfile(
        id=account["id"],
        username=account["username"],
        role=account["role"],
        name=account["name"],
        vehicle_label=account["vehicle_label"],
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_profile,
    )


@router.get("/me", response_model=UserProfile)
async def get_current_profile(current_user: Annotated[dict[str, Any], Depends(get_current_user)]):
    """Return authenticated profile information from token."""
    return UserProfile(
        id=current_user.get("sub", current_user.get("id", "UNKNOWN")),
        username=current_user.get("username", "UNKNOWN"),
        role=current_user.get("role", "driver"),
        name=current_user.get("name", "Unknown User"),
        vehicle_label=current_user.get("vehicle_label"),
    )
