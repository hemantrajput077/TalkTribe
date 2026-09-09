"""PROF-01: add profiles table

Revision ID: 3f8e2a1b9c47
Revises: 4194b8bd8daa
Create Date: 2026-09-09

Creates the profiles table linked to users.id. One profile per user,
lazy-created on first GET /api/v1/profiles/me. Deleting a user cascades
to delete their profile row automatically.
"""

import sqlalchemy as sa
from alembic import op

revision = '3f8e2a1b9c47'
down_revision = 'f2a9b3c7d1e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profession', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_profiles_id', 'profiles', ['id'], unique=False)
    op.create_index('ix_profiles_user_id', 'profiles', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_profiles_user_id', table_name='profiles')
    op.drop_index('ix_profiles_id', table_name='profiles')
    op.drop_table('profiles')
