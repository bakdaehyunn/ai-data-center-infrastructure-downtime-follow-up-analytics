from __future__ import annotations

from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.analytics import (
    DowntimeFollowUpQueue,
    EquipmentDelaySummary,
    MaintenanceBottleneckSummary,
    MaintenanceCurrentStatus,
    MaintenanceStageLeadTime,
    PartsWaitingSummary,
    ProductionLineDelaySummary,
)
from app.models.maintenance import (
    Equipment,
    InspectionResult,
    MaintenanceRequest,
    MaintenanceStageEvent,
    MaintenanceWorkOrder,
    Part,
    ProductionLine,
)
from app.models.ops import DataQualityCheckResult, MaintenanceReconciliationIssue, PipelineRun
from app.schemas.analytics import (
    DataQualityCheckResponse,
    EquipmentDelayResponse,
    FilterMetadataResponse,
    FilterOption,
    FollowUpItemResponse,
    InspectionResponse,
    OverviewResponse,
    PartsWaitingResponse,
    PipelineRunResponse,
    ProductionLineDelayResponse,
    RequestDetailResponse,
    SensorAlertResponse,
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
    "inspection_without_completed_work": "Inspection sequence mismatch",
    "parts_waiting_missing_required_part": "Parts data mismatch",
    "state_reconstruction_active_with_completion_event": "State reconstruction mismatch",
    "state_reconstruction_missing_completion_event": "State reconstruction gap",
    "state_reconstruction_missing_stage_event": "State reconstruction gap",
    "state_reconstruction_stage_mismatch": "State reconstruction mismatch",
}


