"""
SQLAlchemy ORM models for the DoctorBook backend.

Individual models are defined in sibling modules (user, doctor, specialization,
slot, appointment, refresh_token) and imported in `app.db.base` so that
Alembic can discover them via `Base.metadata`.
"""

