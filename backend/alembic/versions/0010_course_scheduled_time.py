"""add course scheduled time

Revision ID: 0010_course_scheduled_time
Revises: 0009_enrollment_payment_details
Create Date: 2026-06-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_course_scheduled_time"
down_revision = "0009_enrollment_payment_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("scheduled_time", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "scheduled_time")
