"""AI data center infrastructure clean baseline.

Revision ID: 0001_ai_infra
Revises:
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_ai_infra"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Explicit clean baseline generated from the approved AI infrastructure metadata.
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
    op.create_table('infrastructure_bottleneck_summary',
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
    sa.PrimaryKeyConstraint('summary_id', name=op.f('pk_infrastructure_bottleneck_summary'))
    )
    op.create_index('ix_infrastructure_bottleneck_summary_date_dimension', 'infrastructure_bottleneck_summary', ['summary_date', 'dimension_type', 'dimension_id'], unique=False)
    op.create_index('ix_infrastructure_bottleneck_summary_stage_delay', 'infrastructure_bottleneck_summary', ['stage', 'total_delay_hours'], unique=False)
    op.create_table('critical_spares',
    sa.Column('spare_id', sa.String(length=64), nullable=False),
    sa.Column('spare_number', sa.String(length=80), nullable=False),
    sa.Column('spare_name', sa.String(length=200), nullable=False),
    sa.Column('spare_category', sa.String(length=80), nullable=False),
    sa.Column('stock_status', sa.String(length=60), nullable=False),
    sa.Column('lead_time_days', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('critical_spare', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('spare_id', name=op.f('pk_critical_spares')),
    sa.UniqueConstraint('spare_number', name='uq_critical_spares_spare_number')
    )
    op.create_index('ix_critical_spares_category_stock', 'critical_spares', ['spare_category', 'stock_status'], unique=False)
    op.create_index('ix_critical_spares_critical_spare', 'critical_spares', ['critical_spare'], unique=False)
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
    op.create_table('infrastructure_zones',
    sa.Column('zone_id', sa.String(length=64), nullable=False),
    sa.Column('zone_code', sa.String(length=80), nullable=False),
    sa.Column('zone_name', sa.String(length=160), nullable=False),
    sa.Column('facility_area', sa.String(length=120), nullable=False),
    sa.Column('zone_priority', sa.String(length=40), nullable=False),
    sa.Column('current_status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('zone_id', name=op.f('pk_infrastructure_zones')),
    sa.UniqueConstraint('zone_code', name='uq_infrastructure_zones_zone_code')
    )
    op.create_index('ix_infrastructure_zones_priority_status', 'infrastructure_zones', ['zone_priority', 'current_status'], unique=False)
    op.create_table('raw_validation_results',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_validation_results')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_validation_result_source_record')
    )
    op.create_index('ix_raw_validation_result_pipeline_source', 'raw_validation_results', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_validation_results_pipeline_run_id'), 'raw_validation_results', ['pipeline_run_id'], unique=False)
    op.create_table('raw_infrastructure_incidents',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_infrastructure_incidents')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_infrastructure_request_source_record')
    )
    op.create_index('ix_raw_infrastructure_request_pipeline_source', 'raw_infrastructure_incidents', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_infrastructure_incidents_pipeline_run_id'), 'raw_infrastructure_incidents', ['pipeline_run_id'], unique=False)
    op.create_table('raw_incident_stage_events',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_incident_stage_events')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_infrastructure_stage_event_source_record')
    )
    op.create_index('ix_raw_infrastructure_stage_event_pipeline_source', 'raw_incident_stage_events', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_incident_stage_events_pipeline_run_id'), 'raw_incident_stage_events', ['pipeline_run_id'], unique=False)
    op.create_table('raw_facility_work_orders',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_facility_work_orders')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_infrastructure_work_order_source_record')
    )
    op.create_index('ix_raw_infrastructure_work_order_pipeline_source', 'raw_facility_work_orders', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_facility_work_orders_pipeline_run_id'), 'raw_facility_work_orders', ['pipeline_run_id'], unique=False)
    op.create_table('raw_telemetry_alerts',
    sa.Column('raw_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_record_id', sa.String(length=120), nullable=False),
    sa.Column('source_system', sa.String(length=80), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('pipeline_run_id', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('raw_id', name=op.f('pk_raw_telemetry_alerts')),
    sa.UniqueConstraint('source_system', 'source_record_id', name='uq_raw_telemetry_alert_source_record')
    )
    op.create_index('ix_raw_telemetry_alert_pipeline_source', 'raw_telemetry_alerts', ['pipeline_run_id', 'source_system'], unique=False)
    op.create_index(op.f('ix_raw_telemetry_alerts_pipeline_run_id'), 'raw_telemetry_alerts', ['pipeline_run_id'], unique=False)
    op.create_table('facilities_engineers',
    sa.Column('engineer_id', sa.String(length=64), nullable=False),
    sa.Column('engineer_name', sa.String(length=160), nullable=False),
    sa.Column('team_name', sa.String(length=120), nullable=False),
    sa.Column('skill_group', sa.String(length=80), nullable=False),
    sa.Column('shift', sa.String(length=40), nullable=False),
    sa.Column('active_status', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('engineer_id', name=op.f('pk_facilities_engineers'))
    )
    op.create_index('ix_facilities_engineers_skill_status', 'facilities_engineers', ['skill_group', 'active_status'], unique=False)
    op.create_index('ix_facilities_engineers_team_shift', 'facilities_engineers', ['team_name', 'shift'], unique=False)
    op.create_table('infrastructure_assets',
    sa.Column('asset_id', sa.String(length=64), nullable=False),
    sa.Column('asset_code', sa.String(length=80), nullable=False),
    sa.Column('asset_name', sa.String(length=200), nullable=False),
    sa.Column('asset_type', sa.String(length=80), nullable=False),
    sa.Column('zone_id', sa.String(length=64), nullable=False),
    sa.Column('criticality_level', sa.String(length=20), nullable=False),
    sa.Column('installed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('manufacturer', sa.String(length=120), nullable=False),
    sa.Column('model_number', sa.String(length=120), nullable=False),
    sa.Column('current_status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['zone_id'], ['infrastructure_zones.zone_id'], name=op.f('fk_asset_zone_id_infrastructure_zones')),
    sa.PrimaryKeyConstraint('asset_id', name=op.f('pk_infrastructure_assets')),
    sa.UniqueConstraint('asset_code', name='uq_infrastructure_assets_asset_code')
    )
    op.create_index('ix_infrastructure_assets_zone_criticality', 'infrastructure_assets', ['zone_id', 'criticality_level'], unique=False)
    op.create_index('ix_asset_type_status', 'infrastructure_assets', ['asset_type', 'current_status'], unique=False)
    op.create_table('spare_waiting_summary',
    sa.Column('spare_id', sa.String(length=64), nullable=False),
    sa.Column('spare_name', sa.String(length=200), nullable=False),
    sa.Column('spare_category', sa.String(length=80), nullable=False),
    sa.Column('waiting_request_count', sa.Integer(), nullable=False),
    sa.Column('total_wait_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('avg_wait_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('critical_spare', sa.Boolean(), nullable=False),
    sa.Column('stock_status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['spare_id'], ['critical_spares.spare_id'], name=op.f('fk_spare_waiting_summary_spare_id_critical_spares')),
    sa.PrimaryKeyConstraint('spare_id', name=op.f('pk_spare_waiting_summary'))
    )
    op.create_index('ix_spare_waiting_summary_category_stock', 'spare_waiting_summary', ['spare_category', 'stock_status'], unique=False)
    op.create_index('ix_spare_waiting_summary_wait_hours', 'spare_waiting_summary', ['total_wait_hours'], unique=False)
    op.create_table('zone_delay_summary',
    sa.Column('zone_id', sa.String(length=64), nullable=False),
    sa.Column('zone_name', sa.String(length=160), nullable=False),
    sa.Column('open_request_count', sa.Integer(), nullable=False),
    sa.Column('delayed_request_count', sa.Integer(), nullable=False),
    sa.Column('critical_asset_delayed_count', sa.Integer(), nullable=False),
    sa.Column('total_downtime_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('top_bottleneck_stage', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['zone_id'], ['infrastructure_zones.zone_id'], name=op.f('fk_zone_delay_summary_zone_id_infrastructure_zones')),
    sa.PrimaryKeyConstraint('zone_id', name=op.f('pk_zone_delay_summary'))
    )
    op.create_index('ix_zone_delay_summary_delayed', 'zone_delay_summary', ['delayed_request_count'], unique=False)
    op.create_index('ix_zone_delay_summary_downtime', 'zone_delay_summary', ['total_downtime_hours'], unique=False)
    op.create_table('asset_delay_summary',
    sa.Column('asset_id', sa.String(length=64), nullable=False),
    sa.Column('asset_name', sa.String(length=200), nullable=False),
    sa.Column('zone_id', sa.String(length=64), nullable=False),
    sa.Column('zone_name', sa.String(length=160), nullable=False),
    sa.Column('request_count', sa.Integer(), nullable=False),
    sa.Column('delayed_request_count', sa.Integer(), nullable=False),
    sa.Column('repeat_failure_count', sa.Integer(), nullable=False),
    sa.Column('total_downtime_hours', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('avg_repair_duration_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('top_failure_mode', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['infrastructure_assets.asset_id'], name=op.f('fk_asset_delay_summary_asset_id_asset')),
    sa.ForeignKeyConstraint(['zone_id'], ['infrastructure_zones.zone_id'], name=op.f('fk_asset_delay_summary_zone_id_infrastructure_zones')),
    sa.PrimaryKeyConstraint('asset_id', name=op.f('pk_asset_delay_summary'))
    )
    op.create_index('ix_asset_delay_summary_delayed', 'asset_delay_summary', ['delayed_request_count'], unique=False)
    op.create_index('ix_asset_delay_summary_downtime', 'asset_delay_summary', ['total_downtime_hours'], unique=False)
    op.create_table('infrastructure_incidents',
    sa.Column('incident_id', sa.String(length=64), nullable=False),
    sa.Column('request_number', sa.String(length=80), nullable=False),
    sa.Column('asset_id', sa.String(length=64), nullable=False),
    sa.Column('zone_id', sa.String(length=64), nullable=False),
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
    sa.ForeignKeyConstraint(['asset_id'], ['infrastructure_assets.asset_id'], name=op.f('fk_infrastructure_incidents_asset_id_asset')),
    sa.ForeignKeyConstraint(['zone_id'], ['infrastructure_zones.zone_id'], name=op.f('fk_infrastructure_incidents_zone_id_infrastructure_zones')),
    sa.PrimaryKeyConstraint('incident_id', name=op.f('pk_infrastructure_incidents')),
    sa.UniqueConstraint('request_number', name='uq_infrastructure_incidents_request_number')
    )
    op.create_index('ix_infrastructure_incidents_asset_status', 'infrastructure_incidents', ['asset_id', 'current_status'], unique=False)
    op.create_index('ix_infrastructure_incidents_zone_stage', 'infrastructure_incidents', ['zone_id', 'current_stage'], unique=False)
    op.create_index('ix_infrastructure_incidents_priority_needed', 'infrastructure_incidents', ['priority_level', 'needed_by_at'], unique=False)
    op.create_index('ix_infrastructure_incidents_type_failure', 'infrastructure_incidents', ['request_type', 'failure_mode'], unique=False)
    op.create_table('downtime_follow_up_queue',
    sa.Column('incident_id', sa.String(length=64), nullable=False),
    sa.Column('priority_rank', sa.Integer(), nullable=False),
    sa.Column('asset_id', sa.String(length=64), nullable=False),
    sa.Column('zone_id', sa.String(length=64), nullable=False),
    sa.Column('current_stage', sa.String(length=80), nullable=False),
    sa.Column('asset_criticality_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('downtime_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('stage_delay_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('infrastructure_zone_impact_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('needed_by_urgency_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('repeat_failure_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('spare_risk_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('total_priority_score', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('recommended_action', sa.String(length=240), nullable=False),
    sa.Column('reason_summary', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['infrastructure_assets.asset_id'], name=op.f('fk_downtime_follow_up_queue_asset_id_asset')),
    sa.ForeignKeyConstraint(['zone_id'], ['infrastructure_zones.zone_id'], name=op.f('fk_downtime_follow_up_queue_zone_id_infrastructure_zones')),
    sa.ForeignKeyConstraint(['incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_downtime_follow_up_queue_incident_id_infrastructure_incidents')),
    sa.PrimaryKeyConstraint('incident_id', name=op.f('pk_downtime_follow_up_queue'))
    )
    op.create_index('ix_downtime_follow_up_queue_rank', 'downtime_follow_up_queue', ['priority_rank'], unique=False)
    op.create_index('ix_downtime_follow_up_queue_score', 'downtime_follow_up_queue', ['total_priority_score'], unique=False)
    op.create_index('ix_downtime_follow_up_queue_stage', 'downtime_follow_up_queue', ['current_stage'], unique=False)
    op.create_table('validation_results',
    sa.Column('validation_id', sa.String(length=64), nullable=False),
    sa.Column('incident_id', sa.String(length=64), nullable=False),
    sa.Column('validation_status', sa.String(length=60), nullable=False),
    sa.Column('validator_id', sa.String(length=64), nullable=True),
    sa.Column('validation_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('validation_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['validator_id'], ['facilities_engineers.engineer_id'], name=op.f('fk_validation_results_validator_id_facilities_engineers')),
    sa.ForeignKeyConstraint(['incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_validation_results_incident_id_infrastructure_incidents')),
    sa.PrimaryKeyConstraint('validation_id', name=op.f('pk_validation_results'))
    )
    op.create_index('ix_validation_results_validator_status', 'validation_results', ['validator_id', 'validation_status'], unique=False)
    op.create_index('ix_validation_results_request_status', 'validation_results', ['incident_id', 'validation_status'], unique=False)
    op.create_table('incident_current_status',
    sa.Column('incident_id', sa.String(length=64), nullable=False),
    sa.Column('asset_id', sa.String(length=64), nullable=False),
    sa.Column('zone_id', sa.String(length=64), nullable=False),
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
    sa.ForeignKeyConstraint(['asset_id'], ['infrastructure_assets.asset_id'], name=op.f('fk_incident_current_status_asset_id_asset')),
    sa.ForeignKeyConstraint(['zone_id'], ['infrastructure_zones.zone_id'], name=op.f('fk_incident_current_status_zone_id_infrastructure_zones')),
    sa.ForeignKeyConstraint(['incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_incident_current_status_incident_id_infrastructure_incidents')),
    sa.PrimaryKeyConstraint('incident_id', name=op.f('pk_incident_current_status'))
    )
    op.create_index('ix_incident_current_status_asset_zone', 'incident_current_status', ['asset_id', 'zone_id'], unique=False)
    op.create_index('ix_incident_current_status_priority_delay', 'incident_current_status', ['priority_level', 'delay_hours'], unique=False)
    op.create_index('ix_incident_current_status_stage_delayed', 'incident_current_status', ['current_stage', 'is_delayed'], unique=False)
    op.create_table('incident_stage_events',
    sa.Column('event_id', sa.String(length=64), nullable=False),
    sa.Column('incident_id', sa.String(length=64), nullable=False),
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
    sa.ForeignKeyConstraint(['incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_incident_stage_events_incident_id_infrastructure_incidents')),
    sa.PrimaryKeyConstraint('event_id', name=op.f('pk_incident_stage_events'))
    )
    op.create_index('ix_incident_stage_events_request_time', 'incident_stage_events', ['incident_id', 'occurred_at'], unique=False)
    op.create_index('ix_incident_stage_events_stage_time', 'incident_stage_events', ['stage', 'occurred_at'], unique=False)
    op.create_index('ix_incident_stage_events_type_status', 'incident_stage_events', ['event_type', 'event_status'], unique=False)
    op.create_table('incident_stage_lead_times',
    sa.Column('lead_time_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('incident_id', sa.String(length=64), nullable=False),
    sa.Column('stage', sa.String(length=80), nullable=False),
    sa.Column('entered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('exited_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('threshold_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('is_bottleneck', sa.Boolean(), nullable=False),
    sa.Column('delay_hours', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_incident_stage_lead_times_incident_id_infrastructure_incidents')),
    sa.PrimaryKeyConstraint('lead_time_id', name=op.f('pk_incident_stage_lead_times'))
    )
    op.create_index('ix_incident_stage_lead_times_request_stage', 'incident_stage_lead_times', ['incident_id', 'stage'], unique=False)
    op.create_index('ix_incident_stage_lead_times_stage_bottleneck', 'incident_stage_lead_times', ['stage', 'is_bottleneck'], unique=False)
    op.create_table('facility_work_orders',
    sa.Column('work_order_id', sa.String(length=64), nullable=False),
    sa.Column('incident_id', sa.String(length=64), nullable=False),
    sa.Column('assigned_team', sa.String(length=120), nullable=False),
    sa.Column('assigned_engineer_id', sa.String(length=64), nullable=True),
    sa.Column('work_order_status', sa.String(length=60), nullable=False),
    sa.Column('planned_start_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_start_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('required_spare_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['assigned_engineer_id'], ['facilities_engineers.engineer_id'], name=op.f('fk_facility_work_orders_assigned_engineer_id_facilities_engineers')),
    sa.ForeignKeyConstraint(['incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_facility_work_orders_incident_id_infrastructure_incidents')),
    sa.ForeignKeyConstraint(['required_spare_id'], ['critical_spares.spare_id'], name=op.f('fk_facility_work_orders_required_spare_id_critical_spares')),
    sa.PrimaryKeyConstraint('work_order_id', name=op.f('pk_facility_work_orders'))
    )
    op.create_index('ix_facility_work_orders_part_status', 'facility_work_orders', ['required_spare_id', 'work_order_status'], unique=False)
    op.create_index('ix_facility_work_orders_request_status', 'facility_work_orders', ['incident_id', 'work_order_status'], unique=False)
    op.create_index('ix_facility_work_orders_team_status', 'facility_work_orders', ['assigned_team', 'work_order_status'], unique=False)
    op.create_table('telemetry_alerts',
    sa.Column('telemetry_alert_id', sa.String(length=64), nullable=False),
    sa.Column('asset_id', sa.String(length=64), nullable=False),
    sa.Column('alert_type', sa.String(length=80), nullable=False),
    sa.Column('severity', sa.String(length=40), nullable=False),
    sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('linked_incident_id', sa.String(length=64), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['infrastructure_assets.asset_id'], name=op.f('fk_telemetry_alerts_asset_id_asset')),
    sa.ForeignKeyConstraint(['linked_incident_id'], ['infrastructure_incidents.incident_id'], name=op.f('fk_telemetry_alerts_linked_incident_id_infrastructure_incidents')),
    sa.PrimaryKeyConstraint('telemetry_alert_id', name=op.f('pk_telemetry_alerts'))
    )
    op.create_index('ix_telemetry_alerts_asset_triggered', 'telemetry_alerts', ['asset_id', 'triggered_at'], unique=False)
    op.create_index('ix_telemetry_alerts_linked_request', 'telemetry_alerts', ['linked_incident_id'], unique=False)
    op.create_index('ix_telemetry_alerts_severity_status', 'telemetry_alerts', ['severity', 'resolved_at'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # Drop objects in dependency-safe reverse order.
    op.drop_index('ix_telemetry_alerts_severity_status', table_name='telemetry_alerts')
    op.drop_index('ix_telemetry_alerts_linked_request', table_name='telemetry_alerts')
    op.drop_index('ix_telemetry_alerts_asset_triggered', table_name='telemetry_alerts')
    op.drop_table('telemetry_alerts')
    op.drop_index('ix_facility_work_orders_team_status', table_name='facility_work_orders')
    op.drop_index('ix_facility_work_orders_request_status', table_name='facility_work_orders')
    op.drop_index('ix_facility_work_orders_part_status', table_name='facility_work_orders')
    op.drop_table('facility_work_orders')
    op.drop_index('ix_incident_stage_lead_times_stage_bottleneck', table_name='incident_stage_lead_times')
    op.drop_index('ix_incident_stage_lead_times_request_stage', table_name='incident_stage_lead_times')
    op.drop_table('incident_stage_lead_times')
    op.drop_index('ix_incident_stage_events_type_status', table_name='incident_stage_events')
    op.drop_index('ix_incident_stage_events_stage_time', table_name='incident_stage_events')
    op.drop_index('ix_incident_stage_events_request_time', table_name='incident_stage_events')
    op.drop_table('incident_stage_events')
    op.drop_index('ix_incident_current_status_stage_delayed', table_name='incident_current_status')
    op.drop_index('ix_incident_current_status_priority_delay', table_name='incident_current_status')
    op.drop_index('ix_incident_current_status_asset_zone', table_name='incident_current_status')
    op.drop_table('incident_current_status')
    op.drop_index('ix_validation_results_request_status', table_name='validation_results')
    op.drop_index('ix_validation_results_validator_status', table_name='validation_results')
    op.drop_table('validation_results')
    op.drop_index('ix_downtime_follow_up_queue_stage', table_name='downtime_follow_up_queue')
    op.drop_index('ix_downtime_follow_up_queue_score', table_name='downtime_follow_up_queue')
    op.drop_index('ix_downtime_follow_up_queue_rank', table_name='downtime_follow_up_queue')
    op.drop_table('downtime_follow_up_queue')
    op.drop_index('ix_infrastructure_incidents_type_failure', table_name='infrastructure_incidents')
    op.drop_index('ix_infrastructure_incidents_priority_needed', table_name='infrastructure_incidents')
    op.drop_index('ix_infrastructure_incidents_zone_stage', table_name='infrastructure_incidents')
    op.drop_index('ix_infrastructure_incidents_asset_status', table_name='infrastructure_incidents')
    op.drop_table('infrastructure_incidents')
    op.drop_index('ix_asset_delay_summary_downtime', table_name='asset_delay_summary')
    op.drop_index('ix_asset_delay_summary_delayed', table_name='asset_delay_summary')
    op.drop_table('asset_delay_summary')
    op.drop_index('ix_zone_delay_summary_downtime', table_name='zone_delay_summary')
    op.drop_index('ix_zone_delay_summary_delayed', table_name='zone_delay_summary')
    op.drop_table('zone_delay_summary')
    op.drop_index('ix_spare_waiting_summary_wait_hours', table_name='spare_waiting_summary')
    op.drop_index('ix_spare_waiting_summary_category_stock', table_name='spare_waiting_summary')
    op.drop_table('spare_waiting_summary')
    op.drop_index('ix_asset_type_status', table_name='infrastructure_assets')
    op.drop_index('ix_infrastructure_assets_zone_criticality', table_name='infrastructure_assets')
    op.drop_table('infrastructure_assets')
    op.drop_index('ix_facilities_engineers_team_shift', table_name='facilities_engineers')
    op.drop_index('ix_facilities_engineers_skill_status', table_name='facilities_engineers')
    op.drop_table('facilities_engineers')
    op.drop_index(op.f('ix_raw_telemetry_alerts_pipeline_run_id'), table_name='raw_telemetry_alerts')
    op.drop_index('ix_raw_telemetry_alert_pipeline_source', table_name='raw_telemetry_alerts')
    op.drop_table('raw_telemetry_alerts')
    op.drop_index(op.f('ix_raw_facility_work_orders_pipeline_run_id'), table_name='raw_facility_work_orders')
    op.drop_index('ix_raw_infrastructure_work_order_pipeline_source', table_name='raw_facility_work_orders')
    op.drop_table('raw_facility_work_orders')
    op.drop_index(op.f('ix_raw_incident_stage_events_pipeline_run_id'), table_name='raw_incident_stage_events')
    op.drop_index('ix_raw_infrastructure_stage_event_pipeline_source', table_name='raw_incident_stage_events')
    op.drop_table('raw_incident_stage_events')
    op.drop_index(op.f('ix_raw_infrastructure_incidents_pipeline_run_id'), table_name='raw_infrastructure_incidents')
    op.drop_index('ix_raw_infrastructure_request_pipeline_source', table_name='raw_infrastructure_incidents')
    op.drop_table('raw_infrastructure_incidents')
    op.drop_index(op.f('ix_raw_validation_results_pipeline_run_id'), table_name='raw_validation_results')
    op.drop_index('ix_raw_validation_result_pipeline_source', table_name='raw_validation_results')
    op.drop_table('raw_validation_results')
    op.drop_index('ix_infrastructure_zones_priority_status', table_name='infrastructure_zones')
    op.drop_table('infrastructure_zones')
    op.drop_index('ix_pipeline_runs_status', table_name='pipeline_runs')
    op.drop_index('ix_pipeline_runs_name_started', table_name='pipeline_runs')
    op.drop_table('pipeline_runs')
    op.drop_index('ix_critical_spares_critical_spare', table_name='critical_spares')
    op.drop_index('ix_critical_spares_category_stock', table_name='critical_spares')
    op.drop_table('critical_spares')
    op.drop_index('ix_infrastructure_bottleneck_summary_stage_delay', table_name='infrastructure_bottleneck_summary')
    op.drop_index('ix_infrastructure_bottleneck_summary_date_dimension', table_name='infrastructure_bottleneck_summary')
    op.drop_table('infrastructure_bottleneck_summary')
    op.drop_index('ix_dq_results_target_table', table_name='data_quality_check_results')
    op.drop_index('ix_dq_results_severity', table_name='data_quality_check_results')
    op.drop_index('ix_dq_results_run_status', table_name='data_quality_check_results')
    op.drop_index(op.f('ix_data_quality_check_results_pipeline_run_id'), table_name='data_quality_check_results')
    op.drop_table('data_quality_check_results')
    # ### end Alembic commands ###
