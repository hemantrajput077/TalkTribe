"""add_role_and_account_status_to_users

Revision ID: f2a9b3c7d1e5
Revises: b85cffda6fd3
Create Date: 2026-08-31 10:00:00.000000

AUTH-04: Replace is_verified boolean with account_status enum; add role enum.
Back-fill: rows where is_verified = TRUE become ACTIVE; all others stay PENDING_VERIFICATION.
"""

import sqlalchemy as sa
from alembic import op

revision = "f2a9b3c7d1e5"
down_revision = "b85cffda6fd3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the two PostgreSQL ENUM types.
    # PostgreSQL has no CREATE TYPE IF NOT EXISTS — the DO block with exception
    # handling is the idiomatic workaround for idempotent type creation.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('USER', 'ADMIN');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE accountstatus AS ENUM (
                'PENDING_VERIFICATION', 'ACTIVE', 'SUSPENDED', 'BLOCKED', 'DELETED'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Add role — server_default required so existing rows get a value immediately
    # (PostgreSQL rejects ADD COLUMN NOT NULL without a default when the table has rows).
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("USER", "ADMIN", name="userrole", create_type=False),
            nullable=False,
            server_default="USER",
        ),
    )

    # Add account_status with the same server_default pattern.
    op.add_column(
        "users",
        sa.Column(
            "account_status",
            sa.Enum(
                "PENDING_VERIFICATION",
                "ACTIVE",
                "SUSPENDED",
                "BLOCKED",
                "DELETED",
                name="accountstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING_VERIFICATION",
        ),
    )

    # Back-fill: anyone who had already verified their email becomes ACTIVE.
    op.execute("UPDATE users SET account_status = 'ACTIVE' WHERE is_verified = TRUE")

    # Drop is_verified — account_status is now the single source of truth.
    op.drop_column("users", "is_verified")


def downgrade() -> None:
    # Restore is_verified as a boolean column.
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )

    # Back-fill: ACTIVE users were verified.
    op.execute("UPDATE users SET is_verified = TRUE WHERE account_status = 'ACTIVE'")

    op.drop_column("users", "account_status")
    op.drop_column("users", "role")

    op.execute("DROP TYPE IF EXISTS accountstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
