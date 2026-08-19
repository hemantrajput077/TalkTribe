"""fix otps_user_id_fkey restore cascade

Revision ID: 4194b8bd8daa
Revises: 748a3a90d846
Create Date: 2026-08-19

Migration 748a3a90d846 accidentally recreated the otps.user_id FK without
ON DELETE CASCADE (the Alembic autogenerate dropped it). This migration
restores it so that deleting a user also deletes their OTP rows.
"""

from alembic import op

revision = '4194b8bd8daa'
down_revision = '748a3a90d846'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the cascade-less FK that migration 748a3a90d846 left behind.
    # PostgreSQL auto-named it otps_user_id_fkey when None was passed.
    op.drop_constraint('otps_user_id_fkey', 'otps', type_='foreignkey')
    op.create_foreign_key(
        'otps_user_id_fkey',
        'otps', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('otps_user_id_fkey', 'otps', type_='foreignkey')
    op.create_foreign_key(
        'otps_user_id_fkey',
        'otps', 'users',
        ['user_id'], ['id'],
    )
