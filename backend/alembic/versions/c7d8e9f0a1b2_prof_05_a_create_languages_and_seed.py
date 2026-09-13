"""PROF-05-a: create languages table and seed English

Revision ID: c7d8e9f0a1b2
Revises: 3d77b96a2528
Create Date: 2026-09-13

Creates the languages reference table and seeds English (ISO 639-1 code: en)
as the only supported language for MVP. Additional languages are out of scope
until the admin language-management feature is built.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

revision = 'c7d8e9f0a1b2'
down_revision = '3d77b96a2528'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_languages_code'),
        sa.UniqueConstraint('name', name='uq_languages_name'),
    )
    op.create_index('ix_languages_id', 'languages', ['id'], unique=False)

    op.execute(text("INSERT INTO languages (name, code) VALUES ('English', 'en')"))


def downgrade() -> None:
    op.drop_index('ix_languages_id', table_name='languages')
    op.drop_table('languages')
