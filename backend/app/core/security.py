from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Access tokens are short-lived (default 15 minutes) and are intended to be
    presented on every authenticated API request.
    """

    if expires_delta is None:
        expires_delta = timedelta(minutes=15)

    now = datetime.now(timezone.utc)
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT and return its payload.

    Any validation errors (signature, expiry, etc.) should be handled by the
    caller.
    """

    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

