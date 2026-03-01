from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from datetime import timedelta, datetime
from typing import List, Optional
import threading
import logging

from database import get_db, engine
import models
import schemas
import rag
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_role
)
from email_utils import (
    send_booking_confirmation,
    send_doctor_notification,
    send_cancellation_email,
    send_prescription_email,
)
from services.booking_service import resolve_slot_from_intent, book_slot_transactionally
from config import settings

logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

def run_migrations():
    with engine.connect() as connection:
        try:
            connection.execute(text("SELECT prescription_notes FROM appointments LIMIT 1"))
        except Exception:
            print("Migrating DB: Adding missing columns to appointments table...")
            try:
                connection.execute(text("ALTER TABLE appointments ADD COLUMN prescription_notes TEXT"))
                connection.execute(text("ALTER TABLE appointments ADD COLUMN medications TEXT"))
                connection.commit()
            except Exception as e:
                print(f"Migration failed: {e}")

run_migrations()

app = FastAPI(title="DoctorBook API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=schemas.TokenResponse, status_code=201)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(400, "Username already taken")
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "Email already registered")

    user = models.User(
        full_name=data.full_name,
        username=data.username,
        email=data.email,
        password=hash_password(data.password),
        role=data.role,
        phone=data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
    )


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
    )


@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ──────────────────────────────────────────────────────────────────────────────
# SPECIALIZATIONS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/specializations", response_model=List[schemas.SpecializationOut])
def list_specializations(db: Session = Depends(get_db)):
    return db.query(models.Specialization).all()