@router.get("/overview", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> OverviewResponse:
    requests = list(db.scalars(select(MaintenanceRequest)))
    current_statuses = list(db.scalars(select(MaintenanceCurrentStatus)))
    equipment_by_id = {equipment.equipment_id: equipment for equipment in db.scalars(select(Equipment))}
    latest_run = _latest_pipeline_run(db)
    failed_quality_count = _failed_quality_count(db, latest_run.pipeline_run_id if latest_run else None)
    top_bottleneck = db.scalar(
        select(MaintenanceBottleneckSummary)
        .where(MaintenanceBottleneckSummary.dimension_type == "STAGE")
        .order_by(desc(MaintenanceBottleneckSummary.total_delay_hours), MaintenanceBottleneckSummary.stage)
        .limit(1)
    )
    parts_waiting_delay = db.scalar(select(func.sum(PartsWaitingSummary.total_wait_hours))) or 0
    repeat_failure_equipment_count = db.scalar(
        select(func.count())
        .select_from(EquipmentDelaySummary)
        .where(EquipmentDelaySummary.repeat_failure_count > 0)
    ) or 0
    technician_assignment_delay = db.scalar(
        select(func.sum(MaintenanceBottleneckSummary.total_delay_hours)).where(
            MaintenanceBottleneckSummary.dimension_type == "STAGE",
            MaintenanceBottleneckSummary.stage == "TECHNICIAN_ASSIGNED",
        )
    ) or 0

    downtime_values = [
        float(request.actual_downtime_hours or request.estimated_downtime_hours)
        for request in requests
    ]

    return OverviewResponse(
        total_requests=len(requests),
        open_requests=sum(1 for request in requests if request.current_status != "COMPLETED"),
        delayed_requests=sum(1 for status in current_statuses if status.is_delayed),
        critical_equipment_delayed=sum(
            1
            for status in current_statuses
            if status.is_delayed
            and equipment_by_id.get(status.equipment_id)
            and equipment_by_id[status.equipment_id].criticality_level == "CRITICAL"
        ),
        avg_downtime_hours=round(mean(downtime_values) if downtime_values else 0, 2),
        top_bottleneck_stage=top_bottleneck.stage if top_bottleneck else None,
        parts_waiting_delay_hours=round(float(parts_waiting_delay), 2),
        repeat_failure_equipment_count=int(repeat_failure_equipment_count),
        technician_assignment_delay_hours=round(float(technician_assignment_delay), 2),
        latest_pipeline_run_status=latest_run.status if latest_run else None,
        data_quality_status="FAILED" if failed_quality_count else "PASS",
    )


@router.get("/follow-ups", response_model=list[FollowUpItemResponse])
def list_follow_ups(
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    priority_level: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[FollowUpItemResponse]:
    stmt = (
        select(DowntimeFollowUpQueue, MaintenanceRequest, Equipment, ProductionLine, MaintenanceCurrentStatus)
        .join(MaintenanceRequest, MaintenanceRequest.maintenance_request_id == DowntimeFollowUpQueue.maintenance_request_id)
        .join(Equipment, Equipment.equipment_id == DowntimeFollowUpQueue.equipment_id)
        .join(ProductionLine, ProductionLine.line_id == DowntimeFollowUpQueue.line_id)
        .join(MaintenanceCurrentStatus, MaintenanceCurrentStatus.maintenance_request_id == DowntimeFollowUpQueue.maintenance_request_id)
    )
    if line_id:
        stmt = stmt.where(DowntimeFollowUpQueue.line_id == line_id)
    if equipment_id:
        stmt = stmt.where(DowntimeFollowUpQueue.equipment_id == equipment_id)
    if priority_level:
        stmt = stmt.where(MaintenanceRequest.priority_level == priority_level)
    if stage:
        stmt = stmt.where(DowntimeFollowUpQueue.current_stage == stage)

    rows = db.execute(stmt.order_by(DowntimeFollowUpQueue.priority_rank).limit(limit)).all()
    return [
        _follow_up_response(queue, request, equipment, line, current)
        for queue, request, equipment, line, current in rows
    ]


@router.get("/follow-ups/{maintenance_request_id}", response_model=RequestDetailResponse)
def get_follow_up_detail(
    maintenance_request_id: str,
    db: Session = Depends(get_db),
) -> RequestDetailResponse:
    request = db.get(MaintenanceRequest, maintenance_request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    equipment = db.get(Equipment, request.equipment_id)
    line = db.get(ProductionLine, request.line_id)
    current = db.get(MaintenanceCurrentStatus, maintenance_request_id)
    queue = db.get(DowntimeFollowUpQueue, maintenance_request_id)
    if equipment is None or line is None or current is None:
        raise HTTPException(status_code=404, detail="Maintenance analytics not found for request")

    stage_lead_times = db.scalars(
        select(MaintenanceStageLeadTime)
        .where(MaintenanceStageLeadTime.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceStageLeadTime.entered_at)
    ).all()
    timeline = db.scalars(
        select(MaintenanceStageEvent)
        .where(MaintenanceStageEvent.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceStageEvent.occurred_at, MaintenanceStageEvent.event_id)
    ).all()
    work_orders = db.scalars(
        select(MaintenanceWorkOrder)
        .where(MaintenanceWorkOrder.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceWorkOrder.work_order_id)
    ).all()
    inspections = db.scalars(
        select(InspectionResult)
        .where(InspectionResult.maintenance_request_id == maintenance_request_id)
        .order_by(InspectionResult.inspection_id)
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
        inspection_results=[_inspection_response(inspection) for inspection in inspections],
        sensor_alerts=[_sensor_alert_response(alert) for alert in request.sensor_alerts],
        quality_flags=_quality_flags_for_request(db, maintenance_request_id),
    )


@router.get("/follow-ups/{maintenance_request_id}/timeline", response_model=list[TimelineEventResponse])
def get_follow_up_timeline(
    maintenance_request_id: str,
    db: Session = Depends(get_db),
) -> list[TimelineEventResponse]:
    if db.get(MaintenanceRequest, maintenance_request_id) is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    events = db.scalars(
        select(MaintenanceStageEvent)
        .where(MaintenanceStageEvent.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceStageEvent.occurred_at, MaintenanceStageEvent.event_id)
    ).all()
    return [_timeline_event_response(event) for event in events]


@router.get("/downtime/stages", response_model=list[StageBottleneckResponse])
def list_stage_downtime(
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[StageBottleneckResponse]:
    stmt = select(MaintenanceBottleneckSummary).where(MaintenanceBottleneckSummary.dimension_type == "STAGE")
    if stage:
        stmt = stmt.where(MaintenanceBottleneckSummary.stage == stage)
    rows = db.scalars(
        stmt.order_by(desc(MaintenanceBottleneckSummary.total_delay_hours), MaintenanceBottleneckSummary.stage)
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


@router.get("/equipment/delays", response_model=list[EquipmentDelayResponse])
def list_equipment_delays(limit: int = 20, db: Session = Depends(get_db)) -> list[EquipmentDelayResponse]:
    rows = db.scalars(
        select(EquipmentDelaySummary)
        .order_by(desc(EquipmentDelaySummary.total_downtime_hours), EquipmentDelaySummary.equipment_name)
        .limit(limit)
    ).all()
    return [EquipmentDelayResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/lines/delays", response_model=list[ProductionLineDelayResponse])
def list_line_delays(db: Session = Depends(get_db)) -> list[ProductionLineDelayResponse]:
    rows = db.scalars(
        select(ProductionLineDelaySummary)
        .order_by(desc(ProductionLineDelaySummary.total_downtime_hours), ProductionLineDelaySummary.line_name)
    ).all()
    return [ProductionLineDelayResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/parts/waiting", response_model=list[PartsWaitingResponse])
def list_parts_waiting(db: Session = Depends(get_db)) -> list[PartsWaitingResponse]:
    rows = db.scalars(
        select(PartsWaitingSummary)
        .order_by(desc(PartsWaitingSummary.total_wait_hours), PartsWaitingSummary.part_name)
    ).all()
    return [PartsWaitingResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/metadata/filters", response_model=FilterMetadataResponse)
def get_filter_metadata(db: Session = Depends(get_db)) -> FilterMetadataResponse:
    lines = db.scalars(select(ProductionLine).order_by(ProductionLine.line_name)).all()
    equipment = db.scalars(select(Equipment).order_by(Equipment.equipment_name)).all()
    work_orders = db.scalars(select(MaintenanceWorkOrder)).all()
    parts = db.scalars(select(Part)).all()
    requests = db.scalars(select(MaintenanceRequest)).all()
    follow_up_stages = db.scalars(
        select(DowntimeFollowUpQueue.current_stage).distinct().order_by(DowntimeFollowUpQueue.current_stage)
    ).all()
    return FilterMetadataResponse(
        production_lines=[FilterOption(id=line.line_id, name=line.line_name) for line in lines],
        equipment=[FilterOption(id=item.equipment_id, name=item.equipment_name) for item in equipment],
        equipment_types=sorted({item.equipment_type for item in equipment}),
        technician_teams=sorted({work_order.assigned_team for work_order in work_orders}),
        part_categories=sorted({part.part_category for part in parts}),
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
    request: MaintenanceRequest,
    equipment: Equipment,
    line: ProductionLine,
    current: MaintenanceCurrentStatus,
) -> FollowUpItemResponse:
    return FollowUpItemResponse(
        priority_rank=queue.priority_rank,
        maintenance_request_id=request.maintenance_request_id,
        request_number=request.request_number,
        request_title=request.request_title,
        equipment_id=equipment.equipment_id,
        equipment_name=equipment.equipment_name,
        line_id=line.line_id,
        line_name=line.line_name,
        current_stage=request.current_stage,
        current_status=request.current_status,
        hours_in_current_stage=float(current.hours_in_current_stage),
        needed_by_at=request.needed_by_at,
        priority_level=request.priority_level,
        business_impact=request.business_impact,
        equipment_criticality_score=float(queue.equipment_criticality_score),
        downtime_score=float(queue.downtime_score),
        stage_delay_score=float(queue.stage_delay_score),
        production_line_impact_score=float(queue.production_line_impact_score),
        needed_by_urgency_score=float(queue.needed_by_urgency_score),
        repeat_failure_score=float(queue.repeat_failure_score),
        parts_risk_score=float(queue.parts_risk_score),
        total_priority_score=float(queue.total_priority_score),
        recommended_action=queue.recommended_action,
        reason_summary=queue.reason_summary,
    )


def _empty_queue_row(request: MaintenanceRequest, current: MaintenanceCurrentStatus) -> DowntimeFollowUpQueue:
    return DowntimeFollowUpQueue(
        maintenance_request_id=request.maintenance_request_id,
        priority_rank=0,
        equipment_id=request.equipment_id,
        line_id=request.line_id,
        current_stage=request.current_stage,
        equipment_criticality_score=0,
        downtime_score=0,
        stage_delay_score=0,
        production_line_impact_score=0,
        needed_by_urgency_score=0,
        repeat_failure_score=0,
        parts_risk_score=0,
        total_priority_score=0,
        recommended_action="No follow-up required" if request.current_status == "COMPLETED" else "Review maintenance request status",
        reason_summary=f"Request is {request.current_status} in {current.current_stage}.",
    )


def _stage_lead_time_response(row: MaintenanceStageLeadTime) -> StageLeadTimeResponse:
    return StageLeadTimeResponse(
        stage=row.stage,
        entered_at=row.entered_at,
        exited_at=row.exited_at,
        duration_hours=float(row.duration_hours),
        threshold_hours=float(row.threshold_hours),
        is_bottleneck=row.is_bottleneck,
        delay_hours=float(row.delay_hours),
    )


def _timeline_event_response(event: MaintenanceStageEvent) -> TimelineEventResponse:
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


def _work_order_response(db: Session, work_order: MaintenanceWorkOrder) -> WorkOrderSummaryResponse:
    part = db.get(Part, work_order.required_part_id) if work_order.required_part_id else None
    return WorkOrderSummaryResponse(
        work_order_id=work_order.work_order_id,
        assigned_team=work_order.assigned_team,
        assigned_technician_id=work_order.assigned_technician_id,
        work_order_status=work_order.work_order_status,
        planned_start_at=work_order.planned_start_at,
        actual_start_at=work_order.actual_start_at,
        actual_completed_at=work_order.actual_completed_at,
        required_part_id=work_order.required_part_id,
        required_part_name=part.part_name if part else None,
        stock_status=part.stock_status if part else None,
    )


def _inspection_response(inspection: InspectionResult) -> InspectionResponse:
    return InspectionResponse(
        inspection_id=inspection.inspection_id,
        inspection_status=inspection.inspection_status,
        inspector_id=inspection.inspector_id,
        inspection_started_at=inspection.inspection_started_at,
        inspection_completed_at=inspection.inspection_completed_at,
        failure_reason=inspection.failure_reason,
    )


def _sensor_alert_response(alert) -> SensorAlertResponse:
    return SensorAlertResponse(
        sensor_alert_id=alert.sensor_alert_id,
        equipment_id=alert.equipment_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        triggered_at=alert.triggered_at,
        resolved_at=alert.resolved_at,
    )


def _quality_flags_for_request(db: Session, maintenance_request_id: str) -> list[str]:
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
        if any(maintenance_request_id in key for key in failed_keys):
            flags.append(f"{check.target_table}.{check.check_name}: {check.message}")
    reconciliation_issues = db.scalars(
        select(MaintenanceReconciliationIssue)
        .where(
            MaintenanceReconciliationIssue.pipeline_run_id == latest_run.pipeline_run_id,
            MaintenanceReconciliationIssue.maintenance_request_id == maintenance_request_id,
            MaintenanceReconciliationIssue.status == "OPEN",
        )
        .order_by(MaintenanceReconciliationIssue.severity, MaintenanceReconciliationIssue.issue_type)
    ).all()
    flags.extend(
        _reconciliation_quality_flag(issue)
        for issue in reconciliation_issues
    )
    return flags


def _reconciliation_quality_flag(issue: MaintenanceReconciliationIssue) -> str:
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
