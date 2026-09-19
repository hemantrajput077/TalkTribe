"""TT-18: add custom-interest columns to interests table

Revision ID: e5f6a7b8c9d0
Revises: 1661bda7e886
Create Date: 2026-09-19

Adds four columns to interests:
  - is_predefined       Boolean NOT NULL DEFAULT TRUE
  - created_by_user_id  Integer FK→users.id  nullable (NULL for predefined rows)
  - is_active           Boolean NOT NULL DEFAULT TRUE
  - created_at          TimestampTZ NOT NULL DEFAULT now()

Existing seeded rows are backfilled via server defaults — all predefined,
no user owner, active, created_at set to migration run time.
"""

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "1661bda7e886"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interests",
        sa.Column("is_predefined", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "interests",
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "interests",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "interests",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_foreign_key(
        "fk_interests_created_by_user_id",
        "interests",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Advance the sequence past the explicitly-seeded rows (IDs 1-14).
    # bulk_insert uses explicit IDs, which do not advance the PostgreSQL
    # SERIAL sequence. Without this, the first custom interest insert would
    # call nextval() → 1, colliding with the "Art" row.
    op.execute(
        "SELECT setval("
        "  pg_get_serial_sequence('interests', 'id'),"
        "  COALESCE((SELECT MAX(id) FROM interests), 0)"
        ")"
    )


def downgrade() -> None:
    op.drop_constraint("fk_interests_created_by_user_id", "interests", type_="foreignkey")
    op.drop_column("interests", "created_at")
    op.drop_column("interests", "is_active")
    op.drop_column("interests", "created_by_user_id")
    op.drop_column("interests", "is_predefined")
