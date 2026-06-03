"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_admin', sa.Boolean, nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'courses',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('max_students', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'subscribers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('subscriber_id', sa.Integer, sa.ForeignKey('subscribers.id'), nullable=False),
        sa.Column('course_id', sa.Integer, sa.ForeignKey('courses.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'active'")),
        sa.Column('payment_status', sa.String(50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('enrollments')
    op.drop_table('subscribers')
    op.drop_table('courses')
    op.drop_table('users')
