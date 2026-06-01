"""maintenance raw source tables

Revision ID: 0003_maintenance_raw_tables
Revises: 0002_maintenance_domain
Create Date: 2026-06-01 00:00:00.000000+00:00
"""

from collections.abc import Sequence
from typing import Optional, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_maintenance_raw_tables"
down_revision: Optional[str] = "0002_maintenance_domain"
branch_labels: Optional[Union[str, Sequence[str]]] = None
depends_on: Optional[Union[str, Sequence[str]]] = None


RAW_TABLES = [
    (
        "raw_maintenance_requests",
        "uq_raw_maintenance_request_source_record",
        "ix_raw_maintenance_request_pipeline_source",
    ),
    (
        "raw_maintenance_stage_events",
        "uq_raw_maintenance_stage_event_source_record",
        "ix_raw_maintenance_stage_event_pipeline_source",
    ),
    (
        "raw_maintenance_work_orders",
        "uq_raw_maintenance_work_order_source_record",
        "ix_raw_maintenance_work_order_pipeline_source",
    ),
    (
        "raw_inspection_results",
        "uq_raw_inspection_result_source_record",
        "ix_raw_inspection_result_pipeline_source",
    ),
    (
        "raw_sensor_alerts",
        "uq_raw_sensor_alert_source_record",
        "ix_raw_sensor_alert_pipeline_source",
    ),
]


def upgrade() -> None:
    for table_name, unique_name, source_index_name in RAW_TABLES:
        op.create_table(
            table_name,
            sa.Column("raw_id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("source_record_id", sa.String(length=120), nullable=False),
            sa.Column("source_system", sa.String(length=80), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("pipeline_run_id", sa.String(length=64), nullable=False),
            sa.PrimaryKeyConstraint("raw_id", name=op.f(f"pk_{table_name}")),
            sa.UniqueConstraint("source_system", "source_record_id", name=unique_name),
        )
        op.create_index(op.f(f"ix_{table_name}_pipeline_run_id"), table_name, ["pipeline_run_id"], unique=False)
        op.create_index(source_index_name, table_name, ["pipeline_run_id", "source_system"], unique=False)


def downgrade() -> None:
    for table_name, _, source_index_name in reversed(RAW_TABLES):
        op.drop_index(source_index_name, table_name=table_name)
        op.drop_index(op.f(f"ix_{table_name}_pipeline_run_id"), table_name=table_name)
        op.drop_table(table_name)
