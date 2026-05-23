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
    total_priority_score: float
    recommended_action: str
    reason_summary: str


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


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
