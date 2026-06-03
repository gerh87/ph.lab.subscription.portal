"""add course files

Revision ID: 0007_course_files
Revises: 0006_course_zoom_url
Create Date: 2026-06-03
"""

import sqlalchemy as sa
from alembic import op


revision = "0007_course_files"
down_revision = "0006_course_zoom_url"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "course_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("guid", sa.String(length=36), nullable=False),
        sa.Column("storage_key", sa.String(length=128), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_course_files_course_id", "course_files", ["course_id"])
    op.create_index("ix_course_files_guid", "course_files", ["guid"], unique=True)
    op.create_index("ix_course_files_uploaded_by_user_id", "course_files", ["uploaded_by_user_id"])
    op.create_unique_constraint("uq_course_files_storage_key", "course_files", ["storage_key"])


def downgrade():
    op.drop_constraint("uq_course_files_storage_key", "course_files", type_="unique")
    op.drop_index("ix_course_files_uploaded_by_user_id", table_name="course_files")
    op.drop_index("ix_course_files_guid", table_name="course_files")
    op.drop_index("ix_course_files_course_id", table_name="course_files")
    op.drop_table("course_files")
