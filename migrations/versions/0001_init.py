"""init: staff / leaves / plans / assignments / jobs

Revision ID: 0001_init
Revises:
Create Date: 2026-11-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "staff",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("skills", sa.String(200), nullable=False, server_default=""),
        sa.Column("active", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "leaves",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("staff_id", sa.Integer(), nullable=False, index=True),
        sa.Column("start", sa.Date(), nullable=False),
        sa.Column("end", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(120), nullable=False, server_default=""),
    )
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.String(7), nullable=False, index=True),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("month", name="uq_plans_month"),
    )
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.String(7), nullable=False, index=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("staff_id", sa.Integer(), nullable=False, index=True),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("idem_key", sa.String(120), nullable=False),
        sa.Column("payload", sa.String(2000), nullable=False, server_default="{}"),
        sa.Column("state", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_run_at", sa.String(32), nullable=False, index=True),
        sa.Column("created_at", sa.String(32), nullable=False, server_default=""),
        sa.UniqueConstraint("idem_key", name="uq_jobs_idem"),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("assignments")
    op.drop_table("plans")
    op.drop_table("leaves")
    op.drop_table("staff")
