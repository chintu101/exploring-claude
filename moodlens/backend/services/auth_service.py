"""
services/auth_service.py
────────────────────────
Authentication helpers.

Responsibilities
────────────────
• Password hashing / verification (bcrypt via passlib)
• JWT creation and decoding (python-jose)
• FastAPI dependency that extracts the current user from the
  Authorization header on protected endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from moodlens.backend.config import settings
from moodlens.backend.database import get_db
from moodlens.backend.models import User

# ── Password hashing ───────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Bearer token extractor ─────────────────────────────────────────────────
_bearer_scheme = HTTPBearer()


class AuthService:
    """
    Stateless utility class for authentication operations.

    All methods are static/class-level; no instance state is held.
    """

    # ── Password helpers ───────────────────────────────────────────────────

    @staticmethod
    def hash_password(plain: str) -> str:
        """Return bcrypt hash of *plain* text password."""
        return _pwd_context.hash(plain)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Return True if *plain* matches *hashed*."""
        return _pwd_context.verify(plain, hashed)

    # ── JWT helpers ────────────────────────────────────────────────────────

    @staticmethod
    def create_access_token(user_id: int, email: str) -> str:
        """
        Create a signed JWT containing the user's id and email.

        The token expires after ``settings.access_token_expire_minutes``.
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate a JWT.

        Raises
        ──────
        HTTPException 401 if the token is invalid or expired.
        """
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc


# ── FastAPI dependency ─────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: decode the Bearer token and return the active User.

    Usage
    ─────
    ```python
    @router.get("/me")
    async def me(user: User = Depends(get_current_user)):
        ...
    ```

    Raises
    ──────
    401 – missing / invalid token
    403 – account is inactive
    404 – user not found in DB (token is valid but user was deleted)
    """
    payload = AuthService.decode_token(credentials.credentials)
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token")

    result = await db.execute(select(User).options(selectinload(User.streak)).where(User.id == int(user_id)))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return user