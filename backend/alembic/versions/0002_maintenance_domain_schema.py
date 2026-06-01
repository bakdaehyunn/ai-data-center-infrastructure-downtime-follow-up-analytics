"""maintenance domain schema

Revision ID: 0002_maintenance_domain
Revises: 0001_initial_schema
Create Date: 2026-06-01 00:00:00.000000+00:00
"""

from collections.abc import Sequence
from typing import Optional, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_maintenance_domain"
down_revision: Optional[str] = "0001_initial_schema"
branch_labels: Optional[Union[str, Sequence[str]]] = None
depends_on: Optional[Union[str, Sequence[str]]] = None


def upgrade() -> None:
    op.create_table(
        "production_lines",
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("line_code", sa.String(length=80), nullable=False),
        sa.Column("line_name", sa.String(length=160), nullable=False),
        sa.Column("plant_area", sa.String(length=120), nullable=False),
        sa.Column("line_priority", sa.String(length=40), nullable=False),
        sa.Column("current_status", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("line_id", name=op.f("pk_production_lines")),
        sa.UniqueConstraint("line_code", name="uq_production_lines_line_code"),
    )
    op.create_index(
        "ix_production_lines_priority_status",
        "production_lines",
        ["line_priority", "current_status"],
        unique=False,
    )

    op.create_table(
        "technicians",
        sa.Column("technician_id", sa.String(length=64), nullable=False),
        sa.Column("technician_name", sa.String(length=160), nullable=False),
        sa.Column("team_name", sa.String(length=120), nullable=False),
        sa.Column("skill_group", sa.String(length=80), nullable=False),
        sa.Column("shift", sa.String(length=40), nullable=False),
        sa.Column("active_status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("technician_id", name=op.f("pk_technicians")),
    )
    op.create_index("ix_technicians_skill_status", "technicians", ["skill_group", "active_status"], unique=False)
    op.create_index("ix_technicians_team_shift", "technicians", ["team_name", "shift"], unique=False)

    op.create_table(
        "parts",
        sa.Column("part_id", sa.String(length=64), nullable=False),
        sa.Column("part_number", sa.String(length=80), nullable=False),
        sa.Column("part_name", sa.String(length=200), nullable=False),
        sa.Column("part_category", sa.String(length=80), nullable=False),
        sa.Column("stock_status", sa.String(length=60), nullable=False),
        sa.Column("lead_time_days", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("critical_spare", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("part_id", name=op.f("pk_parts")),
        sa.UniqueConstraint("part_number", name="uq_parts_part_number"),
    )
    op.create_index("ix_parts_category_stock", "parts", ["part_category", "stock_status"], unique=False)
    op.create_index("ix_parts_critical_spare", "parts", ["critical_spare"], unique=False)

    op.create_table(
        "equipment",
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("equipment_code", sa.String(length=80), nullable=False),
        sa.Column("equipment_name", sa.String(length=200), nullable=False),
        sa.Column("equipment_type", sa.String(length=80), nullable=False),
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("criticality_level", sa.String(length=20), nullable=False),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("manufacturer", sa.String(length=120), nullable=False),
        sa.Column("model_number", sa.String(length=120), nullable=False),
        sa.Column("current_status", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["line_id"],
            ["production_lines.line_id"],
            name=op.f("fk_equipment_line_id_production_lines"),
        ),
        sa.PrimaryKeyConstraint("equipment_id", name=op.f("pk_equipment")),
        sa.UniqueConstraint("equipment_code", name="uq_equipment_equipment_code"),
    )
    op.create_index("ix_equipment_line_criticality", "equipment", ["line_id", "criticality_level"], unique=False)
    op.create_index("ix_equipment_type_status", "equipment", ["equipment_type", "current_status"], unique=False)

    op.create_table(
        "maintenance_requests",
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("request_number", sa.String(length=80), nullable=False),
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("line_id", sa.String(length=64), nullable=False),
        sa.Column("request_title", sa.String(length=240), nullable=False),
        sa.Column("request_type", sa.String(length=80), nullable=False),
        sa.Column("priority_level", sa.String(length=20), nullable=False),
        sa.Column("failure_mode", sa.String(length=80), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("needed_by_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_stage", sa.String(length=80), nullable=False),
        sa.Column("current_status", sa.String(length=60), nullable=False),
        sa.Column("business_impact", sa.String(length=100), nullable=False),
        sa.Column("estimated_downtime_hours", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("actual_downtime_hours", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], name=op.f("fk_maintenance_requests_equipment_id_equipment")),
        sa.ForeignKeyConstraint(["line_id"], ["production_lines.line_id"], name=op.f("fk_maintenance_requests_line_id_production_lines")),
        sa.PrimaryKeyConstraint("maintenance_request_id", name=op.f("pk_maintenance_requests")),
        sa.UniqueConstraint("request_number", name="uq_maintenance_requests_request_number"),
    )
    op.create_index(
        "ix_maintenance_requests_equipment_status",
        "maintenance_requests",
        ["equipment_id", "current_status"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_requests_line_stage",
        "maintenance_requests",
        ["line_id", "current_stage"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_requests_priority_needed",
        "maintenance_requests",
        ["priority_level", "needed_by_at"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_requests_type_failure",
        "maintenance_requests",
        ["request_type", "failure_mode"],
        unique=False,
    )

    op.create_table(
        "maintenance_stage_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("event_status", sa.String(length=60), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_type", sa.String(length=60), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("reason_code", sa.String(length=80), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_maintenance_stage_events_maintenance_request_id_maintenance_requests"),
        ),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk_maintenance_stage_events")),
    )
    op.create_index(
        "ix_maintenance_stage_events_request_time",
        "maintenance_stage_events",
        ["maintenance_request_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_stage_events_stage_time",
        "maintenance_stage_events",
        ["stage", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_stage_events_type_status",
        "maintenance_stage_events",
        ["event_type", "event_status"],
        unique=False,
    )

    op.create_table(
        "maintenance_work_orders",
        sa.Column("work_order_id", sa.String(length=64), nullable=False),
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("assigned_team", sa.String(length=120), nullable=False),
        sa.Column("assigned_technician_id", sa.String(length=64), nullable=True),
        sa.Column("work_order_status", sa.String(length=60), nullable=False),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("required_part_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_technician_id"],
            ["technicians.technician_id"],
            name=op.f("fk_maintenance_work_orders_assigned_technician_id_technicians"),
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_maintenance_work_orders_maintenance_request_id_maintenance_requests"),
        ),
        sa.ForeignKeyConstraint(["required_part_id"], ["parts.part_id"], name=op.f("fk_maintenance_work_orders_required_part_id_parts")),
        sa.PrimaryKeyConstraint("work_order_id", name=op.f("pk_maintenance_work_orders")),
    )
    op.create_index(
        "ix_maintenance_work_orders_part_status",
        "maintenance_work_orders",
        ["required_part_id", "work_order_status"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_work_orders_request_status",
        "maintenance_work_orders",
        ["maintenance_request_id", "work_order_status"],
        unique=False,
    )
    op.create_index(
        "ix_maintenance_work_orders_team_status",
        "maintenance_work_orders",
        ["assigned_team", "work_order_status"],
        unique=False,
    )

    op.create_table(
        "inspection_results",
        sa.Column("inspection_id", sa.String(length=64), nullable=False),
        sa.Column("maintenance_request_id", sa.String(length=64), nullable=False),
        sa.Column("inspection_status", sa.String(length=60), nullable=False),
        sa.Column("inspector_id", sa.String(length=64), nullable=True),
        sa.Column("inspection_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inspection_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["inspector_id"], ["technicians.technician_id"], name=op.f("fk_inspection_results_inspector_id_technicians")),
        sa.ForeignKeyConstraint(
            ["maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_inspection_results_maintenance_request_id_maintenance_requests"),
        ),
        sa.PrimaryKeyConstraint("inspection_id", name=op.f("pk_inspection_results")),
    )
    op.create_index(
        "ix_inspection_results_inspector_status",
        "inspection_results",
        ["inspector_id", "inspection_status"],
        unique=False,
    )
    op.create_index(
        "ix_inspection_results_request_status",
        "inspection_results",
        ["maintenance_request_id", "inspection_status"],
        unique=False,
    )

    op.create_table(
        "sensor_alerts",
        sa.Column("sensor_alert_id", sa.String(length=64), nullable=False),
        sa.Column("equipment_id", sa.String(length=64), nullable=False),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linked_maintenance_request_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.equipment_id"], name=op.f("fk_sensor_alerts_equipment_id_equipment")),
        sa.ForeignKeyConstraint(
            ["linked_maintenance_request_id"],
            ["maintenance_requests.maintenance_request_id"],
            name=op.f("fk_sensor_alerts_linked_maintenance_request_id_maintenance_requests"),
        ),
        sa.PrimaryKeyConstraint("sensor_alert_id", name=op.f("pk_sensor_alerts")),
    )
    op.create_index(
        "ix_sensor_alerts_equipment_triggered",
        "sensor_alerts",
        ["equipment_id", "triggered_at"],
        unique=False,
    )
    op.create_index(
        "ix_sensor_alerts_linked_request",
        "sensor_alerts",
        ["linked_maintenance_request_id"],
        unique=False,
    )
    op.create_index(
        "ix_sensor_alerts_severity_status",
        "sensor_alerts",
        ["severity", "resolved_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_alerts_severity_status", table_name="sensor_alerts")
    op.drop_index("ix_sensor_alerts_linked_request", table_name="sensor_alerts")
    op.drop_index("ix_sensor_alerts_equipment_triggered", table_name="sensor_alerts")
    op.drop_table("sensor_alerts")
    op.drop_index("ix_inspection_results_request_status", table_name="inspection_results")
    op.drop_index("ix_inspection_results_inspector_status", table_name="inspection_results")
    op.drop_table("inspection_results")
    op.drop_index("ix_maintenance_work_orders_team_status", table_name="maintenance_work_orders")
    op.drop_index("ix_maintenance_work_orders_request_status", table_name="maintenance_work_orders")
    op.drop_index("ix_maintenance_work_orders_part_status", table_name="maintenance_work_orders")
    op.drop_table("maintenance_work_orders")
    op.drop_index("ix_maintenance_stage_events_type_status", table_name="maintenance_stage_events")
    op.drop_index("ix_maintenance_stage_events_stage_time", table_name="maintenance_stage_events")
    op.drop_index("ix_maintenance_stage_events_request_time", table_name="maintenance_stage_events")
    op.drop_table("maintenance_stage_events")
    op.drop_index("ix_maintenance_requests_type_failure", table_name="maintenance_requests")
    op.drop_index("ix_maintenance_requests_priority_needed", table_name="maintenance_requests")
    op.drop_index("ix_maintenance_requests_line_stage", table_name="maintenance_requests")
    op.drop_index("ix_maintenance_requests_equipment_status", table_name="maintenance_requests")
    op.drop_table("maintenance_requests")
    op.drop_index("ix_equipment_type_status", table_name="equipment")
    op.drop_index("ix_equipment_line_criticality", table_name="equipment")
    op.drop_table("equipment")
    op.drop_index("ix_parts_critical_spare", table_name="parts")
    op.drop_index("ix_parts_category_stock", table_name="parts")
    op.drop_table("parts")
    op.drop_index("ix_technicians_team_shift", table_name="technicians")
    op.drop_index("ix_technicians_skill_status", table_name="technicians")
    op.drop_table("technicians")
    op.drop_index("ix_production_lines_priority_status", table_name="production_lines")
    op.drop_table("production_lines")
