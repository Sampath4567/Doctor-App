"""initial schema

Revision ID: 202502281200
Revises: None
Create Date: 2025-02-28 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "202502281200"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("patient", "doctor", "admin", name="user_role"),
            nullable=False,
        ),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    # specializations
    op.create_table(
        "specializations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("name", name="uq_specializations_name"),
    )
    op.create_index(
        "ix_specializations_name",
        "specializations",
        ["name"],
        unique=False,
    )

    # doctors
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("specialization_id", sa.Integer(), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("qualification", sa.String(length=255), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "consultation_fee_cents",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["specialization_id"], ["specializations.id"]),
        sa.UniqueConstraint("user_id", name="uq_doctors_user_id"),
    )
    op.create_index("ix_doctors_user_id", "doctors", ["user_id"], unique=False)
    op.create_index(
        "ix_doctors_specialization_id",
        "doctors",
        ["specialization_id"],
        unique=False,
    )

    # slots
    op.create_table(
        "slots",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_booked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"]),
        sa.UniqueConstraint(
            "doctor_id",
            "start_time",
            name="uq_slots_doctor_start_time",
        ),
    )
    op.create_index("ix_slots_doctor_id", "slots", ["doctor_id"], unique=False)
    op.create_index("ix_slots_start_time", "slots", ["start_time"], unique=False)

    # appointments
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("slot_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "booked",
                "cancelled",
                "completed",
                name="appointment_status",
            ),
            nullable=False,
            server_default="booked",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["slot_id"], ["slots.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"]),
        sa.UniqueConstraint("slot_id", name="uq_appointments_slot_id"),
        sa.CheckConstraint(
            "status in ('booked', 'cancelled', 'completed')",
            name="ck_appointments_status_valid",
        ),
    )
    op.create_index(
        "ix_appointments_slot_id",
        "appointments",
        ["slot_id"],
        unique=False,
    )
    op.create_index(
        "ix_appointments_patient_id",
        "appointments",
        ["patient_id"],
        unique=False,
    )

    # refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("token", name="uq_refresh_tokens_token"),
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index("ix_appointments_slot_id", table_name="appointments")
    op.drop_table("appointments")

    op.drop_index("ix_slots_start_time", table_name="slots")
    op.drop_index("ix_slots_doctor_id", table_name="slots")
    op.drop_table("slots")

    op.drop_index("ix_doctors_specialization_id", table_name="doctors")
    op.drop_index("ix_doctors_user_id", table_name="doctors")
    op.drop_table("doctors")

    op.drop_index("ix_specializations_name", table_name="specializations")
    op.drop_table("specializations")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

