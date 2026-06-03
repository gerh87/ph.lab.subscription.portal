"""add course zoom url

Revision ID: 0006_course_zoom_url
Revises: 0005_course_date
Create Date: 2026-06-02
"""

import sqlalchemy as sa
from alembic import op


revision = "0006_course_zoom_url"
down_revision = "0005_course_date"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("courses", sa.Column("zoom_url", sa.String(length=1024), nullable=True))


def downgrade():
    op.drop_column("courses", "zoom_url")
