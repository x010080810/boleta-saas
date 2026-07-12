"""add system_settings table

Revision ID: 001
Revises:
Create Date: 2026-07-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, default=""),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
