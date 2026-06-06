"""add infrastructure dependency topology

Revision ID: 0004_infra_topology
Revises: 0003_impact_context
Create Date: 2026-06-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_infra_topology"
down_revision: Union[str, None] = "0003_impact_context"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "infrastructure_dependencies",
        sa.Column("dependency_id", sa.String(length=64), nullable=False),
        sa.Column("dependent_asset_id", sa.String(length=64), nullable=False),
        sa.Column("dependency_asset_id", sa.String(length=64), nullable=False),
        sa.Column("dependency_type", sa.String(length=60), nullable=False),
        sa.Column("dependency_role", sa.String(length=40), nullable=False),
        sa.Column("impact_scope", sa.String(length=80), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["dependent_asset_id"], ["infrastructure_assets.asset_id"]),
        sa.ForeignKeyConstraint(["dependency_asset_id"], ["infrastructure_assets.asset_id"]),
        sa.PrimaryKeyConstraint("dependency_id"),
        sa.UniqueConstraint(
            "dependent_asset_id",
            "dependency_asset_id",
            "dependency_type",
            name="uq_infrastructure_dependency_edge",
        ),
    )
    op.create_index(
        "ix_infrastructure_dependencies_dependent",
        "infrastructure_dependencies",
        ["dependent_asset_id", "dependency_type"],
    )
    op.create_index(
        "ix_infrastructure_dependencies_dependency",
        "infrastructure_dependencies",
        ["dependency_asset_id", "dependency_type"],
    )
    op.create_index(
        "ix_infrastructure_dependencies_type_role",
        "infrastructure_dependencies",
        ["dependency_type", "dependency_role"],
    )


def downgrade() -> None:
    op.drop_index("ix_infrastructure_dependencies_type_role", table_name="infrastructure_dependencies")
    op.drop_index("ix_infrastructure_dependencies_dependency", table_name="infrastructure_dependencies")
    op.drop_index("ix_infrastructure_dependencies_dependent", table_name="infrastructure_dependencies")
    op.drop_table("infrastructure_dependencies")
