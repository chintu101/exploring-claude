"""
routes/auth.py
──────────────
Authentication endpoints.

Endpoints
─────────
POST /auth/register  – Create a new user account
POST /auth/login     – Authenticate and return JWT
GET  /auth/me        – Return the current user's profile
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from moodlens.backend.database import get_db
from moodlens.backend.models import User
from moodlens.backend.schemas import Token, UserLogin, UserOut, UserRegister
from moodlens.backend.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Create a new MoodLens account.

    - Validates email uniqueness
    - Hashes the password with bcrypt
    - Returns a JWT so the user is immediately logged in

    Raises
    ──────
    409 – Email already registered
    """
    # Check uniqueness
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=AuthService.hash_password(payload.password),
    )
    db.add(user)
    await db.flush()  # Populate user.id without full commit

    token = AuthService.create_access_token(user.id, user.email)
    return Token(access_token=token)


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT",
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """
    Authenticate with email + password.

    Returns a signed JWT valid for 24 hours.

    Raises
    ──────
    401 – Invalid credentials
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user: User | None = result.scalar_one_or_none()

    if not user or not AuthService.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support.",
        )

    return Token(access_token=AuthService.create_access_token(user.id, user.email))


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the authenticated user's public profile."""
    return UserOut.model_validate(current_user)
