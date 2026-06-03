from __future__ import annotations

from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.analytics import (
    DowntimeFollowUpQueue,
    AssetDelaySummary,
    InfrastructureBottleneckSummary,
    IncidentCurrentStatus,
    IncidentStageLeadTime,
    SpareWaitingSummary,
    ZoneDelaySummary,
)
from app.models.infrastructure import (
    InfrastructureAsset,
    ValidationResult,
    InfrastructureIncident,
    IncidentStageEvent,
    FacilityWorkOrder,
    CriticalSpare,
    InfrastructureZone,
)
from app.models.ops import DataQualityCheckResult, InfrastructureReconciliationIssue, PipelineRun
from app.schemas.analytics import (
    DataQualityCheckResponse,
    InfrastructureAssetDelayResponse,
    FilterMetadataResponse,
    FilterOption,
    FollowUpItemResponse,
    ValidationResponse,
    OverviewResponse,
    SpareWaitingResponse,
    PipelineRunResponse,
    InfrastructureZoneDelayResponse,
    RequestDetailResponse,
    TelemetryAlertResponse,
    StageBottleneckResponse,
    StageLeadTimeResponse,
    TimelineEventResponse,
    WorkOrderSummaryResponse,
    string_list,
)

router = APIRouter(prefix="/api")


RECONCILIATION_FLAG_LABELS = {
    "analytics_output_missing_current_status": "Analytics output gap",
    "event_sequence_before_request": "Event timeline mismatch",
    "validation_without_completed_work": "Validation sequence mismatch",
    "spare_waiting_missing_required_spare": "Spare or vendor evidence mismatch",
    "state_reconstruction_active_with_completion_event": "State reconstruction mismatch",
    "state_reconstruction_missing_completion_event": "State reconstruction gap",
    "state_reconstruction_missing_stage_event": "State reconstruction gap",
    "state_reconstruction_stage_mismatch": "State reconstruction mismatch",
}


