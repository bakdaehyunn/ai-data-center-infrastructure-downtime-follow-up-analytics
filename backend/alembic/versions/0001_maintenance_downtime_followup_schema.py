"""Maintenance downtime follow-up clean baseline.

Revision ID: 0001_maintenance_downtime
Revises:
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_maintenance_downtime"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Explicit clean baseline generated from the approved maintenance-only metadata.
    op.create_table('data_quality_check_results',
    sa.Column('check_result_id', sa.String(length=64), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.Column('check_name', sa.String(length=160), nullable=False),
    sa.Column('target_table', sa.String(length=120), nullable=False),
    sa.Column('severity', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('failed_row_count', sa.Integer(), nullable=False),
    sa.Column('sample_failed_keys', sa.JSON(), nullable=True),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('check_result_id', name=op.f('pk_data_quality_check_results'))
    )
    op.create_index(op.f('ix_data_quality_check_results_pipeline_run_id'), 'data_quality_check_results', ['pipeline_run_id'], unique=False)
    op.create_index('ix_dq_results_run_status', 'data_quality_check_results', ['pipeline_run_id', 'status'], unique=False)
    op.create_index('ix_dq_results_severity', 'data_quality_check_results', ['severity'], unique=False)
    op.create_index('ix_dq_results_target_table', 'data_quality_check_results', ['target_table'], unique=False)
    op.create_table('maintenance_bottleneck_summary',
    sa.Column('summary_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('summary_date', sa.Date(), nullable=False),
    sa.Column('dimension_type', sa.String(length=40), nullable=False),
    sa.Column('dimension_id', sa.String(length=80), nullable=False),
    sa.Column('stage', sa.String(length=80), nullable=False),
    sa.Column('request_count', sa.Integer(), nullable=False),
    sa.Column('delayed_count', sa.Integer(), nullable=False),
    sa.Column('delay_rate', sa.Numeric(precision=6, scale=4), nullable=False),
    sa.Column('avg_duration_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('p90_duration_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('total_delay_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('summary_id', name=op.f('pk_maintenance_bottleneck_summary'))
    )
    op.create_index('ix_maintenance_bottleneck_summary_date_dimension', 'maintenance_bottleneck_summary', ['summary_date', 'dimension_type', 'dimension_id'], unique=False)
    op.create_index('ix_maintenance_bottleneck_summary_stage_delay', 'maintenance_bottleneck_summary', ['stage', 'total_delay_hours'], unique=False)
    op.create_table('parts',
    sa.Column('part_id', sa.String(length=64), nullable=False),
    sa.Column('part_number', sa.String(length=80), nullable=False),
    sa.Column('part_name', sa.String(length=200), nullable=False),
    sa.Column('part_category', sa.String(length=80), nullable=False),
    sa.Column('stock_status', sa.String(length=60), nullable=False),
    sa.Column('lead_time_days', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('critical_spare', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('part_id', name=op.f('pk_parts')),
    sa.UniqueConstraint('part_number', name='uq_parts_part_number')
    )
    op.create_index('ix_parts_category_stock', 'parts', ['part_category', 'stock_status'], unique=False)
    op.create_index('ix_parts_critical_spare', 'parts', ['critical_spare'], unique=False)
    op.create_table('pipeline_runs',
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.Column('pipeline_name', sa.String(length=120), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('rows_extracted', sa.Integer(), nullable=False),
    sa.Column('rows_loaded', sa.Integer(), nullable=False),
    sa.Column('rows_rejected', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('pipeline_run_id', name=op.f('pk_pipeline_runs'))
    )
    op.create_index('ix_pipeline_runs_name_started', 'pipeline_runs', ['pipeline_name', 'started_at'], unique=False)
    op.create_index('ix_pipeline_runs_status', 'pipeline_runs', ['status'], unique=False)
    op.create_table('production_lines',
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('line_code', sa.String(length=80), nullable=False),
    sa.Column('line_name', sa.String(length=160), nullable=False),
    sa.Column('plant_area', sa.String(length=120), nullable=False),
    sa.Column('line_priority', sa.String(length=40), nullable=False),
    sa.Column('current_status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('line_id', name=op.f('pk_production_lines')),
    sa.UniqueConstraint('line_code', name='uq_production_lines_line_code')
    )
    op.create_index('ix_production_lines_priority_status', 'production_lines', ['line_priority', 'current_status'], unique=False)
    op.create_table('raw_inspection_results',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_inspection_results')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_inspection_result_source_record')
    )
    op.create_index('ix_raw_inspection_result_pipeline_source', 'raw_inspection_results', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_inspection_results_pipeline_run_id'), 'raw_inspection_results', ['pipeline_run_id'], unique=False)
    op.create_table('raw_maintenance_requests',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_maintenance_requests')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_maintenance_request_source_record')
    )
    op.create_index('ix_raw_maintenance_request_pipeline_source', 'raw_maintenance_requests', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_maintenance_requests_pipeline_run_id'), 'raw_maintenance_requests', ['pipeline_run_id'], unique=False)
    op.create_table('raw_maintenance_stage_events',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_maintenance_stage_events')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_maintenance_stage_event_source_record')
    )
    op.create_index('ix_raw_maintenance_stage_event_pipeline_source', 'raw_maintenance_stage_events', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_maintenance_stage_events_pipeline_run_id'), 'raw_maintenance_stage_events', ['pipeline_run_id'], unique=False)
    op.create_table('raw_maintenance_work_orders',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_maintenance_work_orders')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_maintenance_work_order_source_record')
    )
    op.create_index('ix_raw_maintenance_work_order_pipeline_source', 'raw_maintenance_work_orders', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_maintenance_work_orders_pipeline_run_id'), 'raw_maintenance_work_orders', ['pipeline_run_id'], unique=False)
    op.create_table('raw_sensor_alerts',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_sensor_alerts')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_sensor_alert_source_record')
    )
    op.create_index('ix_raw_sensor_alert_pipeline_source', 'raw_sensor_alerts', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_sensor_alerts_pipeline_run_id'), 'raw_sensor_alerts', ['pipeline_run_id'], unique=False)
    op.create_table('technicians',
    sa.Column('technician_id', sa.String(length=64), nullable=False),
    sa.Column('technician_name', sa.String(length=160), nullable=False),
    sa.Column('team_name', sa.String(length=120), nullable=False),
    sa.Column('skill_group', sa.String(length=80), nullable=False),
    sa.Column('shift', sa.String(length=40), nullable=False),
    sa.Column('active_status', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('technician_id', name=op.f('pk_technicians'))
    )
    op.create_index('ix_technicians_skill_status', 'technicians', ['skill_group', 'active_status'], unique=False)
    op.create_index('ix_technicians_team_shift', 'technicians', ['team_name', 'shift'], unique=False)
    op.create_table('equipment',
    sa.Column('equipment_id', sa.String(length=64), nullable=False),
    sa.Column('equipment_code', sa.String(length=80), nullable=False),
    sa.Column('equipment_name', sa.String(length=200), nullable=False),
    sa.Column('equipment_type', sa.String(length=80), nullable=False),
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('criticality_level', sa.String(length=20), nullable=False),
    sa.Column('installed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('manufacturer', sa.String(length=120), nullable=False),
    sa.Column('model_number', sa.String(length=120), nullable=False),
    sa.Column('current_status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['line_id'], ['production_lines.line_id'], name=op.f('fk_equipment_line_id_production_lines')),
    sa.PrimaryKeyConstraint('equipment_id', name=op.f('pk_equipment')),
    sa.UniqueConstraint('equipment_code', name='uq_equipment_equipment_code')
    )
    op.create_index('ix_equipment_line_criticality', 'equipment', ['line_id', 'criticality_level'], unique=False)
    op.create_index('ix_equipment_type_status', 'equipment', ['equipment_type', 'current_status'], unique=False)
    op.create_table('parts_waiting_summary',
    sa.Column('part_id', sa.String(length=64), nullable=False),
    sa.Column('part_name', sa.String(length=200), nullable=False),
    sa.Column('part_category', sa.String(length=80), nullable=False),
    sa.Column('waiting_request_count', sa.Integer(), nullable=False),
    sa.Column('total_wait_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('avg_wait_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('critical_spare', sa.Boolean(), nullable=False),
    sa.Column('stock_status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['part_id'], ['parts.part_id'], name=op.f('fk_parts_waiting_summary_part_id_parts')),
    sa.PrimaryKeyConstraint('part_id', name=op.f('pk_parts_waiting_summary'))
    )
    op.create_index('ix_parts_waiting_summary_category_stock', 'parts_waiting_summary', ['part_category', 'stock_status'], unique=False)
    op.create_index('ix_parts_waiting_summary_wait_hours', 'parts_waiting_summary', ['total_wait_hours'], unique=False)
    op.create_table('production_line_delay_summary',
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('line_name', sa.String(length=160), nullable=False),
    sa.Column('open_request_count', sa.Integer(), nullable=False),
    sa.Column('delayed_request_count', sa.Integer(), nullable=False),
    sa.Column('critical_equipment_delayed_count', sa.Integer(), nullable=False),
    sa.Column('total_downtime_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('top_bottleneck_stage', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['line_id'], ['production_lines.line_id'], name=op.f('fk_production_line_delay_summary_line_id_production_lines')),
    sa.PrimaryKeyConstraint('line_id', name=op.f('pk_production_line_delay_summary'))
    )
    op.create_index('ix_production_line_delay_summary_delayed', 'production_line_delay_summary', ['delayed_request_count'], unique=False)
    op.create_index('ix_production_line_delay_summary_downtime', 'production_line_delay_summary', ['total_downtime_hours'], unique=False)
    op.create_table('equipment_delay_summary',
    sa.Column('equipment_id', sa.String(length=64), nullable=False),
    sa.Column('equipment_name', sa.String(length=200), nullable=False),
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('line_name', sa.String(length=160), nullable=False),
    sa.Column('request_count', sa.Integer(), nullable=False),
    sa.Column('delayed_request_count', sa.Integer(), nullable=False),
    sa.Column('repeat_failure_count', sa.Integer(), nullable=False),
    sa.Column('total_downtime_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('avg_repair_duration_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('top_failure_mode', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.equipment_id'], name=op.f('fk_equipment_delay_summary_equipment_id_equipment')),
    sa.ForeignKeyConstraint(['line_id'], ['production_lines.line_id'], name=op.f('fk_equipment_delay_summary_line_id_production_lines')),
    sa.PrimaryKeyConstraint('equipment_id', name=op.f('pk_equipment_delay_summary'))
    )
    op.create_index('ix_equipment_delay_summary_delayed', 'equipment_delay_summary', ['delayed_request_count'], unique=False)
    op.create_index('ix_equipment_delay_summary_downtime', 'equipment_delay_summary', ['total_downtime_hours'], unique=False)
    op.create_table('maintenance_requests',
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('request_number', sa.String(length=80), nullable=False),
    sa.Column('equipment_id', sa.String(length=64), nullable=False),
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('request_title', sa.String(length=240), nullable=False),
    sa.Column('request_type', sa.String(length=80), nullable=False),
    sa.Column('priority_level', sa.String(length=20), nullable=False),
    sa.Column('failure_mode', sa.String(length=80), nullable=False),
    sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('needed_by_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('current_stage', sa.String(length=80), nullable=False),
    sa.Column('current_status', sa.String(length=60), nullable=False),
    sa.Column('business_impact', sa.String(length=100), nullable=False),
    sa.Column('estimated_downtime_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('actual_downtime_hours', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.equipment_id'], name=op.f('fk_maintenance_requests_equipment_id_equipment')),
    sa.ForeignKeyConstraint(['line_id'], ['production_lines.line_id'], name=op.f('fk_maintenance_requests_line_id_production_lines')),
    sa.PrimaryKeyConstraint('maintenance_request_id', name=op.f('pk_maintenance_requests')),
    sa.UniqueConstraint('request_number', name='uq_maintenance_requests_request_number')
    )
    op.create_index('ix_maintenance_requests_equipment_status', 'maintenance_requests', ['equipment_id', 'current_status'], unique=False)
    op.create_index('ix_maintenance_requests_line_stage', 'maintenance_requests', ['line_id', 'current_stage'], unique=False)
    op.create_index('ix_maintenance_requests_priority_needed', 'maintenance_requests', ['priority_level', 'needed_by_at'], unique=False)
    op.create_index('ix_maintenance_requests_type_failure', 'maintenance_requests', ['request_type', 'failure_mode'], unique=False)
    op.create_table('downtime_follow_up_queue',
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('priority_rank', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.String(length=64), nullable=False),
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('current_stage', sa.String(length=80), nullable=False),
    sa.Column('equipment_criticality_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('downtime_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('stage_delay_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('production_line_impact_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('needed_by_urgency_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('repeat_failure_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('parts_risk_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('total_priority_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('recommended_action', sa.String(length=240), nullable=False),
    sa.Column('reason_summary', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.equipment_id'], name=op.f('fk_downtime_follow_up_queue_equipment_id_equipment')),
    sa.ForeignKeyConstraint(['line_id'], ['production_lines.line_id'], name=op.f('fk_downtime_follow_up_queue_line_id_production_lines')),
    sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_downtime_follow_up_queue_maintenance_request_id_maintenance_requests')),
    sa.PrimaryKeyConstraint('maintenance_request_id', name=op.f('pk_downtime_follow_up_queue'))
    )
    op.create_index('ix_downtime_follow_up_queue_rank', 'downtime_follow_up_queue', ['priority_rank'], unique=False)
    op.create_index('ix_downtime_follow_up_queue_score', 'downtime_follow_up_queue', ['total_priority_score'], unique=False)
    op.create_index('ix_downtime_follow_up_queue_stage', 'downtime_follow_up_queue', ['current_stage'], unique=False)
    op.create_table('inspection_results',
    sa.Column('inspection_id', sa.String(length=64), nullable=False),
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('inspection_status', sa.String(length=60), nullable=False),
    sa.Column('inspector_id', sa.String(length=64), nullable=True),
    sa.Column('inspection_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('inspection_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['inspector_id'], ['technicians.technician_id'], name=op.f('fk_inspection_results_inspector_id_technicians')),
    sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_inspection_results_maintenance_request_id_maintenance_requests')),
    sa.PrimaryKeyConstraint('inspection_id', name=op.f('pk_inspection_results'))
    )
    op.create_index('ix_inspection_results_inspector_status', 'inspection_results', ['inspector_id', 'inspection_status'], unique=False)
    op.create_index('ix_inspection_results_request_status', 'inspection_results', ['maintenance_request_id', 'inspection_status'], unique=False)
    op.create_table('maintenance_current_status',
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('equipment_id', sa.String(length=64), nullable=False),
    sa.Column('line_id', sa.String(length=64), nullable=False),
    sa.Column('current_stage', sa.String(length=80), nullable=False),
    sa.Column('current_status', sa.String(length=60), nullable=False),
    sa.Column('stage_entered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('hours_in_current_stage', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('is_delayed', sa.Boolean(), nullable=False),
    sa.Column('delay_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('needed_by_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('priority_level', sa.String(length=20), nullable=False),
    sa.Column('business_impact', sa.String(length=100), nullable=False),
    sa.Column('next_owner_type', sa.String(length=60), nullable=True),
    sa.Column('next_owner_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.equipment_id'], name=op.f('fk_maintenance_current_status_equipment_id_equipment')),
    sa.ForeignKeyConstraint(['line_id'], ['production_lines.line_id'], name=op.f('fk_maintenance_current_status_line_id_production_lines')),
    sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_maintenance_current_status_maintenance_request_id_maintenance_requests')),
    sa.PrimaryKeyConstraint('maintenance_request_id', name=op.f('pk_maintenance_current_status'))
    )
    op.create_index('ix_maintenance_current_status_equipment_line', 'maintenance_current_status', ['equipment_id', 'line_id'], unique=False)
    op.create_index('ix_maintenance_current_status_priority_delay', 'maintenance_current_status', ['priority_level', 'delay_hours'], unique=False)
    op.create_index('ix_maintenance_current_status_stage_delayed', 'maintenance_current_status', ['current_stage', 'is_delayed'], unique=False)
    op.create_table('maintenance_stage_events',
    sa.Column('event_id', sa.String(length=64), nullable=False),
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('stage', sa.String(length=80), nullable=False),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('event_status', sa.String(length=60), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actor_type', sa.String(length=60), nullable=False),
    sa.Column('actor_id', sa.String(length=64), nullable=True),
    sa.Column('reason_code', sa.String(length=80), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_maintenance_stage_events_maintenance_request_id_maintenance_requests')),
    sa.PrimaryKeyConstraint('event_id', name=op.f('pk_maintenance_stage_events'))
    )
    op.create_index('ix_maintenance_stage_events_request_time', 'maintenance_stage_events', ['maintenance_request_id', 'occurred_at'], unique=False)
    op.create_index('ix_maintenance_stage_events_stage_time', 'maintenance_stage_events', ['stage', 'occurred_at'], unique=False)
    op.create_index('ix_maintenance_stage_events_type_status', 'maintenance_stage_events', ['event_type', 'event_status'], unique=False)
    op.create_table('maintenance_stage_lead_times',
    sa.Column('lead_time_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('stage', sa.String(length=80), nullable=False),
    sa.Column('entered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('exited_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('threshold_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('is_bottleneck', sa.Boolean(), nullable=False),
    sa.Column('delay_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_maintenance_stage_lead_times_maintenance_request_id_maintenance_requests')),
    sa.PrimaryKeyConstraint('lead_time_id', name=op.f('pk_maintenance_stage_lead_times'))
    )
    op.create_index('ix_maintenance_stage_lead_times_request_stage', 'maintenance_stage_lead_times', ['maintenance_request_id', 'stage'], unique=False)
    op.create_index('ix_maintenance_stage_lead_times_stage_bottleneck', 'maintenance_stage_lead_times', ['stage', 'is_bottleneck'], unique=False)
    op.create_table('maintenance_work_orders',
    sa.Column('work_order_id', sa.String(length=64), nullable=False),
    sa.Column('maintenance_request_id', sa.String(length=64), nullable=False),
    sa.Column('assigned_team', sa.String(length=120), nullable=False),
    sa.Column('assigned_technician_id', sa.String(length=64), nullable=True),
    sa.Column('work_order_status', sa.String(length=60), nullable=False),
    sa.Column('planned_start_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_start_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('required_part_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assigned_technician_id'], ['technicians.technician_id'], name=op.f('fk_maintenance_work_orders_assigned_technician_id_technicians')),
    sa.ForeignKeyConstraint(['maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_maintenance_work_orders_maintenance_request_id_maintenance_requests')),
    sa.ForeignKeyConstraint(['required_part_id'], ['parts.part_id'], name=op.f('fk_maintenance_work_orders_required_part_id_parts')),
    sa.PrimaryKeyConstraint('work_order_id', name=op.f('pk_maintenance_work_orders'))
    )
    op.create_index('ix_maintenance_work_orders_part_status', 'maintenance_work_orders', ['required_part_id', 'work_order_status'], unique=False)
    op.create_index('ix_maintenance_work_orders_request_status', 'maintenance_work_orders', ['maintenance_request_id', 'work_order_status'], unique=False)
    op.create_index('ix_maintenance_work_orders_team_status', 'maintenance_work_orders', ['assigned_team', 'work_order_status'], unique=False)
    op.create_table('sensor_alerts',
    sa.Column('sensor_alert_id', sa.String(length=64), nullable=False),
    sa.Column('equipment_id', sa.String(length=64), nullable=False),
    sa.Column('alert_type', sa.String(length=80), nullable=False),
    sa.Column('severity', sa.String(length=40), nullable=False),
    sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('linked_maintenance_request_id', sa.String(length=64), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.equipment_id'], name=op.f('fk_sensor_alerts_equipment_id_equipment')),
    sa.ForeignKeyConstraint(['linked_maintenance_request_id'], ['maintenance_requests.maintenance_request_id'], name=op.f('fk_sensor_alerts_linked_maintenance_request_id_maintenance_requests')),
    sa.PrimaryKeyConstraint('sensor_alert_id', name=op.f('pk_sensor_alerts'))
    )
    op.create_index('ix_sensor_alerts_equipment_triggered', 'sensor_alerts', ['equipment_id', 'triggered_at'], unique=False)
    op.create_index('ix_sensor_alerts_linked_request', 'sensor_alerts', ['linked_maintenance_request_id'], unique=False)
    op.create_index('ix_sensor_alerts_severity_status', 'sensor_alerts', ['severity', 'resolved_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # Drop objects in dependency-safe reverse order.
    op.drop_index('ix_sensor_alerts_severity_status', table_name='sensor_alerts')
    op.drop_index('ix_sensor_alerts_linked_request', table_name='sensor_alerts')
    op.drop_index('ix_sensor_alerts_equipment_triggered', table_name='sensor_alerts')
    op.drop_table('sensor_alerts')
    op.drop_index('ix_maintenance_work_orders_team_status', table_name='maintenance_work_orders')
    op.drop_index('ix_maintenance_work_orders_request_status', table_name='maintenance_work_orders')
    op.drop_index('ix_maintenance_work_orders_part_status', table_name='maintenance_work_orders')
    op.drop_table('maintenance_work_orders')
    op.drop_index('ix_maintenance_stage_lead_times_stage_bottleneck', table_name='maintenance_stage_lead_times')
    op.drop_index('ix_maintenance_stage_lead_times_request_stage', table_name='maintenance_stage_lead_times')
    op.drop_table('maintenance_stage_lead_times')
    op.drop_index('ix_maintenance_stage_events_type_status', table_name='maintenance_stage_events')
    op.drop_index('ix_maintenance_stage_events_stage_time', table_name='maintenance_stage_events')
    op.drop_index('ix_maintenance_stage_events_request_time', table_name='maintenance_stage_events')
    op.drop_table('maintenance_stage_events')
    op.drop_index('ix_maintenance_current_status_stage_delayed', table_name='maintenance_current_status')
    op.drop_index('ix_maintenance_current_status_priority_delay', table_name='maintenance_current_status')
    op.drop_index('ix_maintenance_current_status_equipment_line', table_name='maintenance_current_status')
    op.drop_table('maintenance_current_status')
    op.drop_index('ix_inspection_results_request_status', table_name='inspection_results')
    op.drop_index('ix_inspection_results_inspector_status', table_name='inspection_results')
    op.drop_table('inspection_results')
    op.drop_index('ix_downtime_follow_up_queue_stage', table_name='downtime_follow_up_queue')
    op.drop_index('ix_downtime_follow_up_queue_score', table_name='downtime_follow_up_queue')
    op.drop_index('ix_downtime_follow_up_queue_rank', table_name='downtime_follow_up_queue')
    op.drop_table('downtime_follow_up_queue')
    op.drop_index('ix_maintenance_requests_type_failure', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_priority_needed', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_line_stage', table_name='maintenance_requests')
    op.drop_index('ix_maintenance_requests_equipment_status', table_name='maintenance_requests')
    op.drop_table('maintenance_requests')
    op.drop_index('ix_equipment_delay_summary_downtime', table_name='equipment_delay_summary')
    op.drop_index('ix_equipment_delay_summary_delayed', table_name='equipment_delay_summary')
    op.drop_table('equipment_delay_summary')
    op.drop_index('ix_production_line_delay_summary_downtime', table_name='production_line_delay_summary')
    op.drop_index('ix_production_line_delay_summary_delayed', table_name='production_line_delay_summary')
    op.drop_table('production_line_delay_summary')
    op.drop_index('ix_parts_waiting_summary_wait_hours', table_name='parts_waiting_summary')
    op.drop_index('ix_parts_waiting_summary_category_stock', table_name='parts_waiting_summary')
    op.drop_table('parts_waiting_summary')
    op.drop_index('ix_equipment_type_status', table_name='equipment')
    op.drop_index('ix_equipment_line_criticality', table_name='equipment')
    op.drop_table('equipment')
    op.drop_index('ix_technicians_team_shift', table_name='technicians')
    op.drop_index('ix_technicians_skill_status', table_name='technicians')
    op.drop_table('technicians')
    op.drop_index(op.f('ix_raw_sensor_alerts_pipeline_run_id'), table_name='raw_sensor_alerts')
    op.drop_index('ix_raw_sensor_alert_pipeline_source', table_name='raw_sensor_alerts')
    op.drop_table('raw_sensor_alerts')
    op.drop_index(op.f('ix_raw_maintenance_work_orders_pipeline_run_id'), table_name='raw_maintenance_work_orders')
    op.drop_index('ix_raw_maintenance_work_order_pipeline_source', table_name='raw_maintenance_work_orders')
    op.drop_table('raw_maintenance_work_orders')
    op.drop_index(op.f('ix_raw_maintenance_stage_events_pipeline_run_id'), table_name='raw_maintenance_stage_events')
    op.drop_index('ix_raw_maintenance_stage_event_pipeline_source', table_name='raw_maintenance_stage_events')
    op.drop_table('raw_maintenance_stage_events')
    op.drop_index(op.f('ix_raw_maintenance_requests_pipeline_run_id'), table_name='raw_maintenance_requests')
    op.drop_index('ix_raw_maintenance_request_pipeline_source', table_name='raw_maintenance_requests')
    op.drop_table('raw_maintenance_requests')
    op.drop_index(op.f('ix_raw_inspection_results_pipeline_run_id'), table_name='raw_inspection_results')
    op.drop_index('ix_raw_inspection_result_pipeline_source', table_name='raw_inspection_results')
    op.drop_table('raw_inspection_results')
    op.drop_index('ix_production_lines_priority_status', table_name='production_lines')
    op.drop_table('production_lines')
    op.drop_index('ix_pipeline_runs_status', table_name='pipeline_runs')
    op.drop_index('ix_pipeline_runs_name_started', table_name='pipeline_runs')
    op.drop_table('pipeline_runs')
    op.drop_index('ix_parts_critical_spare', table_name='parts')
    op.drop_index('ix_parts_category_stock', table_name='parts')
    op.drop_table('parts')
    op.drop_index('ix_maintenance_bottleneck_summary_stage_delay', table_name='maintenance_bottleneck_summary')
    op.drop_index('ix_maintenance_bottleneck_summary_date_dimension', table_name='maintenance_bottleneck_summary')
    op.drop_table('maintenance_bottleneck_summary')
    op.drop_index('ix_dq_results_target_table', table_name='data_quality_check_results')
    op.drop_index('ix_dq_results_severity', table_name='data_quality_check_results')
    op.drop_index('ix_dq_results_run_status', table_name='data_quality_check_results')
    op.drop_index(op.f('ix_data_quality_check_results_pipeline_run_id'), table_name='data_quality_check_results')
    op.drop_table('data_quality_check_results')
    # ### end Alembic commands ###
