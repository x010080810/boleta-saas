"""add is_active to user_company_assignments

Revision ID: 002
Revises: 001
Create Date: 2026-07-11

"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_company_assignments",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade():
    op.drop_column("user_company_assignments", "is_active")