@router.get("/overview", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> OverviewResponse:
    requests = list(db.scalars(select(InfrastructureIncident)))
    current_statuses = list(db.scalars(select(IncidentCurrentStatus)))
    asset_by_id = {asset.asset_id: asset for asset in db.scalars(select(InfrastructureAsset))}
    latest_run = _latest_pipeline_run(db)
    failed_quality_count = _failed_quality_count(db, latest_run.pipeline_run_id if latest_run else None)
    top_bottleneck = db.scalar(
        select(InfrastructureBottleneckSummary)
        .where(InfrastructureBottleneckSummary.dimension_type == "STAGE")
        .order_by(desc(InfrastructureBottleneckSummary.total_delay_hours), InfrastructureBottleneckSummary.stage)
        .limit(1)
    )
    spare_waiting_delay = db.scalar(select(func.sum(SpareWaitingSummary.total_wait_hours))) or 0
    repeat_failure_asset_count = db.scalar(
        select(func.count())
        .select_from(AssetDelaySummary)
        .where(AssetDelaySummary.repeat_failure_count > 0)
    ) or 0
    engineer_assignment_delay = db.scalar(
        select(func.sum(InfrastructureBottleneckSummary.total_delay_hours)).where(
            InfrastructureBottleneckSummary.dimension_type == "STAGE",
            InfrastructureBottleneckSummary.stage == "ENGINEER_ASSIGNED",
        )
    ) or 0

    downtime_values = [
        float(request.actual_downtime_hours or request.estimated_downtime_hours)
        for request in requests
    ]

    return OverviewResponse(
        total_requests=len(requests),
        open_requests=sum(1 for request in requests if request.current_status != "RESTORED"),
        delayed_requests=sum(1 for status in current_statuses if status.is_delayed),
        critical_asset_delayed=sum(
            1
            for status in current_statuses
            if status.is_delayed
            and asset_by_id.get(status.asset_id)
            and asset_by_id[status.asset_id].criticality_level == "CRITICAL"
        ),
        avg_downtime_hours=round(mean(downtime_values) if downtime_values else 0, 2),
        top_bottleneck_stage=top_bottleneck.stage if top_bottleneck else None,
        spare_waiting_delay_hours=round(float(spare_waiting_delay), 2),
        repeat_failure_asset_count=int(repeat_failure_asset_count),
        engineer_assignment_delay_hours=round(float(engineer_assignment_delay), 2),
        latest_pipeline_run_status=latest_run.status if latest_run else None,
        data_quality_status="FAILED" if failed_quality_count else "PASS",
    )


@router.get("/follow-ups", response_model=list[FollowUpItemResponse])
def list_follow_ups(
    zone_id: Optional[str] = None,
    asset_id: Optional[str] = None,
    priority_level: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[FollowUpItemResponse]:
    stmt = (
        select(DowntimeFollowUpQueue, InfrastructureIncident, InfrastructureAsset, InfrastructureZone, IncidentCurrentStatus)
        .join(InfrastructureIncident, InfrastructureIncident.incident_id == DowntimeFollowUpQueue.incident_id)
        .join(InfrastructureAsset, InfrastructureAsset.asset_id == DowntimeFollowUpQueue.asset_id)
        .join(InfrastructureZone, InfrastructureZone.zone_id == DowntimeFollowUpQueue.zone_id)
        .join(IncidentCurrentStatus, IncidentCurrentStatus.incident_id == DowntimeFollowUpQueue.incident_id)
    )
    if zone_id:
        stmt = stmt.where(DowntimeFollowUpQueue.zone_id == zone_id)
    if asset_id:
        stmt = stmt.where(DowntimeFollowUpQueue.asset_id == asset_id)
    if priority_level:
        stmt = stmt.where(InfrastructureIncident.priority_level == priority_level)
    if stage:
        stmt = stmt.where(DowntimeFollowUpQueue.current_stage == stage)

    rows = db.execute(stmt.order_by(DowntimeFollowUpQueue.priority_rank).limit(limit)).all()
    return [
        _follow_up_response(queue, request, equipment, line, current)
        for queue, request, equipment, line, current in rows
    ]


@router.get("/follow-ups/{incident_id}", response_model=RequestDetailResponse)
def get_follow_up_detail(
    incident_id: str,
    db: Session = Depends(get_db),
) -> RequestDetailResponse:
    request = db.get(InfrastructureIncident, incident_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Infrastructure incident not found")

    equipment = db.get(InfrastructureAsset, request.asset_id)
    line = db.get(InfrastructureZone, request.zone_id)
    current = db.get(IncidentCurrentStatus, incident_id)
    queue = db.get(DowntimeFollowUpQueue, incident_id)
    if equipment is None or line is None or current is None:
        raise HTTPException(status_code=404, detail="Infrastructure analytics not found for incident")

    stage_lead_times = db.scalars(
        select(IncidentStageLeadTime)
        .where(IncidentStageLeadTime.incident_id == incident_id)
        .order_by(IncidentStageLeadTime.entered_at)
    ).all()
    timeline = db.scalars(
        select(IncidentStageEvent)
        .where(IncidentStageEvent.incident_id == incident_id)
        .order_by(IncidentStageEvent.occurred_at, IncidentStageEvent.event_id)
    ).all()
    work_orders = db.scalars(
        select(FacilityWorkOrder)
        .where(FacilityWorkOrder.incident_id == incident_id)
        .order_by(FacilityWorkOrder.work_order_id)
    ).all()
    validations = db.scalars(
        select(ValidationResult)
        .where(ValidationResult.incident_id == incident_id)
        .order_by(ValidationResult.validation_id)
    ).all()

    return RequestDetailResponse(
        request=_follow_up_response(
            queue or _empty_queue_row(request, current),
            request,
            equipment,
            line,
            current,
        ),
        stage_lead_times=[_stage_lead_time_response(row) for row in stage_lead_times],
        timeline=[_timeline_event_response(event) for event in timeline],
        work_orders=[_work_order_response(db, work_order) for work_order in work_orders],
        validation_results=[_validation_response(validation) for validation in validations],
        telemetry_alerts=[_telemetry_alert_response(alert) for alert in request.telemetry_alerts],
        quality_flags=_quality_flags_for_request(db, incident_id),
    )


@router.get("/follow-ups/{incident_id}/timeline", response_model=list[TimelineEventResponse])
def get_follow_up_timeline(
    incident_id: str,
    db: Session = Depends(get_db),
) -> list[TimelineEventResponse]:
    if db.get(InfrastructureIncident, incident_id) is None:
        raise HTTPException(status_code=404, detail="Infrastructure incident not found")
    events = db.scalars(
        select(IncidentStageEvent)
        .where(IncidentStageEvent.incident_id == incident_id)
        .order_by(IncidentStageEvent.occurred_at, IncidentStageEvent.event_id)
    ).all()
    return [_timeline_event_response(event) for event in events]


@router.get("/downtime/stages", response_model=list[StageBottleneckResponse])
def list_stage_downtime(
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[StageBottleneckResponse]:
    stmt = select(InfrastructureBottleneckSummary).where(InfrastructureBottleneckSummary.dimension_type == "STAGE")
    if stage:
        stmt = stmt.where(InfrastructureBottleneckSummary.stage == stage)
    rows = db.scalars(
        stmt.order_by(desc(InfrastructureBottleneckSummary.total_delay_hours), InfrastructureBottleneckSummary.stage)
    ).all()
    return [
        StageBottleneckResponse(
            stage=row.stage,
            request_count=row.request_count,
            delayed_count=row.delayed_count,
            delay_rate=float(row.delay_rate),
            avg_duration_hours=float(row.avg_duration_hours),
            p90_duration_hours=float(row.p90_duration_hours),
            total_delay_hours=float(row.total_delay_hours),
        )
        for row in rows
    ]


@router.get("/equipment/delays", response_model=list[InfrastructureAssetDelayResponse])
def list_equipment_delays(limit: int = 20, db: Session = Depends(get_db)) -> list[InfrastructureAssetDelayResponse]:
    rows = db.scalars(
        select(AssetDelaySummary)
        .order_by(desc(AssetDelaySummary.total_downtime_hours), AssetDelaySummary.asset_name)
        .limit(limit)
    ).all()
    return [InfrastructureAssetDelayResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/assets/delays", response_model=list[InfrastructureAssetDelayResponse])
def list_asset_delays(limit: int = 20, db: Session = Depends(get_db)) -> list[InfrastructureAssetDelayResponse]:
    return list_equipment_delays(limit=limit, db=db)


@router.get("/lines/delays", response_model=list[InfrastructureZoneDelayResponse])
def list_line_delays(db: Session = Depends(get_db)) -> list[InfrastructureZoneDelayResponse]:
    rows = db.scalars(
        select(ZoneDelaySummary)
        .order_by(desc(ZoneDelaySummary.total_downtime_hours), ZoneDelaySummary.zone_name)
    ).all()
    return [InfrastructureZoneDelayResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/zones/delays", response_model=list[InfrastructureZoneDelayResponse])
def list_zone_delays(db: Session = Depends(get_db)) -> list[InfrastructureZoneDelayResponse]:
    return list_line_delays(db=db)


@router.get("/parts/waiting", response_model=list[SpareWaitingResponse])
def list_spare_waiting(db: Session = Depends(get_db)) -> list[SpareWaitingResponse]:
    rows = db.scalars(
        select(SpareWaitingSummary)
        .order_by(desc(SpareWaitingSummary.total_wait_hours), SpareWaitingSummary.spare_name)
    ).all()
    return [SpareWaitingResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/spares/waiting", response_model=list[SpareWaitingResponse])
def list_spares_waiting(db: Session = Depends(get_db)) -> list[SpareWaitingResponse]:
    return list_spare_waiting(db=db)


@router.get("/metadata/filters", response_model=FilterMetadataResponse)
def get_filter_metadata(db: Session = Depends(get_db)) -> FilterMetadataResponse:
    lines = db.scalars(select(InfrastructureZone).order_by(InfrastructureZone.zone_name)).all()
    assets = db.scalars(select(InfrastructureAsset).order_by(InfrastructureAsset.asset_name)).all()
    work_orders = db.scalars(select(FacilityWorkOrder)).all()
    parts = db.scalars(select(CriticalSpare)).all()
    requests = db.scalars(select(InfrastructureIncident)).all()
    follow_up_stages = db.scalars(
        select(DowntimeFollowUpQueue.current_stage).distinct().order_by(DowntimeFollowUpQueue.current_stage)
    ).all()
    return FilterMetadataResponse(
        infrastructure_zones=[FilterOption(id=line.zone_id, name=line.zone_name) for line in lines],
        assets=[FilterOption(id=item.asset_id, name=item.asset_name) for item in assets],
        asset_types=sorted({item.asset_type for item in assets}),
        facilities_teams=sorted({work_order.assigned_team for work_order in work_orders}),
        spare_categories=sorted({part.spare_category for part in parts}),
        priority_levels=sorted({request.priority_level for request in requests}),
        request_types=sorted({request.request_type for request in requests}),
        failure_modes=sorted({request.failure_mode for request in requests}),
        stages=list(follow_up_stages),
    )


@router.get("/pipeline-runs", response_model=list[PipelineRunResponse])
def list_pipeline_runs(limit: int = 10, db: Session = Depends(get_db)) -> list[PipelineRunResponse]:
    rows = db.scalars(select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(limit)).all()
    return [PipelineRunResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/data-quality/checks", response_model=list[DataQualityCheckResponse])
def list_data_quality_checks(
    pipeline_run_id: Optional[str] = None,
    status: Optional[str] = None,
    all_runs: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[DataQualityCheckResponse]:
    stmt = select(DataQualityCheckResult)
    if not all_runs:
        latest_run_id = pipeline_run_id
        if latest_run_id is None:
            latest_run = _latest_pipeline_run(db)
            latest_run_id = latest_run.pipeline_run_id if latest_run else None
        if latest_run_id is None:
            return []
        stmt = stmt.where(DataQualityCheckResult.pipeline_run_id == latest_run_id)
    elif pipeline_run_id:
        stmt = stmt.where(DataQualityCheckResult.pipeline_run_id == pipeline_run_id)
    if status:
        stmt = stmt.where(DataQualityCheckResult.status == status)
    rows = db.scalars(stmt.order_by(desc(DataQualityCheckResult.created_at)).limit(limit)).all()
    return [DataQualityCheckResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/data-quality/checks/{check_result_id}", response_model=DataQualityCheckResponse)
def get_data_quality_check(check_result_id: str, db: Session = Depends(get_db)) -> DataQualityCheckResponse:
    row = db.get(DataQualityCheckResult, check_result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Data quality check not found")
    return DataQualityCheckResponse.model_validate(row, from_attributes=True)


def _follow_up_response(
    queue: DowntimeFollowUpQueue,
    request: InfrastructureIncident,
    equipment: InfrastructureAsset,
    line: InfrastructureZone,
    current: IncidentCurrentStatus,
) -> FollowUpItemResponse:
    return FollowUpItemResponse(
        priority_rank=queue.priority_rank,
        incident_id=request.incident_id,
        request_number=request.request_number,
        request_title=request.request_title,
        asset_id=equipment.asset_id,
        asset_name=equipment.asset_name,
        zone_id=line.zone_id,
        zone_name=line.zone_name,
        current_stage=request.current_stage,
        current_status=request.current_status,
        hours_in_current_stage=float(current.hours_in_current_stage),
        needed_by_at=request.needed_by_at,
        priority_level=request.priority_level,
        business_impact=request.business_impact,
        asset_criticality_score=float(queue.asset_criticality_score),
        downtime_score=float(queue.downtime_score),
        stage_delay_score=float(queue.stage_delay_score),
        infrastructure_zone_impact_score=float(queue.infrastructure_zone_impact_score),
        needed_by_urgency_score=float(queue.needed_by_urgency_score),
        repeat_failure_score=float(queue.repeat_failure_score),
        spare_risk_score=float(queue.spare_risk_score),
        total_priority_score=float(queue.total_priority_score),
        recommended_action=queue.recommended_action,
        reason_summary=queue.reason_summary,
    )


def _empty_queue_row(request: InfrastructureIncident, current: IncidentCurrentStatus) -> DowntimeFollowUpQueue:
    return DowntimeFollowUpQueue(
        incident_id=request.incident_id,
        priority_rank=0,
        asset_id=request.asset_id,
        zone_id=request.zone_id,
        current_stage=request.current_stage,
        asset_criticality_score=0,
        downtime_score=0,
        stage_delay_score=0,
        infrastructure_zone_impact_score=0,
        needed_by_urgency_score=0,
        repeat_failure_score=0,
        spare_risk_score=0,
        total_priority_score=0,
        recommended_action="No follow-up required" if request.current_status == "RESTORED" else "Review infrastructure incident status",
        reason_summary=f"Incident is {request.current_status} in {current.current_stage}.",
    )


def _stage_lead_time_response(row: IncidentStageLeadTime) -> StageLeadTimeResponse:
    return StageLeadTimeResponse(
        stage=row.stage,
        entered_at=row.entered_at,
        exited_at=row.exited_at,
        duration_hours=float(row.duration_hours),
        threshold_hours=float(row.threshold_hours),
        is_bottleneck=row.is_bottleneck,
        delay_hours=float(row.delay_hours),
    )


def _timeline_event_response(event: IncidentStageEvent) -> TimelineEventResponse:
    metadata = event.metadata_json or {}
    return TimelineEventResponse(
        event_id=event.event_id,
        stage=event.stage,
        event_type=event.event_type,
        event_status=event.event_status,
        occurred_at=event.occurred_at,
        actor_type=event.actor_type,
        reason_code=event.reason_code,
        message=metadata.get("message"),
    )


def _work_order_response(db: Session, work_order: FacilityWorkOrder) -> WorkOrderSummaryResponse:
    part = db.get(CriticalSpare, work_order.required_spare_id) if work_order.required_spare_id else None
    return WorkOrderSummaryResponse(
        work_order_id=work_order.work_order_id,
        assigned_team=work_order.assigned_team,
        assigned_engineer_id=work_order.assigned_engineer_id,
        work_order_status=work_order.work_order_status,
        planned_start_at=work_order.planned_start_at,
        actual_start_at=work_order.actual_start_at,
        actual_completed_at=work_order.actual_completed_at,
        required_spare_id=work_order.required_spare_id,
        required_spare_name=part.spare_name if part else None,
        stock_status=part.stock_status if part else None,
    )


def _validation_response(validation: ValidationResult) -> ValidationResponse:
    return ValidationResponse(
        validation_id=validation.validation_id,
        validation_status=validation.validation_status,
        validator_id=validation.validator_id,
        validation_started_at=validation.validation_started_at,
        validation_completed_at=validation.validation_completed_at,
        failure_reason=validation.failure_reason,
    )


def _telemetry_alert_response(alert) -> TelemetryAlertResponse:
    return TelemetryAlertResponse(
        telemetry_alert_id=alert.telemetry_alert_id,
        asset_id=alert.asset_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        triggered_at=alert.triggered_at,
        resolved_at=alert.resolved_at,
    )


def _quality_flags_for_request(db: Session, incident_id: str) -> list[str]:
    latest_run = _latest_pipeline_run(db)
    if latest_run is None:
        return []
    failed_checks = db.scalars(
        select(DataQualityCheckResult).where(
            DataQualityCheckResult.pipeline_run_id == latest_run.pipeline_run_id,
            DataQualityCheckResult.status != "PASS",
        )
    ).all()
    flags: list[str] = []
    for check in failed_checks:
        failed_keys = string_list(check.sample_failed_keys)
        if any(incident_id in key for key in failed_keys):
            flags.append(f"{check.target_table}.{check.check_name}: {check.message}")
    reconciliation_issues = db.scalars(
        select(InfrastructureReconciliationIssue)
        .where(
            InfrastructureReconciliationIssue.pipeline_run_id == latest_run.pipeline_run_id,
            InfrastructureReconciliationIssue.incident_id == incident_id,
            InfrastructureReconciliationIssue.status == "OPEN",
        )
        .order_by(InfrastructureReconciliationIssue.severity, InfrastructureReconciliationIssue.issue_type)
    ).all()
    flags.extend(
        _reconciliation_quality_flag(issue)
        for issue in reconciliation_issues
    )
    return flags


def _reconciliation_quality_flag(issue: InfrastructureReconciliationIssue) -> str:
    label = RECONCILIATION_FLAG_LABELS.get(issue.issue_type, "Reconciliation issue")
    return f"{label}: {issue.message}"


def _latest_pipeline_run(db: Session) -> PipelineRun | None:
    return db.scalar(select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(1))


def _failed_quality_count(db: Session, pipeline_run_id: str | None) -> int:
    if pipeline_run_id is None:
        return 0
    return db.scalar(
        select(func.count())
        .select_from(DataQualityCheckResult)
        .where(
            DataQualityCheckResult.pipeline_run_id == pipeline_run_id,
            DataQualityCheckResult.status != "PASS",
        )
    ) or 0
