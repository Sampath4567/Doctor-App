from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AppointmentStatus(str, enum.Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("slot_id", name="uq_appointments_slot_id"),
        Index("ix_appointments_slot_id", "slot_id"),
        Index("ix_appointments_patient_id", "patient_id"),
        CheckConstraint(
            "status in ('booked', 'cancelled', 'completed')",
            name="ck_appointments_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.id"),
        nullable=False,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        SqlEnum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.BOOKED,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    slot: Mapped["Slot"] = relationship(
        "Slot",
        back_populates="appointment",
    )
    patient: Mapped["User"] = relationship(
        "User",
        back_populates="appointments",
    )

