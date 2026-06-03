"""Add maintenance reconciliation issues.

Revision ID: 0002_reconciliation_issues
Revises: 0001_maintenance_downtime
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_reconciliation_issues"
down_revision = "0001_maintenance_downtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_reconciliation_issues",
        sa.Column("issue_id", sa.String(length=80), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=True),
        sa.Column("equipment_id", sa.String(length=64), nullable=True),
        sa.Column("issue_type", sa.String(length=160), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("issue_id", name=op.f("pk_maintenance_reconciliation_issues")),
    )
    op.create_index(
        op.f("ix_maintenance_reconciliation_issues_equipment_id"),
        "maintenance_reconciliation_issues",
        ["equipment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_reconciliation_issues_maintenance_request_id"),
        "maintenance_reconciliation_issues",
        ["maintenance_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_maintenance_reconciliation_issues_pipeline_run_id"),
        "maintenance_reconciliation_issues",
        ["pipeline_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_issues_request_status",
        "maintenance_reconciliation_issues",
        ["maintenance_request_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_issues_run_request",
        "maintenance_reconciliation_issues",
        ["pipeline_run_id", "maintenance_request_id"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_issues_type_severity",
        "maintenance_reconciliation_issues",
        ["issue_type", "severity"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reconciliation_issues_type_severity", table_name="maintenance_reconciliation_issues")
    op.drop_index("ix_reconciliation_issues_run_request", table_name="maintenance_reconciliation_issues")
    op.drop_index("ix_reconciliation_issues_request_status", table_name="maintenance_reconciliation_issues")
    op.drop_index(
        op.f("ix_maintenance_reconciliation_issues_pipeline_run_id"),
        table_name="maintenance_reconciliation_issues",
    )
    op.drop_index(
        op.f("ix_maintenance_reconciliation_issues_maintenance_request_id"),
        table_name="maintenance_reconciliation_issues",
    )
    op.drop_index(
        op.f("ix_maintenance_reconciliation_issues_equipment_id"),
        table_name="maintenance_reconciliation_issues",
    )
    op.drop_table("maintenance_reconciliation_issues")
