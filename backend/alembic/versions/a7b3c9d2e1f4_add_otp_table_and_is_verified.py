"""Add OTP table and is_verified field to users

Revision ID: a7b3c9d2e1f4
Revises: c36d28f94a42
Create Date: 2026-08-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'a7b3c9d2e1f4'
down_revision = 'c36d28f94a42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade database schema.

    Changes:
    1. Add is_verified column to users table
    2. Create otps table for storing OTP codes
    """
    # Add is_verified column to users table
    op.add_column('users',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false')
    )

    # Create otps table
    op.create_table('otps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('otp', sa.String(length=6), nullable=False),
        sa.Column('purpose', sa.String(length=30), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index(op.f('ix_otps_id'), 'otps', ['id'], unique=False)
    op.create_index('ix_otps_user_id_purpose', 'otps', ['user_id', 'purpose'], unique=False)
    op.create_index('ix_otps_expires_at', 'otps', ['expires_at'], unique=False)


def downgrade() -> None:
    """
    Downgrade database schema (rollback changes).

    This removes the changes made in upgrade().
    """
    # Drop indexes
    op.drop_index('ix_otps_expires_at', table_name='otps')
    op.drop_index('ix_otps_user_id_purpose', table_name='otps')
    op.drop_index(op.f('ix_otps_id'), table_name='otps')

    # Drop otps table
    op.drop_table('otps')

    # Remove is_verified column from users table
    op.drop_column('users', 'is_verified')
