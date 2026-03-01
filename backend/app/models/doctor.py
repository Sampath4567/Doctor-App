from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_doctors_user_id"),
        Index("ix_doctors_user_id", "user_id"),
        Index("ix_doctors_specialization_id", "specialization_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    specialization_id: Mapped[int] = mapped_column(
        ForeignKey("specializations.id"),
        nullable=False,
    )
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qualification: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consultation_fee_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="doctor_profile",
    )
    specialization: Mapped["Specialization"] = relationship(
        "Specialization",
        back_populates="doctors",
    )
    slots: Mapped[List["Slot"]] = relationship(
        "Slot",
        back_populates="doctor",
    )

