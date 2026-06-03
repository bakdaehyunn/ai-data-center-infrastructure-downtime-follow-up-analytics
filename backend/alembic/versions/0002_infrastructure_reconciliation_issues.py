"""Add infrastructure reconciliation issues.

Revision ID: 0002_infra_recon
Revises: 0001_ai_infra
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_infra_recon"
down_revision = "0001_ai_infra"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "infrastructure_reconciliation_issues",
        sa.Column("issue_id", sa.String(length=80), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
        sa.Column("incident_id", sa.String(length=64), nullable=True),
        sa.Column("asset_id", sa.String(length=64), nullable=True),
        sa.Column("issue_type", sa.String(length=160), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("issue_id", name=op.f("pk_infrastructure_reconciliation_issues")),
    )
    op.create_index(
        op.f("ix_infrastructure_reconciliation_issues_asset_id"),
        "infrastructure_reconciliation_issues",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_infrastructure_reconciliation_issues_incident_id"),
        "infrastructure_reconciliation_issues",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_infrastructure_reconciliation_issues_pipeline_run_id"),
        "infrastructure_reconciliation_issues",
        ["pipeline_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_issues_request_status",
        "infrastructure_reconciliation_issues",
        ["incident_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_issues_run_request",
        "infrastructure_reconciliation_issues",
        ["pipeline_run_id", "incident_id"],
        unique=False,
    )
    op.create_index(
        "ix_reconciliation_issues_type_severity",
        "infrastructure_reconciliation_issues",
        ["issue_type", "severity"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reconciliation_issues_type_severity", table_name="infrastructure_reconciliation_issues")
    op.drop_index("ix_reconciliation_issues_run_request", table_name="infrastructure_reconciliation_issues")
    op.drop_index("ix_reconciliation_issues_request_status", table_name="infrastructure_reconciliation_issues")
    op.drop_index(
        op.f("ix_infrastructure_reconciliation_issues_pipeline_run_id"),
        table_name="infrastructure_reconciliation_issues",
    )
    op.drop_index(
        op.f("ix_infrastructure_reconciliation_issues_incident_id"),
        table_name="infrastructure_reconciliation_issues",
    )
    op.drop_index(
        op.f("ix_infrastructure_reconciliation_issues_asset_id"),
        table_name="infrastructure_reconciliation_issues",
    )
    op.drop_table("infrastructure_reconciliation_issues")
