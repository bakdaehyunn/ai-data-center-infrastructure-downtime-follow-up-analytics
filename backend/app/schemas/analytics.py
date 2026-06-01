from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    total_requests: int
    open_requests: int
    delayed_requests: int
    critical_open_requests: int
    avg_cycle_time_hours: float
    total_delay_hours: float
    top_bottleneck_stage: Optional[str]
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


class VendorBottleneckResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    total_po_count: int
    delayed_po_count: int
    delay_rate: float
    avg_confirmation_hours: float
    avg_delivery_delay_days: float
    reliability_tier: str
    total_delay_hours: float


class CriticalRequestResponse(BaseModel):
    priority_rank: int
    request_id: str
    request_number: str
    request_title: str
    department_id: str
    department_name: str
    current_stage: str
    current_status: str
    days_in_current_stage: float
    needed_by_date: date
    criticality_level: str
    business_impact: str
    criticality_score: float
    delay_score: float
    business_impact_score: float
    needed_by_urgency_score: float
    vendor_risk_score: float
    total_priority_score: float
    recommended_action: str
    reason_summary: str


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


class PurchaseOrderSummaryResponse(BaseModel):
    po_id: str
    po_number: str
    vendor_id: str
    vendor_name: str
    po_status: str
    expected_delivery_date: Optional[date]
    actual_delivery_date: Optional[date]


class ReceiptSummaryResponse(BaseModel):
    receipt_id: str
    received_at: Optional[datetime]
    inspection_status: str
    inspection_completed_at: Optional[datetime]


class RequestDetailResponse(BaseModel):
    request: CriticalRequestResponse
    stage_lead_times: list[StageLeadTimeResponse]
    timeline: list[TimelineEventResponse]
    related_po: Optional[PurchaseOrderSummaryResponse]
    receipt: Optional[ReceiptSummaryResponse]
    quality_flags: list[str]


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
    departments: list[FilterOption]
    vendors: list[FilterOption]
    item_categories: list[str]
    criticality_levels: list[str]
    stages: list[str]


class MaintenanceOverviewResponse(BaseModel):
    total_requests: int
    open_requests: int
    delayed_requests: int
    critical_equipment_delayed: int
    avg_downtime_hours: float
    top_bottleneck_stage: Optional[str]
    parts_waiting_delay_hours: float
    repeat_failure_equipment_count: int
    technician_assignment_delay_hours: float
    latest_pipeline_run_status: Optional[str]
    data_quality_status: str


class MaintenanceCriticalRequestResponse(BaseModel):
    priority_rank: int
    maintenance_request_id: str
    request_number: str
    request_title: str
    equipment_id: str
    equipment_name: str
    line_id: str
    line_name: str
    current_stage: str
    current_status: str
    hours_in_current_stage: float
    needed_by_at: datetime
    priority_level: str
    business_impact: str
    equipment_criticality_score: float
    downtime_score: float
    stage_delay_score: float
    production_line_impact_score: float
    needed_by_urgency_score: float
    repeat_failure_score: float
    parts_risk_score: float
    total_priority_score: float
    recommended_action: str
    reason_summary: str


class MaintenanceWorkOrderSummaryResponse(BaseModel):
    work_order_id: str
    assigned_team: str
    assigned_technician_id: Optional[str]
    work_order_status: str
    planned_start_at: Optional[datetime]
    actual_start_at: Optional[datetime]
    actual_completed_at: Optional[datetime]
    required_part_id: Optional[str]
    required_part_name: Optional[str]
    stock_status: Optional[str]


class MaintenanceInspectionResponse(BaseModel):
    inspection_id: str
    inspection_status: str
    inspector_id: Optional[str]
    inspection_started_at: Optional[datetime]
    inspection_completed_at: Optional[datetime]
    failure_reason: Optional[str]


class MaintenanceSensorAlertResponse(BaseModel):
    sensor_alert_id: str
    equipment_id: str
    alert_type: str
    severity: str
    triggered_at: datetime
    resolved_at: Optional[datetime]


class MaintenanceRequestDetailResponse(BaseModel):
    request: MaintenanceCriticalRequestResponse
    stage_lead_times: list[StageLeadTimeResponse]
    timeline: list[TimelineEventResponse]
    work_orders: list[MaintenanceWorkOrderSummaryResponse]
    inspection_results: list[MaintenanceInspectionResponse]
    sensor_alerts: list[MaintenanceSensorAlertResponse]
    quality_flags: list[str]


class EquipmentDelayResponse(BaseModel):
    equipment_id: str
    equipment_name: str
    line_id: str
    line_name: str
    request_count: int
    delayed_request_count: int
    repeat_failure_count: int
    total_downtime_hours: float
    avg_repair_duration_hours: float
    top_failure_mode: str


class ProductionLineDelayResponse(BaseModel):
    line_id: str
    line_name: str
    open_request_count: int
    delayed_request_count: int
    critical_equipment_delayed_count: int
    total_downtime_hours: float
    top_bottleneck_stage: str


class PartsWaitingResponse(BaseModel):
    part_id: str
    part_name: str
    part_category: str
    waiting_request_count: int
    total_wait_hours: float
    avg_wait_hours: float
    critical_spare: bool
    stock_status: str


class MaintenanceFilterMetadataResponse(BaseModel):
    production_lines: list[FilterOption]
    equipment: list[FilterOption]
    equipment_types: list[str]
    technician_teams: list[str]
    part_categories: list[str]
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
