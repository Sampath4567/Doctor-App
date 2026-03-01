from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Boolean, Text, Enum
)
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150))
    username = Column(String(100), unique=True, index=True)
    email = Column(String(200), unique=True, index=True)
    password = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.patient)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    appointments = relationship("Appointment", back_populates="patient", foreign_keys="Appointment.patient_id")


class Specialization(Base):
    __tablename__ = "specializations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # emoji or icon name

    doctors = relationship("Doctor", back_populates="specialization")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    specialization_id = Column(Integer, ForeignKey("specializations.id"))
    bio = Column(Text, nullable=True)
    qualification = Column(String(255), nullable=True)
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(Integer, default=0)  # in cents or smallest unit
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="doctor_profile")
    specialization = relationship("Specialization", back_populates="doctors")
    slots = relationship("Slot", back_populates="doctor")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    slot_date = Column(String(20))         # "2025-06-10"
    start_time = Column(String(10))        # "10:00"
    end_time = Column(String(10))          # "10:30"  (always 30 min later)
    is_booked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    doctor = relationship("Doctor", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), unique=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(Text, nullable=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.booked)
    prescription_notes = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    slot = relationship("Slot", back_populates="appointment")
    patient = relationship("User", back_populates="appointments", foreign_keys=[patient_id])
