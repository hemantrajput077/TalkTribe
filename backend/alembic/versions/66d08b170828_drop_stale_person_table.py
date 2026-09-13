"""Drop stale person table

Revision ID: 66d08b170828
Revises: ff432d6f2a5e
Create Date: 2026-09-12

Removes the `person` table that was created outside the Alembic migration
chain (likely from a manual experiment) and has no place in the TalkTribe schema.
Uses IF EXISTS so the migration is safe on fresh CI databases where the table
never existed.
"""

import sqlalchemy as sa
from alembic import op

revision = "66d08b170828"
down_revision = "ff432d6f2a5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IF EXISTS makes this safe on fresh CI DBs where person never existed
    op.execute("DROP TABLE IF EXISTS person")


def downgrade() -> None:
    # Restore the table exactly as it was found in the local dev DB
    op.create_table(
        "person",
        sa.Column("id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column("salary", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("city", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.Column("gender", sa.VARCHAR(length=100), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="person_pkey"),
    )
