"""Create the initial database migration baseline.

Revision ID: 001_baseline
Revises:
Create Date: 2026-09-06
"""

from collections.abc import Sequence

from alembic import op


revision: str = "001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
