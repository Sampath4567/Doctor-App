from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, AppointmentStatus


# ─── Auth Schemas ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: UserRole = UserRole.patient


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


# ─── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    role: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Specialization ────────────────────────────────────────────────────────────

class SpecializationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None


class SpecializationOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]

    class Config:
        from_attributes = True


# ─── Doctor ────────────────────────────────────────────────────────────────────

class DoctorCreate(BaseModel):
    user_id: int
    specialization_id: int
    bio: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: int = 0
    consultation_fee: int = 0


class DoctorOut(BaseModel):
    id: int
    user_id: int
    specialization_id: int
    bio: Optional[str]
    qualification: Optional[str]
    experience_years: int
    consultation_fee: int
    is_available: bool
    user: Optional["UserOut"] = None
    specialization: Optional[SpecializationOut] = None

    class Config:
        from_attributes = True


# ─── Slot ──────────────────────────────────────────────────────────────────────

class SlotBulkCreate(BaseModel):
    start_date: Optional[str] = None  # "YYYY-MM-DD"
    end_date: Optional[str] = None    # "YYYY-MM-DD"
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    slot_duration: int = 30
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    days_of_week: List[int] = [0, 1, 2, 3, 4] # 0=Mon, 6=Sun
    weeks: int = 4

class SlotCreate(BaseModel):
    slot_date: str    # "YYYY-MM-DD"
    start_time: str   # "HH:MM"


class SlotOut(BaseModel):
    id: int
    doctor_id: int
    slot_date: str
    start_time: str
    end_time: str
    is_booked: bool

    class Config:
        from_attributes = True


# ─── Appointment ───────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    slot_id: int
    reason: Optional[str] = None

class AppointmentComplete(BaseModel):
    prescription_notes: str
    medications: str

class AppointmentOut(BaseModel):
    id: int
    slot_id: int
    patient_id: int
    reason: Optional[str]
    status: str
    prescription_notes: Optional[str] = None
    medications: Optional[str] = None
    notes: Optional[str]
    created_at: datetime
    slot: Optional[SlotOut] = None
    patient: Optional[UserOut] = None

    class Config:
        from_attributes = True

# ─── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

DoctorOut.model_rebuild()
