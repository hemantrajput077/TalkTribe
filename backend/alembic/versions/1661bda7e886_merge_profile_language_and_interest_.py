"""merge profile language and interest migration heads

Revision ID: 1661bda7e886
Revises: 66d08b170828, d8e9f0a1b2c7
Create Date: 2026-09-13 17:35:26.508435

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1661bda7e886'
down_revision = ('66d08b170828', 'd8e9f0a1b2c7')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
