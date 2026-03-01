from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.slot import Slot


class AppointmentRepository:
    """
    Data access helpers for Appointment entities.
    """

    def get_for_update(self, db: Session, appointment_id: int) -> Optional[Appointment]:
        """
        Load an appointment row and acquire a row-level lock on it.
        """

        return (
            db.query(Appointment)
            .with_for_update()
            .filter(Appointment.id == appointment_id)
            .one_or_none()
        )

    def get_with_slot_for_update(
        self,
        db: Session,
        appointment_id: int,
    ) -> Optional[Appointment]:
        """
        Load an appointment together with its slot, locking both.

        SELECT ... FOR UPDATE applied on a join will lock all selected rows
        (appointment and slot), ensuring safe concurrent updates.
        """

        return (
            db.query(Appointment)
            .join(Slot, Appointment.slot_id == Slot.id)
            .with_for_update()
            .filter(Appointment.id == appointment_id)
            .one_or_none()
        )


appointment_repository = AppointmentRepository()

