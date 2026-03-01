from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

import models
from email_utils import send_booking_confirmation, send_doctor_notification


logger = logging.getLogger(__name__)


def _normalize(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    return s or None


def _part_of_day_range(part_of_day: str) -> Optional[Tuple[str, str]]:
    """Map a coarse part of day to a concrete time range."""
    part = part_of_day.lower()
    if part == "morning":
        return "08:00", "12:00"
    if part == "afternoon":
        return "12:00", "17:00"
    if part == "evening":
        return "17:00", "21:00"
    return None


def _interpret_day_of_week(day_of_week: str) -> Optional[str]:
    """
    Convert a day-of-week phrase into a concrete date string (YYYY-MM-DD),
    choosing the next occurrence (including today for 'today').
    """
    dow = day_of_week.strip().lower()
    today = datetime.utcnow().date()

    if dow in {"today", "tdy"}:
        return today.strftime("%Y-%m-%d")
    if dow in {"tomorrow", "tmrw", "tommorow"}:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if dow in weekdays:
        target = weekdays.index(dow)
        delta = (target - today.weekday()) % 7
        if delta == 0:
            # Today later
            delta = 7
        return (today + timedelta(days=delta)).strftime("%Y-%m-%d")

    return None


def _format_available_slots_for_day(slots: List[models.Slot]) -> str:
    times = sorted({s.start_time for s in slots})
    if not times:
        return ""
    return ", ".join(times)


def _list_available_specializations(db: Session) -> str:
    specs = db.query(models.Specialization).all()
    names = [s.name for s in specs]
    return ", ".join(names) if names else "no specializations are currently configured"


def _list_available_doctors(db: Session) -> str:
    doctors = (
        db.query(models.Doctor)
        .options(joinedload(models.Doctor.user), joinedload(models.Doctor.specialization))
        .filter(models.Doctor.is_available == True)
        .all()
    )
    if not doctors:
        return "no doctors are currently available"
    parts = []
    for d in doctors[:10]:
        spec_name = d.specialization.name if d.specialization else "General"
        parts.append(f"Dr. {d.user.full_name} ({spec_name})")
    if len(doctors) > 10:
        parts.append("... and more")
    return "; ".join(parts)


def resolve_slot_from_intent(db: Session, user: models.User, intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to resolve a concrete slot from the extracted intent.

    Returns a dict:
      {
        "status": "slot_selected" | "need_clarification" | "error",
        "message": Optional[str],
        "slot": Optional[models.Slot],
      }
    """
    logger.info("Resolving slot from intent for user %s: %s", getattr(user, "id", None), intent)

    if user.role != models.UserRole.patient:
        return {
            "status": "error",
            "message": "Only patients can book appointments via chat.",
            "slot": None,
        }

    doctor_name = _normalize(intent.get("doctor_name"))
    specialization = _normalize(intent.get("specialization"))
    date_str = _normalize(intent.get("date"))
    day_of_week = _normalize(intent.get("day_of_week"))
    time_str = _normalize(intent.get("time"))
    part_of_day = _normalize(intent.get("part_of_day"))

    # ── Doctor / Specialization resolution ──────────────────────────────────────
    candidate_doctors: List[models.Doctor] = []
    selected_specialization = None

    if doctor_name:
        logger.info("Looking up doctor by name fragment: %s", doctor_name)
        q = (
            db.query(models.Doctor)
            .join(models.User, models.Doctor.user_id == models.User.id)
            .options(joinedload(models.Doctor.user), joinedload(models.Doctor.specialization))
            .filter(
                models.Doctor.is_available == True,
                models.User.full_name.ilike(f"%{doctor_name}%"),
            )
        )
        candidate_doctors = q.all()

        if not candidate_doctors:
            msg = (
                f"I couldn't find any available doctor matching “{doctor_name}”. "
                f"Currently available doctors are: {_list_available_doctors(db)}. "
                f"Please tell me the exact doctor name you want to book with."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}

        if len(candidate_doctors) > 1:
            options = "; ".join(
                f"Dr. {d.user.full_name} ({d.specialization.name if d.specialization else 'General'})"
                for d in candidate_doctors[:10]
            )
            msg = (
                f"I found multiple doctors matching “{doctor_name}”: {options}. "
                "Please reply with the full name of the doctor you want to see, for example: "
                f"“Book Dr. {candidate_doctors[0].user.full_name} on 2026-03-04 at 10:00”."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}

        selected_specialization = candidate_doctors[0].specialization

    elif specialization:
        logger.info("Looking up specialization by name fragment: %s", specialization)
        spec = (
            db.query(models.Specialization)
            .filter(models.Specialization.name.ilike(f"%{specialization}%"))
            .first()
        )
        if not spec:
            msg = (
                f"I couldn't find any specialization matching “{specialization}”. "
                f"Available specializations are: {_list_available_specializations(db)}. "
                "Please tell me which specialization you prefer."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}

        selected_specialization = spec
        candidate_doctors = (
            db.query(models.Doctor)
            .options(joinedload(models.Doctor.user), joinedload(models.Doctor.specialization))
            .filter(
                models.Doctor.is_available == True,
                models.Doctor.specialization_id == spec.id,
            )
            .all()
        )
        if not candidate_doctors:
            msg = (
                f"There are currently no available doctors for {spec.name}. "
                "Please choose a different specialization or doctor."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}

    else:
        # No doctor or specialization specified -> impossible to compute meaningful slots.
        msg = (
            "To help you book an appointment, please tell me which doctor or specialization "
            "you would like to see. For example: “I want to see a cardiologist” or "
            "“Book an appointment with Dr. Ravi”."
        )
        return {"status": "need_clarification", "message": msg, "slot": None}

    # ── Date resolution ─────────────────────────────────────────────────────────
    target_date: Optional[str] = None

    if date_str:
        try:
            # Validate format
            parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
            target_date = parsed.strftime("%Y-%m-%d")
        except ValueError:
            msg = (
                f"The date “{date_str}” is not in the expected format YYYY-MM-DD. "
                "Please provide a date like 2026-03-04."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}
    elif day_of_week:
        interpreted = _interpret_day_of_week(day_of_week)
        if not interpreted:
            msg = (
                f"I couldn't interpret the day “{day_of_week}”. "
                "Please provide a specific calendar date in the format YYYY-MM-DD."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}
        target_date = interpreted
    else:
        msg = (
            "On what date would you like the appointment? "
            "Please reply with a specific date in the format YYYY-MM-DD, for example: "
            "“Book Dr. {name} on 2026-03-04 in the morning”."
        )
        return {"status": "need_clarification", "message": msg, "slot": None}

    logger.info("Using target date %s for slot search.", target_date)

    # ── Time / part-of-day resolution ───────────────────────────────────────────
    time_range: Optional[Tuple[str, str]] = None
    if time_str:
        # Validate HH:MM minimally
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            msg = (
                f"The time “{time_str}” is not in the expected format HH:MM (24-hour). "
                "Please provide a time like 10:00 or 15:30."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}
    elif part_of_day:
        rng = _part_of_day_range(part_of_day)
        if not rng:
            msg = (
                f"I couldn't understand the part of day “{part_of_day}”. "
                "Please give a specific time like 10:00, or say morning/afternoon/evening."
            )
            return {"status": "need_clarification", "message": msg, "slot": None}
        time_range = rng
        logger.info("Using part-of-day range %s-%s", rng[0], rng[1])
    else:
        # Missing precise time information -> we will enumerate actual options from DB.
        time_range = None

    # ── Slot query ──────────────────────────────────────────────────────────────
    doctor_ids = [d.id for d in candidate_doctors]
    logger.info("Candidate doctor IDs: %s", doctor_ids)

    q = (
        db.query(models.Slot)
        .options(joinedload(models.Slot.doctor).joinedload(models.Doctor.user),
                 joinedload(models.Slot.doctor).joinedload(models.Doctor.specialization))
        .filter(
            models.Slot.doctor_id.in_(doctor_ids),
            models.Slot.slot_date == target_date,
            models.Slot.is_booked == False,
        )
        .order_by(models.Slot.start_time)
    )

    if time_str:
        q = q.filter(models.Slot.start_time == time_str)
    elif time_range:
        start, end = time_range
        q = q.filter(and_(models.Slot.start_time >= start, models.Slot.start_time <= end))

    slots = q.all()
    logger.info("Found %d candidate slots for requested criteria.", len(slots))

    if not slots:
        # No slots matching the precise criteria; tell user explicitly.
        doc_desc = ""
        if doctor_name:
            doc_desc = f" with Dr. {candidate_doctors[0].user.full_name}"
        elif selected_specialization:
            doc_desc = f" in {selected_specialization.name}"

        time_desc = ""
        if time_str:
            time_desc = f" at {time_str}"
        elif part_of_day:
            time_desc = f" in the {part_of_day}"

        msg = (
            f"I couldn't find any available slots{doc_desc} on {target_date}{time_desc}. "
            "Please choose a different time or date."
        )
        return {"status": "need_clarification", "message": msg, "slot": None}

    if not time_str and not time_range:
        # We have a date and doctor(s), but no specific time -> enumerate actual options.
        # To avoid hallucinations, list only real slots from DB.
        grouped_by_doctor: Dict[int, List[models.Slot]] = {}
        for s in slots:
            grouped_by_doctor.setdefault(s.doctor_id, []).append(s)

        parts = []
        for d in candidate_doctors:
            doc_slots = grouped_by_doctor.get(d.id, [])
            if not doc_slots:
                continue
            times_str = _format_available_slots_for_day(doc_slots)
            if times_str:
                spec_name = d.specialization.name if d.specialization else "General"
                parts.append(f"Dr. {d.user.full_name} ({spec_name}): {times_str}")

        if not parts:
            msg = (
                f"I couldn't find any available slots on {target_date}. "
                "Please try a different date."
            )
        else:
            listing = " | ".join(parts)
            msg = (
                f"Available slots on {target_date} are: {listing}. "
                "Please reply with the exact doctor name, date, and time you prefer. "
                "For example: “Book Dr. {candidate_doctors[0].user.full_name} on "
                f"{target_date} at {slots[0].start_time}”."
            )

        return {"status": "need_clarification", "message": msg, "slot": None}

    if len(slots) > 1:
        # Even after time or part-of-day filtering we ended up with multiple concrete slots.
        # Do not guess – ask the user to choose.
        listing = ", ".join(s.start_time for s in slots[:10])
        msg = (
            f"There are multiple available slots on {target_date}: {listing}. "
            "Please reply with the exact time you prefer in HH:MM format."
        )
        return {"status": "need_clarification", "message": msg, "slot": None}

    # Exactly one slot -> we can proceed to booking.
    selected_slot = slots[0]
    logger.info("Resolved unique slot ID %s for booking.", selected_slot.id)
    return {"status": "slot_selected", "message": None, "slot": selected_slot}


def book_slot_transactionally(
    db: Session,
    user: models.User,
    slot_id: int,
    reason: Optional[str] = None,
    background_tasks: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Safely book a slot for the given patient user, guarding against races.

    Returns a dict:
      {
        "success": bool,
        "message": str,
        "appointment_id": Optional[int],
        "doctor_name": Optional[str],
        "specialization": Optional[str],
        "date": Optional[str],
        "time": Optional[str],
      }
    """
    logger.info(
        "Attempting transactional booking for user %s on slot %s",
        getattr(user, "id", None),
        slot_id,
    )

    result: Dict[str, Any] = {
        "success": False,
        "message": "",
        "appointment_id": None,
        "doctor_name": None,
        "specialization": None,
        "date": None,
        "time": None,
    }

    if user.role != models.UserRole.patient:
        result["message"] = "Only patients can book appointments."
        return result

    try:
        # Re-fetch the slot inside this transaction and lock it for update
        slot = (
            db.query(models.Slot)
            .options(
                joinedload(models.Slot.doctor).joinedload(models.Doctor.user),
                joinedload(models.Slot.doctor).joinedload(models.Doctor.specialization),
            )
            .with_for_update()
            .filter(models.Slot.id == slot_id)
            .first()
        )

        if not slot:
            logger.warning("Slot %s no longer exists.", slot_id)
            result["message"] = "That slot is no longer available."
            return result

        if slot.is_booked:
            logger.info("Slot %s was already booked when attempting to book.", slot_id)
            result["message"] = "Sorry, that slot has just been booked by someone else. Please choose another time."
            return result

        appointment = models.Appointment(
            slot_id=slot.id,
            patient_id=user.id,
            reason=reason,
        )

        slot.is_booked = True
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        db.refresh(slot)

        doctor_user = slot.doctor.user
        spec = slot.doctor.specialization

        result.update(
            {
                "success": True,
                "message": "Appointment booked successfully.",
                "appointment_id": appointment.id,
                "doctor_name": doctor_user.full_name,
                "specialization": spec.name if spec else "",
                "date": slot.slot_date,
                "time": slot.start_time,
            }
        )

        logger.info(
            "Successfully booked appointment %s for user %s with doctor %s on %s at %s",
            appointment.id,
            user.id,
            doctor_user.full_name,
            slot.slot_date,
            slot.start_time,
        )

        # Schedule notification emails in the background, if available.
        if background_tasks is not None:
            from email_utils import send_booking_confirmation, send_doctor_notification

            background_tasks.add_task(
                send_booking_confirmation,
                patient_email=user.email,
                patient_name=user.full_name,
                doctor_name=doctor_user.full_name,
                specialization=spec.name if spec else "",
                slot_date=slot.slot_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                reason=reason or "",
            )
            background_tasks.add_task(
                send_doctor_notification,
                doctor_email=doctor_user.email,
                doctor_name=doctor_user.full_name,
                patient_name=user.full_name,
                patient_phone=user.phone or "",
                slot_date=slot.slot_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                reason=reason or "",
            )

        return result

    except IntegrityError as exc:
        logger.error("IntegrityError while booking slot %s: %s", slot_id, exc)
        db.rollback()
        result["message"] = "Sorry, there was a conflict while booking that slot. Please try another time."
        return result

    except Exception as exc:  # pragma: no cover - safety net
        logger.error("Unexpected error while booking slot %s: %s", slot_id, exc)
        db.rollback()
        result["message"] = "An unexpected error occurred while booking your appointment."
        return result

