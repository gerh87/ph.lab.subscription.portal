"""link subscribers to users

Revision ID: 0003_subscriber_user_link
Revises: 0002_auth0_user_fields
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_subscriber_user_link"
down_revision = "0002_auth0_user_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscribers", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_subscribers_user_id", "subscribers", ["user_id"])
    op.create_foreign_key(
        "fk_subscribers_user_id_users",
        "subscribers",
        "users",
        ["user_id"],
        ["id"],
    )
    op.execute(
        """
        UPDATE subscribers
        SET user_id = users.id
        FROM subscribers
        INNER JOIN users ON LOWER(subscribers.email) = LOWER(users.email)
        WHERE subscribers.user_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_subscribers_user_id_users", "subscribers", type_="foreignkey")
    op.drop_index("ix_subscribers_user_id", table_name="subscribers")
    op.drop_column("subscribers", "user_id")
