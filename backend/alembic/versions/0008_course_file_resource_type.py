"""add course file resource type

Revision ID: 0008_course_file_resource_type
Revises: 0007_course_files
Create Date: 2026-06-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_course_file_resource_type"
down_revision = "0007_course_files"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "course_files",
        sa.Column(
            "resource_type",
            sa.String(length=40),
            nullable=False,
            server_default="public_resource",
        ),
    )
    op.create_index("ix_course_files_resource_type", "course_files", ["resource_type"])


def downgrade() -> None:
    op.drop_index("ix_course_files_resource_type", table_name="course_files")
    op.drop_column("course_files", "resource_type")