@app.post("/specializations", response_model=schemas.SpecializationOut, status_code=201)
def create_specialization(
    data: schemas.SpecializationCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    if db.query(models.Specialization).filter(models.Specialization.name == data.name).first():
        raise HTTPException(400, "Specialization already exists")
    spec = models.Specialization(**data.model_dump())
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@app.delete("/specializations/{spec_id}", status_code=204)
def delete_specialization(
    spec_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    spec = db.query(models.Specialization).filter(models.Specialization.id == spec_id).first()
    if not spec:
        raise HTTPException(404, "Not found")
    db.delete(spec)
    db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# DOCTORS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/doctors", response_model=List[schemas.DoctorOut])
def list_doctors(
    specialization_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Doctor).options(
        joinedload(models.Doctor.user),
        joinedload(models.Doctor.specialization),
    ).filter(models.Doctor.is_available == True)
    if specialization_id:
        q = q.filter(models.Doctor.specialization_id == specialization_id)
    return q.all()


@app.get("/doctors/{doctor_id}", response_model=schemas.DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).options(
        joinedload(models.Doctor.user),
        joinedload(models.Doctor.specialization),
    ).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    return doctor


@app.post("/doctors", response_model=schemas.DoctorOut, status_code=201)
def create_doctor(
    data: schemas.DoctorCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    if db.query(models.Doctor).filter(models.Doctor.user_id == data.user_id).first():
        raise HTTPException(400, "Doctor profile already exists for this user")
    doctor = models.Doctor(**data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return db.query(models.Doctor).options(
        joinedload(models.Doctor.user),
        joinedload(models.Doctor.specialization),
    ).filter(models.Doctor.id == doctor.id).first()


@app.put("/doctors/{doctor_id}", response_model=schemas.DoctorOut)
def update_doctor(
    doctor_id: int,
    data: schemas.DoctorCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    for k, v in data.model_dump().items():
        setattr(doctor, k, v)
    db.commit()
    db.refresh(doctor)
    return doctor


# ──────────────────────────────────────────────────────────────────────────────
# SLOTS
# ──────────────────────────────────────────────────────────────────────────────

def calc_end_time(start: str) -> str:
    h, m = map(int, start.split(":"))
    m += 30
    if m >= 60:
        h += 1
        m -= 60
    return f"{h:02d}:{m:02d}"


@app.get("/doctors/{doctor_id}/slots", response_model=List[schemas.SlotOut])
def get_slots(
    doctor_id: int,
    date: Optional[str] = None,
    available_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(models.Slot).filter(models.Slot.doctor_id == doctor_id)
    if date:
        q = q.filter(models.Slot.slot_date == date)
    if available_only:
        q = q.filter(models.Slot.is_booked == False)
    return q.order_by(models.Slot.slot_date, models.Slot.start_time).all()


@app.post("/doctors/{doctor_id}/slots", response_model=schemas.SlotOut, status_code=201)
def create_slot(
    doctor_id: int,
    data: schemas.SlotCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Allow doctor themselves or admin
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    if current_user.role != "admin" and doctor.user_id != current_user.id:
        raise HTTPException(403, "Cannot add slots for another doctor")

    end_time = calc_end_time(data.start_time)

    # Check for duplicate slot
    existing = db.query(models.Slot).filter(
        models.Slot.doctor_id == doctor_id,
        models.Slot.slot_date == data.slot_date,
        models.Slot.start_time == data.start_time,
    ).first()
    if existing:
        raise HTTPException(400, "Slot already exists for this time")

    slot = models.Slot(
        doctor_id=doctor_id,
        slot_date=data.slot_date,
        start_time=data.start_time,
        end_time=end_time,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@app.post("/doctors/{doctor_id}/slots/bulk", status_code=201)
def create_slots_bulk(
    doctor_id: int,
    data: schemas.SlotBulkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    if current_user.role != "admin" and doctor.user_id != current_user.id:
        raise HTTPException(403, "Cannot add slots for another doctor")

    try:
        start_date = datetime.strptime(data.start_date, "%Y-%m-%d").date() if data.start_date else datetime.now().date()
        end_date = datetime.strptime(data.end_date, "%Y-%m-%d").date() if data.end_date else start_date + timedelta(weeks=data.weeks)
        start_t = datetime.strptime(data.start_time, "%H:%M").time()
        end_t = datetime.strptime(data.end_time, "%H:%M").time()
        lunch_s = datetime.strptime(data.lunch_start, "%H:%M").time() if data.lunch_start else None
        lunch_e = datetime.strptime(data.lunch_end, "%H:%M").time() if data.lunch_end else None
    except ValueError:
        raise HTTPException(400, "Invalid date or time format")

    if start_date > end_date:
        raise HTTPException(400, "Start date must be before end date")
    if start_t >= end_t:
        raise HTTPException(400, "Start time must be before end time")

    current_date = start_date
    created_count = 0

    while current_date <= end_date:
        if current_date.weekday() not in data.days_of_week:
            current_date += timedelta(days=1)
            continue
        
        curr_dt = datetime.combine(current_date, start_t)
        day_end_dt = datetime.combine(current_date, end_t)
        
        while curr_dt + timedelta(minutes=data.slot_duration) <= day_end_dt:
            slot_start_t = curr_dt.time()
            slot_end_t = (curr_dt + timedelta(minutes=data.slot_duration)).time()
            
            is_lunch = False
            if lunch_s and lunch_e:
                if max(slot_start_t, lunch_s) < min(slot_end_t, lunch_e):
                    is_lunch = True
            
            if not is_lunch:
                date_str = current_date.strftime("%Y-%m-%d")
                s_time_str = slot_start_t.strftime("%H:%M")
                e_time_str = slot_end_t.strftime("%H:%M")
                
                existing = db.query(models.Slot).filter(
                    models.Slot.doctor_id == doctor_id,
                    models.Slot.slot_date == date_str,
                    models.Slot.start_time == s_time_str,
                ).first()
                
                if not existing:
                    slot = models.Slot(
                        doctor_id=doctor_id,
                        slot_date=date_str,
                        start_time=s_time_str,
                        end_time=e_time_str,
                    )
                    db.add(slot)
                    created_count += 1
            
            curr_dt += timedelta(minutes=data.slot_duration)
        current_date += timedelta(days=1)

    db.commit()
    return {"message": f"Created {created_count} slots"}


@app.delete("/doctors/{doctor_id}/slots/future", status_code=204)
def clear_future_slots(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    if current_user.role != "admin" and doctor.user_id != current_user.id:
        raise HTTPException(403, "Forbidden")

    today = datetime.now().strftime("%Y-%m-%d")
    db.query(models.Slot).filter(
        models.Slot.doctor_id == doctor_id,
        models.Slot.is_booked == False,
        models.Slot.slot_date >= today
    ).delete(synchronize_session=False)
    db.commit()


@app.delete("/doctors/{doctor_id}/slots/{slot_id}", status_code=204)
def delete_slot(
    doctor_id: int,
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    slot = db.query(models.Slot).filter(
        models.Slot.id == slot_id,
        models.Slot.doctor_id == doctor_id,
    ).first()
    if not slot:
        raise HTTPException(404, "Slot not found")
    if slot.is_booked:
        raise HTTPException(400, "Cannot delete a booked slot")

    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if current_user.role != "admin" and doctor.user_id != current_user.id:
        raise HTTPException(403, "Forbidden")

    db.delete(slot)
    db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# APPOINTMENTS
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/appointments", response_model=schemas.AppointmentOut, status_code=201)
def book_appointment(
    data: schemas.AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("patient")),
):
    slot = db.query(models.Slot).filter(models.Slot.id == data.slot_id).first()
    if not slot:
        raise HTTPException(404, "Slot not found")
    if slot.is_booked:
        raise HTTPException(409, "Slot is already booked")

    # Mark slot as booked
    slot.is_booked = True

    appointment = models.Appointment(
        slot_id=data.slot_id,
        patient_id=current_user.id,
        reason=data.reason,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Load relations for email
    appt = db.query(models.Appointment).options(
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.user),
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.specialization),
        joinedload(models.Appointment.patient),
    ).filter(models.Appointment.id == appointment.id).first()

    doctor_user = appt.slot.doctor.user
    spec = appt.slot.doctor.specialization

    # Send emails in background
    background_tasks.add_task(
        send_booking_confirmation,
        patient_email=current_user.email,
        patient_name=current_user.full_name,
        doctor_name=doctor_user.full_name,
        specialization=spec.name if spec else "",
        slot_date=appt.slot.slot_date,
        start_time=appt.slot.start_time,
        end_time=appt.slot.end_time,
        reason=data.reason or "",
    )
    background_tasks.add_task(
        send_doctor_notification,
        doctor_email=doctor_user.email,
        doctor_name=doctor_user.full_name,
        patient_name=current_user.full_name,
        patient_phone=current_user.phone or "",
        slot_date=appt.slot.slot_date,
        start_time=appt.slot.start_time,
        end_time=appt.slot.end_time,
        reason=data.reason or "",
    )

    return appt


@app.get("/appointments/my", response_model=List[schemas.AppointmentOut])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Appointment).options(
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.user),
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.specialization),
        joinedload(models.Appointment.patient),
    )
    if current_user.role == "patient":
        q = q.filter(models.Appointment.patient_id == current_user.id)
    elif current_user.role == "doctor":
        doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
        if not doctor:
            return []
        q = q.join(models.Slot).filter(models.Slot.doctor_id == doctor.id)
    else:
        pass  # admin sees all
    return q.order_by(models.Appointment.created_at.desc()).all()


@app.put("/appointments/{appointment_id}/cancel", response_model=schemas.AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    appt = db.query(models.Appointment).options(
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.user),
        joinedload(models.Appointment.patient),
    ).filter(models.Appointment.id == appointment_id).first()

    if not appt:
        raise HTTPException(404, "Appointment not found")

    # Only patient who booked, the doctor, or admin can cancel
    if current_user.role == "patient" and appt.patient_id != current_user.id:
        raise HTTPException(403, "Forbidden")

    if appt.status == "cancelled":
        raise HTTPException(400, "Already cancelled")

    appt.status = models.AppointmentStatus.cancelled
    appt.slot.is_booked = False
    db.commit()
    db.refresh(appt)

    # Notify both parties
    doctor_user = appt.slot.doctor.user
    background_tasks.add_task(
        send_cancellation_email,
        to_email=appt.patient.email,
        recipient_name=appt.patient.full_name,
        role="patient",
        slot_date=appt.slot.slot_date,
        start_time=appt.slot.start_time,
    )
    background_tasks.add_task(
        send_cancellation_email,
        to_email=doctor_user.email,
        recipient_name=doctor_user.full_name,
        role="doctor",
        slot_date=appt.slot.slot_date,
        start_time=appt.slot.start_time,
    )

    return appt


@app.put("/appointments/{appointment_id}/complete", response_model=schemas.AppointmentOut)
def complete_appointment(
    appointment_id: int,
    data: schemas.AppointmentComplete,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    appt = db.query(models.Appointment).options(
        joinedload(models.Appointment.slot).joinedload(models.Slot.doctor),
        joinedload(models.Appointment.patient),
    ).filter(models.Appointment.id == appointment_id).first()

    if not appt:
        raise HTTPException(404, "Appointment not found")
    
    # Verify this doctor owns the appointment
    if appt.slot.doctor.user_id != current_user.id:
        raise HTTPException(403, "You can only complete your own appointments")

    if appt.status == models.AppointmentStatus.completed:
        raise HTTPException(400, "Appointment already completed")

    appt.status = models.AppointmentStatus.completed
    appt.prescription_notes = data.prescription_notes
    appt.medications = data.medications
    
    db.commit()
    db.refresh(appt)

    # Send prescription email to patient
    background_tasks.add_task(
        send_prescription_email,
        to_email=appt.patient.email,
        patient_name=appt.patient.full_name,
        doctor_name=current_user.full_name,
        slot_date=appt.slot.slot_date,
        notes=data.prescription_notes,
        medications=data.medications,
    )

    return appt


@app.get("/appointments/all", response_model=List[schemas.AppointmentOut])
def all_appointments(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    return db.query(models.Appointment).options(
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.user),
        joinedload(models.Appointment.slot)
        .joinedload(models.Slot.doctor)
        .joinedload(models.Doctor.specialization),
        joinedload(models.Appointment.patient),
    ).order_by(models.Appointment.created_at.desc()).all()


# ─── CHAT BOT ─────────────────────────────────────────────────────────────────

def _single_message_stream(message: str):
    yield message


@app.post("/chat", response_model=schemas.ChatResponse)
def chat_with_bot(
    data: schemas.ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Preserve existing behavior for non-patient roles.
    if current_user.role != models.UserRole.patient:
        response_text = rag.ask_bot(data.message, db, current_user)
        return schemas.ChatResponse(response=response_text)

    # For patients, first try to detect booking intent.
    intent = rag.extract_booking_intent(data.message)
    logger.info("Chat intent for user %s: %s", current_user.id, intent)

    if intent.get("intent") != "book_appointment":
        response_text = rag.ask_bot(data.message, db, current_user)
        return schemas.ChatResponse(response=response_text)

    # Booking intent: resolve slot and book transactionally.
    resolution = resolve_slot_from_intent(db, current_user, intent)
    logger.info("Slot resolution result for user %s: %s", current_user.id, resolution)

    if resolution["status"] == "slot_selected" and resolution.get("slot") is not None:
        slot = resolution["slot"]
        booking_result = book_slot_transactionally(
            db=db,
            user=current_user,
            slot_id=slot.id,
            reason=None,
            background_tasks=background_tasks,
        )
        logger.info("Booking transaction result for user %s: %s", current_user.id, booking_result)

        if not booking_result.get("success"):
            return schemas.ChatResponse(response=booking_result.get("message") or "Unable to book that slot.")

        confirmation_text = (
            f"Your appointment with Dr. {booking_result['doctor_name']} "
            f"({booking_result['specialization']}) is confirmed for "
            f"{booking_result['date']} at {booking_result['time']}. "
            f"Appointment ID: {booking_result['appointment_id']}."
        )
        return schemas.ChatResponse(response=confirmation_text)

    # Any non-terminal resolution returns its clarification or error message.
    message = resolution.get("message") or "Sorry, I couldn't book that appointment. Please try again."
    return schemas.ChatResponse(response=message)


@app.post("/chat/stream")
def chat_with_bot_stream(
    data: schemas.ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Non-patients: preserve existing streaming chatbot behavior.
    if current_user.role != models.UserRole.patient:
        return StreamingResponse(rag.ask_bot_stream(data.message, db, current_user), media_type="text/plain")

    # Patients: attempt booking intent extraction first.
    intent = rag.extract_booking_intent(data.message)
    logger.info("Chat (stream) intent for user %s: %s", current_user.id, intent)

    if intent.get("intent") != "book_appointment":
        return StreamingResponse(rag.ask_bot_stream(data.message, db, current_user), media_type="text/plain")

    resolution = resolve_slot_from_intent(db, current_user, intent)
    logger.info("Slot (stream) resolution result for user %s: %s", current_user.id, resolution)

    if resolution["status"] == "slot_selected" and resolution.get("slot") is not None:
        slot = resolution["slot"]
        booking_result = book_slot_transactionally(
            db=db,
            user=current_user,
            slot_id=slot.id,
            reason=None,
            background_tasks=background_tasks,
        )
        logger.info("Booking (stream) transaction result for user %s: %s", current_user.id, booking_result)

        if not booking_result.get("success"):
            msg = booking_result.get("message") or "Unable to book that slot."
        else:
            msg = (
                f"Your appointment with Dr. {booking_result['doctor_name']} "
                f"({booking_result['specialization']}) is confirmed for "
                f"{booking_result['date']} at {booking_result['time']}. "
                f"Appointment ID: {booking_result['appointment_id']}."
            )
    else:
        msg = resolution.get("message") or "Sorry, I couldn't book that appointment. Please try again."

    return StreamingResponse(_single_message_stream(msg), media_type="text/plain")

# ──────────────────────────────────────────────────────────────────────────────
# USERS (admin)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/users", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin")),
):
    return db.query(models.User).all()
