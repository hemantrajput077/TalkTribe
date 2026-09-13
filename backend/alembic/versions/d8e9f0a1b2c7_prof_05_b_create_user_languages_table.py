"""PROF-05-b: create user_languages join table

Revision ID: d8e9f0a1b2c7
Revises: c7d8e9f0a1b2
Create Date: 2026-09-13

user_languages maps each user to languages they speak, with a role
(NATIVE, FLUENT, LEARNING) and an optional CEFR proficiency level
(A1-C2, required only for LEARNING role).

PUT /api/v1/profiles/me/languages uses full-replace semantics:
all rows for the user are deleted and replaced atomically on every call.

Unique constraint on (user_id, language_id, role) prevents duplicate
role entries for the same user+language combination. The business rule
that the same language cannot be both NATIVE and LEARNING is enforced
at the application layer.
"""

import sqlalchemy as sa
from alembic import op

revision = 'd8e9f0a1b2c7'
down_revision = 'c7d8e9f0a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('language_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('proficiency', sa.String(length=5), nullable=True),
        sa.ForeignKeyConstraint(['language_id'], ['languages.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'language_id', 'role', name='uq_user_language_role'),
    )
    op.create_index('ix_user_languages_id', 'user_languages', ['id'], unique=False)
    op.create_index('ix_user_languages_user_id', 'user_languages', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_user_languages_user_id', table_name='user_languages')
    op.drop_index('ix_user_languages_id', table_name='user_languages')
    op.drop_table('user_languages')
