from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    total_requests: int
    open_requests: int
    delayed_requests: int
    critical_asset_delayed: int
    avg_downtime_hours: float
    top_bottleneck_stage: Optional[str]
    spare_waiting_delay_hours: float
    repeat_failure_asset_count: int
    engineer_assignment_delay_hours: float
    capacity_risk_kw: float
    affected_gpu_count: int
    redundancy_lost_incidents: int
    vendor_eta_missed_count: int
    latest_pipeline_run_status: Optional[str]
    data_quality_status: str


class StageBottleneckResponse(BaseModel):
    stage: str
    request_count: int
    delayed_count: int
    delay_rate: float
    avg_duration_hours: float
    p90_duration_hours: float
    total_delay_hours: float


class FollowUpItemResponse(BaseModel):
    priority_rank: int
    incident_id: str
    request_number: str
    request_title: str
    asset_id: str
    asset_name: str
    zone_id: str
    zone_name: str
    current_stage: str
    current_status: str
    hours_in_current_stage: float
    needed_by_at: datetime
    priority_level: str
    business_impact: str
    asset_criticality_score: float
    downtime_score: float
    stage_delay_score: float
    infrastructure_zone_impact_score: float
    needed_by_urgency_score: float
    repeat_failure_score: float
    spare_risk_score: float
    capacity_risk_score: float
    redundancy_risk_score: float
    thermal_risk_score: float
    vendor_eta_risk_score: float
    mitigation_credit_score: float
    total_priority_score: float
    recommended_action: str
    reason_summary: str
    redundancy_state: Optional[str] = None
    affected_gpu_count: int = 0
    estimated_capacity_risk_kw: float = 0
    mitigation_status: Optional[str] = None
    vendor_status: Optional[str] = None
    impact_confidence_status: str = "UNVERIFIED"
    impact_trust_issue_count: int = 0


class StageLeadTimeResponse(BaseModel):
    stage: str
    entered_at: datetime
    exited_at: Optional[datetime]
    duration_hours: float
    threshold_hours: float
    is_bottleneck: bool
    delay_hours: float


class TimelineEventResponse(BaseModel):
    event_id: str
    stage: str
    event_type: str
    event_status: str
    occurred_at: datetime
    actor_type: str
    reason_code: Optional[str]
    message: Optional[str]


class WorkOrderSummaryResponse(BaseModel):
    work_order_id: str
    assigned_team: str
    assigned_engineer_id: Optional[str]
    work_order_status: str
    planned_start_at: Optional[datetime]
    actual_start_at: Optional[datetime]
    actual_completed_at: Optional[datetime]
    required_spare_id: Optional[str]
    required_spare_name: Optional[str]
    stock_status: Optional[str]


class ValidationResponse(BaseModel):
    validation_id: str
    validation_status: str
    validator_id: Optional[str]
    validation_started_at: Optional[datetime]
    validation_completed_at: Optional[datetime]
    failure_reason: Optional[str]


class TelemetryAlertResponse(BaseModel):
    telemetry_alert_id: str
    asset_id: str
    alert_type: str
    severity: str
    triggered_at: datetime
    resolved_at: Optional[datetime]


class ImpactTelemetryReadingResponse(BaseModel):
    metric: str
    value: float
    unit: str
    status: str


class InfrastructureImpactSnapshotResponse(BaseModel):
    impact_snapshot_id: str
    incident_id: str
    asset_id: str
    zone_id: str
    snapshot_at: datetime
    redundancy_state: str
    affected_rack_count: int
    affected_gpu_count: int
    estimated_capacity_risk_kw: float
    estimated_gpu_capacity_risk_pct: float
    thermal_breach_minutes: int
    power_redundancy_lost: bool
    cooling_redundancy_lost: bool
    mitigation_status: str
    vendor_eta_at: Optional[datetime]
    vendor_status: str
    source_system: str
    telemetry_readings: list[ImpactTelemetryReadingResponse] = Field(default_factory=list)


class ImpactTrustFlagResponse(BaseModel):
    issue_type: str
    severity: str
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ImpactSummaryResponse(BaseModel):
    incident_count: int
    capacity_risk_kw: float
    affected_rack_count: int
    affected_gpu_count: int
    redundancy_lost_incidents: int
    vendor_eta_missed_count: int
    mitigated_incidents: int
    thermal_breach_minutes: int
    trusted_impact_count: int
    warning_impact_count: int
    unverified_impact_count: int


class InfrastructureDependencyResponse(BaseModel):
    dependency_id: str
    dependent_asset_id: str
    dependent_asset_name: str
    dependent_asset_type: str
    dependent_status: str
    dependency_asset_id: str
    dependency_asset_name: str
    dependency_asset_type: str
    dependency_status: str
    dependency_type: str
    dependency_role: str
    impact_scope: str
    dependent_active_incident_count: int
    dependency_active_incident_count: int


class ConnectorContractResponse(BaseModel):
    source_name: str
    extract_file: str
    target_table: str
    cadence: str
    required_payload_fields: list[str] = Field(default_factory=list)
    optional_payload_fields: list[str] = Field(default_factory=list)
    notes: str


class RequestDetailResponse(BaseModel):
    request: FollowUpItemResponse
    stage_lead_times: list[StageLeadTimeResponse]
    timeline: list[TimelineEventResponse]
    work_orders: list[WorkOrderSummaryResponse]
    validation_results: list[ValidationResponse]
    telemetry_alerts: list[TelemetryAlertResponse]
    impact_snapshot: Optional[InfrastructureImpactSnapshotResponse]
    quality_flags: list[str]
    impact_confidence_status: str
    impact_trust_flags: list[ImpactTrustFlagResponse]


class InfrastructureAssetDelayResponse(BaseModel):
    asset_id: str
    asset_name: str
    zone_id: str
    zone_name: str
    request_count: int
    delayed_request_count: int
    repeat_failure_count: int
    total_downtime_hours: float
    avg_repair_duration_hours: float
    top_failure_mode: str


class InfrastructureZoneDelayResponse(BaseModel):
    zone_id: str
    zone_name: str
    open_request_count: int
    delayed_request_count: int
    critical_asset_delayed_count: int
    total_downtime_hours: float
    top_bottleneck_stage: str


class SpareWaitingResponse(BaseModel):
    spare_id: str
    spare_name: str
    spare_category: str
    waiting_request_count: int
    total_wait_hours: float
    avg_wait_hours: float
    critical_spare: bool
    stock_status: str


class PipelineRunResponse(BaseModel):
    pipeline_run_id: str
    pipeline_name: str
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    rows_extracted: int
    rows_loaded: int
    rows_rejected: int
    error_message: Optional[str]


class DataQualityCheckResponse(BaseModel):
    check_result_id: str
    pipeline_run_id: str
    check_name: str
    target_table: str
    severity: str
    status: str
    failed_row_count: int
    sample_failed_keys: list[str] = Field(default_factory=list)
    message: str
    created_at: datetime


class FilterOption(BaseModel):
    id: str
    name: str


class FilterMetadataResponse(BaseModel):
    infrastructure_zones: list[FilterOption]
    assets: list[FilterOption]
    asset_types: list[str]
    facilities_teams: list[str]
    spare_categories: list[str]
    priority_levels: list[str]
    request_types: list[str]
    failure_modes: list[str]
    stages: list[str]


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
