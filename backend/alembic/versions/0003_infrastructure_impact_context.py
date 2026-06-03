"""add infrastructure impact context

Revision ID: 0003_impact_context
Revises: 0002_infra_recon
Create Date: 2026-06-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_impact_context"
down_revision: Union[str, None] = "0002_infra_recon"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "infrastructure_impact_snapshots",
        sa.Column("impact_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("incident_id", sa.String(length=64), nullable=False),
        sa.Column("asset_id", sa.String(length=64), nullable=False),
        sa.Column("zone_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redundancy_state", sa.String(length=40), nullable=False),
        sa.Column("affected_rack_count", sa.Integer(), nullable=False),
        sa.Column("affected_gpu_count", sa.Integer(), nullable=False),
        sa.Column("estimated_capacity_risk_kw", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("estimated_gpu_capacity_risk_pct", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("thermal_breach_minutes", sa.Integer(), nullable=False),
        sa.Column("power_redundancy_lost", sa.Boolean(), nullable=False),
        sa.Column("cooling_redundancy_lost", sa.Boolean(), nullable=False),
        sa.Column("mitigation_status", sa.String(length=60), nullable=False),
        sa.Column("vendor_eta_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vendor_status", sa.String(length=80), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("telemetry_readings_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["infrastructure_assets.asset_id"]),
        sa.ForeignKeyConstraint(["incident_id"], ["infrastructure_incidents.incident_id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["infrastructure_zones.zone_id"]),
        sa.PrimaryKeyConstraint("impact_snapshot_id"),
    )
    op.create_index(
        "ix_infrastructure_impact_asset_snapshot",
        "infrastructure_impact_snapshots",
        ["asset_id", "snapshot_at"],
    )
    op.create_index(
        "ix_infrastructure_impact_incident_snapshot",
        "infrastructure_impact_snapshots",
        ["incident_id", "snapshot_at"],
    )
    op.create_index(
        "ix_infrastructure_impact_mitigation",
        "infrastructure_impact_snapshots",
        ["mitigation_status"],
    )
    op.create_index(
        "ix_infrastructure_impact_redundancy",
        "infrastructure_impact_snapshots",
        ["redundancy_state"],
    )
    op.create_index(
        "ix_infrastructure_impact_vendor_status",
        "infrastructure_impact_snapshots",
        ["vendor_status"],
    )

    for column_name in [
        "capacity_risk_score",
        "redundancy_risk_score",
        "thermal_risk_score",
        "vendor_eta_risk_score",
        "mitigation_credit_score",
    ]:
        op.add_column(
            "downtime_follow_up_queue",
            sa.Column(
                column_name,
                sa.Numeric(precision=8, scale=2),
                server_default="0",
                nullable=False,
            ),
        )
        op.alter_column("downtime_follow_up_queue", column_name, server_default=None)


def downgrade() -> None:
    for column_name in [
        "mitigation_credit_score",
        "vendor_eta_risk_score",
        "thermal_risk_score",
        "redundancy_risk_score",
        "capacity_risk_score",
    ]:
        op.drop_column("downtime_follow_up_queue", column_name)

    op.drop_index("ix_infrastructure_impact_vendor_status", table_name="infrastructure_impact_snapshots")
    op.drop_index("ix_infrastructure_impact_redundancy", table_name="infrastructure_impact_snapshots")
    op.drop_index("ix_infrastructure_impact_mitigation", table_name="infrastructure_impact_snapshots")
    op.drop_index("ix_infrastructure_impact_incident_snapshot", table_name="infrastructure_impact_snapshots")
    op.drop_index("ix_infrastructure_impact_asset_snapshot", table_name="infrastructure_impact_snapshots")
    op.drop_table("infrastructure_impact_snapshots")
