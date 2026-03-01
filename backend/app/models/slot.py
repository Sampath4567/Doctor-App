from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint("doctor_id", "start_time", name="uq_slots_doctor_start_time"),
        Index("ix_slots_doctor_id", "doctor_id"),
        Index("ix_slots_start_time", "start_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_booked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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

    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="slots",
    )
    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        back_populates="slot",
        uselist=False,
    )

