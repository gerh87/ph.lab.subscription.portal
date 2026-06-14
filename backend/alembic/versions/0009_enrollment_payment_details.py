"""add enrollment payment details

Revision ID: 0009_enrollment_payment_details
Revises: 0008_course_file_resource_type
Create Date: 2026-06-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_enrollment_payment_details"
down_revision = "0008_course_file_resource_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("enrollments", sa.Column("payment_method", sa.String(length=50), nullable=True))
    op.add_column("enrollments", sa.Column("payment_reference", sa.String(length=255), nullable=True))
    op.add_column("enrollments", sa.Column("payment_provider_id", sa.String(length=255), nullable=True))
    op.add_column("enrollments", sa.Column("payment_provider_status", sa.String(length=50), nullable=True))
    op.add_column("enrollments", sa.Column("manual_payment_notes", sa.Text(), nullable=True))
    op.add_column("enrollments", sa.Column("payment_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("enrollments", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_enrollments_payment_method", "enrollments", ["payment_method"])
    op.create_index("ix_enrollments_payment_status", "enrollments", ["payment_status"])


def downgrade() -> None:
    op.drop_index("ix_enrollments_payment_status", table_name="enrollments")
    op.drop_index("ix_enrollments_payment_method", table_name="enrollments")
    op.drop_column("enrollments", "paid_at")
    op.drop_column("enrollments", "payment_requested_at")
    op.drop_column("enrollments", "manual_payment_notes")
    op.drop_column("enrollments", "payment_provider_status")
    op.drop_column("enrollments", "payment_provider_id")
    op.drop_column("enrollments", "payment_reference")
    op.drop_column("enrollments", "payment_method")
