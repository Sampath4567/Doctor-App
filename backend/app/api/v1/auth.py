from __future__ import annotations

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_current_user, get_valid_refresh_token
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.services.auth_service import (
    authenticate_user,
    create_refresh_token,
    register_user,
    rotate_refresh_token,
    revoke_refresh_token,
)


router = APIRouter(tags=["auth"])


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.PATIENT


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/auth/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db_session),
):
    try:
        user = register_user(
            db,
            email=payload.email,
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            phone=payload.phone,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    access_token = create_access_token(user.id)
    refresh = create_refresh_token(db, user=user)
    db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh.token,
    )


@router.post("/auth/login", response_model=TokenPair)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db_session),
):
    user = authenticate_user(
        db,
        username_or_email=payload.username_or_email,
        password=payload.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )

    access_token = create_access_token(user.id)
    refresh = create_refresh_token(db, user=user)
    db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh.token,
    )


@router.post("/auth/refresh", response_model=TokenPair)
def refresh_tokens(
    payload: RefreshRequest,
    db: Session = Depends(get_db_session),
):
    token = get_valid_refresh_token(payload.refresh_token, db)
    user: User = token.user

    new_refresh = rotate_refresh_token(db, old_token=token)
    access_token = create_access_token(user.id)
    db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh.token,
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    token = get_valid_refresh_token(payload.refresh_token, db)
    if token.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke token belonging to another user",
        )

    revoke_refresh_token(db, token=token)
    db.commit()
    return None

