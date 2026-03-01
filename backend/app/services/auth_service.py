from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token as _create_access_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole


def register_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.PATIENT,
    phone: Optional[str] = None,
) -> User:
    existing = (
        db.query(User)
        .filter((User.email == email) | (User.username == username))
        .first()
    )
    if existing:
        raise ValueError("User with this email or username already exists")

    user = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        phone=phone,
    )
    db.add(user)
    db.flush()
    return user


def authenticate_user(
    db: Session,
    *,
    username_or_email: str,
    password: str,
) -> Optional[User]:
    q = db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    )
    user = q.first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def create_access_token(user_id: int) -> str:
    """
    Convenience wrapper around the core JWT helper so that higher layers
    don't need to know about the subject semantics.
    """

    return _create_access_token(subject=user_id)


def create_refresh_token(
    db: Session,
    *,
    user: User,
    expires_in_days: int = 7,
) -> RefreshToken:
    """
    Create and persist a new refresh token for the given user.
    """

    from secrets import token_urlsafe

    token_value = token_urlsafe(48)
    now = datetime.now(timezone.utc)
    token = RefreshToken(
        user_id=user.id,
        token=token_value,
        expires_at=now + timedelta(days=expires_in_days),
        revoked=False,
    )
    db.add(token)
    db.flush()
    return token


def rotate_refresh_token(
    db: Session,
    *,
    old_token: RefreshToken,
    expires_in_days: int = 7,
) -> RefreshToken:
    """
    Revoke the provided refresh token and create a new one for the same user.
    """

    if old_token.revoked:
        raise ValueError("Refresh token already revoked")

    old_token.revoked = True
    return create_refresh_token(db, user=old_token.user, expires_in_days=expires_in_days)


def revoke_refresh_token(db: Session, *, token: RefreshToken) -> None:
    """
    Mark the given refresh token as revoked.
    """

    if not token.revoked:
        token.revoked = True
        db.add(token)

