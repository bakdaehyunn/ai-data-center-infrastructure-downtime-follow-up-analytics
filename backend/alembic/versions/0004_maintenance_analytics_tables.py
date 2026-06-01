"""maintenance analytics tables

Revision ID: 0004_maintenance_analytics
Revises: 0003_maintenance_raw_tables
Create Date: 2026-06-01 00:00:00.000000+00:00
"""

from collections.abc import Sequence
from typing import Optional, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_maintenance_analytics"
down_revision: Optional[str] = "0003_maintenance_raw_tables"
branch_labels: Optional[Union[str, Sequence[str]]] = None
depends_on: Optional[Union[str, Sequence[str]]] = None


def upgrade() -> None:
    op.create_table(
        "maintenance_current_status",
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("current_stage", sa.String(length=80), nullable=False),
        sa.Column("current_status", sa.String(length=60), nullable=False),
        sa.Column("stage_entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hours_in_current_stage", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_delayed", sa.Boolean(), nullable=False),
        sa.Column("delay_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("needed_by_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("priority_level", sa.String(length=20), nullable=False),
        sa.Column("business_impact", sa.String(length=100), nullable=False),
        sa.Column("next_owner_type", sa.String(length=60), nullable=True),
        sa.Column("next_owner_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], name=op.f("fk_maintenance_current_status_equipment_id_equipment")),
        sa.ForeignKeyConstraint(["line_id"], ["production_lines.line_id"], name=op.f("fk_maintenance_current_status_line_id_production_lines")),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_maintenance_current_status_maintenance_request_id_maintenance_requests"),
        ),
        sa.PrimaryKeyConstraint("maintenance_request_id", name=op.f("pk_maintenance_current_status")),
    )
    op.create_index(
        "ix_maintenance_current_status_equipment_line",
        "maintenance_current_status",
        ["equipment_id", "line_id"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_current_status_priority_delay",
        "maintenance_current_status",
        ["priority_level", "delay_hours"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_current_status_stage_delayed",
        "maintenance_current_status",
        ["current_stage", "is_delayed"],
        unique=False,
    )

    op.create_table(
        "maintenance_stage_lead_times",
        sa.Column("lead_time_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("threshold_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_bottleneck", sa.Boolean(), nullable=False),
        sa.Column("delay_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_maintenance_stage_lead_times_maintenance_request_id_maintenance_requests"),
        ),
        sa.PrimaryKeyConstraint("lead_time_id", name=op.f("pk_maintenance_stage_lead_times")),
    )
    op.create_index(
        "ix_maintenance_stage_lead_times_request_stage",
        "maintenance_stage_lead_times",
        ["maintenance_request_id", "stage"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_stage_lead_times_stage_bottleneck",
        "maintenance_stage_lead_times",
        ["stage", "is_bottleneck"],
        unique=False,
    )

    op.create_table(
        "critical_maintenance_queue",
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("priority_rank", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("current_stage", sa.String(length=80), nullable=False),
        sa.Column("equipment_criticality_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("downtime_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("stage_delay_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("production_line_impact_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("needed_by_urgency_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("repeat_failure_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("parts_risk_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("total_priority_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("recommended_action", sa.String(length=240), nullable=False),
        sa.Column("reason_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], name=op.f("fk_critical_maintenance_queue_equipment_id_equipment")),
        sa.ForeignKeyConstraint(["line_id"], ["production_lines.line_id"], name=op.f("fk_critical_maintenance_queue_line_id_production_lines")),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_critical_maintenance_queue_maintenance_request_id_maintenance_requests"),
        ),
        sa.PrimaryKeyConstraint("maintenance_request_id", name=op.f("pk_critical_maintenance_queue")),
    )
    op.create_index("ix_critical_maintenance_queue_rank", "critical_maintenance_queue", ["priority_rank"], unique=False)
    op.create_index("ix_critical_maintenance_queue_score", "critical_maintenance_queue", ["total_priority_score"], unique=False)
    op.create_index("ix_critical_maintenance_queue_stage", "critical_maintenance_queue", ["current_stage"], unique=False)

    op.create_table(
        "maintenance_bottleneck_summary",
        sa.Column("summary_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("summary_date", sa.Date(), nullable=False),
        sa.Column("dimension_type", sa.String(length=40), nullable=False),
        sa.Column("dimension_id", sa.String(length=80), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("delayed_count", sa.Integer(), nullable=False),
        sa.Column("delay_rate", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("avg_duration_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("p90_duration_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_delay_hours", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("summary_id", name=op.f("pk_maintenance_bottleneck_summary")),
    )
    op.create_index(
        "ix_maintenance_bottleneck_summary_date_dimension",
        "maintenance_bottleneck_summary",
        ["summary_date", "dimension_type", "dimension_id"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_bottleneck_summary_stage_delay",
        "maintenance_bottleneck_summary",
        ["stage", "total_delay_hours"],
        unique=False,
    )

    op.create_table(
        "equipment_delay_summary",
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("equipment_name", sa.String(length=200), nullable=False),
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("line_name", sa.String(length=160), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("delayed_request_count", sa.Integer(), nullable=False),
        sa.Column("repeat_failure_count", sa.Integer(), nullable=False),
        sa.Column("total_downtime_hours", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("avg_repair_duration_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("top_failure_mode", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], name=op.f("fk_equipment_delay_summary_equipment_id_equipment")),
        sa.ForeignKeyConstraint(["line_id"], ["production_lines.line_id"], name=op.f("fk_equipment_delay_summary_line_id_production_lines")),
        sa.PrimaryKeyConstraint("equipment_id", name=op.f("pk_equipment_delay_summary")),
    )
    op.create_index("ix_equipment_delay_summary_delayed", "equipment_delay_summary", ["delayed_request_count"], unique=False)
    op.create_index("ix_equipment_delay_summary_downtime", "equipment_delay_summary", ["total_downtime_hours"], unique=False)

    op.create_table(
        "production_line_delay_summary",
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("line_name", sa.String(length=160), nullable=False),
        sa.Column("open_request_count", sa.Integer(), nullable=False),
        sa.Column("delayed_request_count", sa.Integer(), nullable=False),
        sa.Column("critical_equipment_delayed_count", sa.Integer(), nullable=False),
        sa.Column("total_downtime_hours", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("top_bottleneck_stage", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["production_lines.line_id"], name=op.f("fk_production_line_delay_summary_line_id_production_lines")),
        sa.PrimaryKeyConstraint("line_id", name=op.f("pk_production_line_delay_summary")),
    )
    op.create_index("ix_production_line_delay_summary_delayed", "production_line_delay_summary", ["delayed_request_count"], unique=False)
    op.create_index("ix_production_line_delay_summary_downtime", "production_line_delay_summary", ["total_downtime_hours"], unique=False)

    op.create_table(
        "parts_waiting_summary",
        sa.Column("part_id", sa.String(length=64), nullable=False),
        sa.Column("part_name", sa.String(length=200), nullable=False),
        sa.Column("part_category", sa.String(length=80), nullable=False),
        sa.Column("waiting_request_count", sa.Integer(), nullable=False),
        sa.Column("total_wait_hours", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("avg_wait_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("critical_spare", sa.Boolean(), nullable=False),
        sa.Column("stock_status", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["part_id"], ["parts.part_id"], name=op.f("fk_parts_waiting_summary_part_id_parts")),
        sa.PrimaryKeyConstraint("part_id", name=op.f("pk_parts_waiting_summary")),
    )
    op.create_index("ix_parts_waiting_summary_category_stock", "parts_waiting_summary", ["part_category", "stock_status"], unique=False)
    op.create_index("ix_parts_waiting_summary_wait_hours", "parts_waiting_summary", ["total_wait_hours"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_parts_waiting_summary_wait_hours", table_name="parts_waiting_summary")
    op.drop_index("ix_parts_waiting_summary_category_stock", table_name="parts_waiting_summary")
    op.drop_table("parts_waiting_summary")
    op.drop_index("ix_production_line_delay_summary_downtime", table_name="production_line_delay_summary")
    op.drop_index("ix_production_line_delay_summary_delayed", table_name="production_line_delay_summary")
    op.drop_table("production_line_delay_summary")
    op.drop_index("ix_equipment_delay_summary_downtime", table_name="equipment_delay_summary")
    op.drop_index("ix_equipment_delay_summary_delayed", table_name="equipment_delay_summary")
    op.drop_table("equipment_delay_summary")
    op.drop_index("ix_maintenance_bottleneck_summary_stage_delay", table_name="maintenance_bottleneck_summary")
    op.drop_index("ix_maintenance_bottleneck_summary_date_dimension", table_name="maintenance_bottleneck_summary")
    op.drop_table("maintenance_bottleneck_summary")
    op.drop_index("ix_critical_maintenance_queue_stage", table_name="critical_maintenance_queue")
    op.drop_index("ix_critical_maintenance_queue_score", table_name="critical_maintenance_queue")
    op.drop_index("ix_critical_maintenance_queue_rank", table_name="critical_maintenance_queue")
    op.drop_table("critical_maintenance_queue")
    op.drop_index("ix_maintenance_stage_lead_times_stage_bottleneck", table_name="maintenance_stage_lead_times")
    op.drop_index("ix_maintenance_stage_lead_times_request_stage", table_name="maintenance_stage_lead_times")
    op.drop_table("maintenance_stage_lead_times")
    op.drop_index("ix_maintenance_current_status_stage_delayed", table_name="maintenance_current_status")
    op.drop_index("ix_maintenance_current_status_priority_delay", table_name="maintenance_current_status")
    op.drop_index("ix_maintenance_current_status_equipment_line", table_name="maintenance_current_status")
    op.drop_table("maintenance_current_status")
