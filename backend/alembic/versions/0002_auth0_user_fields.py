"""add auth0 user fields

Revision ID: 0002_auth0_user_fields
Revises: 0001_initial
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_auth0_user_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auth0_sub", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("picture", sa.String(1024), nullable=True))
    op.create_index("ix_users_auth0_sub", "users", ["auth0_sub"])


def downgrade() -> None:
    op.drop_index("ix_users_auth0_sub", table_name="users")
    op.drop_column("users", "picture")
    op.drop_column("users", "auth0_sub")
