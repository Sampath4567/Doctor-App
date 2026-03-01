from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.slot import Slot
from app.repositories.appointment_repository import appointment_repository
from app.repositories.slot_repository import slot_repository


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class BookingError(Exception):
    """Base class for booking-related domain errors."""


class SlotNotFoundError(BookingError):
    pass


class SlotAlreadyBookedError(BookingError):
    pass


class AppointmentNotFoundError(BookingError):
    pass


class PermissionDeniedError(BookingError):
    pass


class InvalidAppointmentStateError(BookingError):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Service layer
# ──────────────────────────────────────────────────────────────────────────────


def book_slot(
    db: Session,
    *,
    patient_id: int,
    slot_id: int,
) -> Appointment:
    """
    Attempt to book a slot for a patient.

    - Locks the slot row with SELECT ... FOR UPDATE.
    - Ensures the slot is not already booked.
    - Creates a new Appointment in BOOKED state.
    - Marks the slot as booked.

    This function is transaction-safe when called with a Session whose
    lifetime is bound to the request. The internal `db.begin()` ensures that
    all operations are committed atomically or rolled back on error.
    """

    with db.begin():
        slot: Slot | None = slot_repository.get_for_update(db, slot_id)
        if slot is None:
            raise SlotNotFoundError(f"Slot {slot_id} does not exist")

        if slot.is_booked:
            raise SlotAlreadyBookedError(f"Slot {slot_id} is already booked")

        appointment = Appointment(
            slot_id=slot.id,
            patient_id=patient_id,
            status=AppointmentStatus.BOOKED,
        )

        slot.is_booked = True
        db.add(appointment)
        db.flush()

        return appointment


def cancel_appointment(
    db: Session,
    *,
    patient_id: int,
    appointment_id: int,
) -> Appointment:
    """
    Cancel an appointment on behalf of a patient.

    - Locks both the appointment and its slot (via SELECT ... FOR UPDATE).
    - Ensures the appointment belongs to the given patient.
    - Allows cancellation only from BOOKED state.
    - Transitions status to CANCELLED and frees the slot.
    """

    with db.begin():
        appt = appointment_repository.get_with_slot_for_update(db, appointment_id)
        if appt is None:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appt.patient_id != patient_id:
            raise PermissionDeniedError("Patient does not own this appointment")

        if appt.status is not AppointmentStatus.BOOKED:
            raise InvalidAppointmentStateError(
                f"Cannot cancel appointment in state {appt.status}"
            )

        appt.status = AppointmentStatus.CANCELLED
        if appt.slot is not None:
            appt.slot.is_booked = False

        db.flush()
        return appt


def complete_appointment(
    db: Session,
    *,
    doctor_id: int,
    appointment_id: int,
) -> Appointment:
    """
    Mark an appointment as completed on behalf of a doctor.

    - Locks both the appointment and its slot.
    - Ensures the appointment is associated with the given doctor.
    - Allows completion only from BOOKED state.
    - Transitions status to COMPLETED. Slot remains booked but can be
      interpreted as consumed.
    """

    with db.begin():
        appt = appointment_repository.get_with_slot_for_update(db, appointment_id)
        if appt is None:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")

        if appt.slot is None or appt.slot.doctor_id != doctor_id:
            raise PermissionDeniedError("Doctor does not own this appointment")

        if appt.status is not AppointmentStatus.BOOKED:
            raise InvalidAppointmentStateError(
                f"Cannot complete appointment in state {appt.status}"
            )

        appt.status = AppointmentStatus.COMPLETED
        db.flush()
        return appt

