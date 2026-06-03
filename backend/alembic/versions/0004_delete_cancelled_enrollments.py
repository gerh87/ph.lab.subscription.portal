"""delete cancelled enrollments

Revision ID: 0004_del_cancelled
Revises: 0003_subscriber_user_link
Create Date: 2026-06-02
"""

from alembic import op


revision = "0004_del_cancelled"
down_revision = "0003_subscriber_user_link"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DELETE FROM enrollments WHERE status = 'cancelled'")


def downgrade():
    pass
