"""TT-14: add interests and user_interests tables

Revision ID: ff432d6f2a5e
Revises: 3d77b96a2528
Create Date: 2026-09-12

Creates:
  - interests        — predefined catalogue seeded with 14 topics
  - user_interests   — join table (user_id, interest_id) composite PK
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff432d6f2a5e"
down_revision = "3d77b96a2528"
branch_labels = None
depends_on = None

_SEED_INTERESTS = [
    {"id": 1, "name": "Art"},
    {"id": 2, "name": "Books"},
    {"id": 3, "name": "Business"},
    {"id": 4, "name": "Cooking"},
    {"id": 5, "name": "Fashion"},
    {"id": 6, "name": "Fitness"},
    {"id": 7, "name": "Gaming"},
    {"id": 8, "name": "Movies"},
    {"id": 9, "name": "Music"},
    {"id": 10, "name": "Nature"},
    {"id": 11, "name": "Science"},
    {"id": 12, "name": "Sports"},
    {"id": 13, "name": "Technology"},
    {"id": 14, "name": "Travel"},
]


def upgrade() -> None:
    interests_table = op.create_table(
        "interests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_interests_id"), "interests", ["id"], unique=False)

    # Seed the predefined catalogue
    op.bulk_insert(interests_table, _SEED_INTERESTS)

    op.create_table(
        "user_interests",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("interest_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["interest_id"], ["interests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "interest_id"),
    )
    op.create_index(
        op.f("ix_user_interests_user_id"), "user_interests", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_interests_user_id"), table_name="user_interests")
    op.drop_table("user_interests")
    op.drop_index(op.f("ix_interests_id"), table_name="interests")
    op.drop_table("interests")
