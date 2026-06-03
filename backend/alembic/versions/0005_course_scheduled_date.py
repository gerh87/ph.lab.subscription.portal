"""add course scheduled date

Revision ID: 0005_course_date
Revises: 0004_del_cancelled
Create Date: 2026-06-02
"""

import sqlalchemy as sa
from alembic import op


revision = "0005_course_date"
down_revision = "0004_del_cancelled"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("courses", sa.Column("scheduled_date", sa.Date(), nullable=True))


def downgrade():
    op.drop_column("courses", "scheduled_date")
