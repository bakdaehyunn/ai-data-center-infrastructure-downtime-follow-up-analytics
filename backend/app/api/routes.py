from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.analytics import (
    BottleneckSummary,
    CriticalRequestQueue,
    CriticalMaintenanceQueue,
    EquipmentDelaySummary,
    MaintenanceBottleneckSummary,
    MaintenanceCurrentStatus,
    MaintenanceStageLeadTime,
    PartsWaitingSummary,
    ProductionLineDelaySummary,
    RequestCurrentStatus,
    RequestStageLeadTime,
    VendorDelaySummary,
)
from app.models.core import Department, Item, ProcurementStageEvent, PurchaseOrder, PurchaseRequest, Receipt, Vendor
from app.models.maintenance import (
    Equipment,
    InspectionResult,
    MaintenanceRequest,
    MaintenanceStageEvent,
    MaintenanceWorkOrder,
    Part,
    ProductionLine,
    SensorAlert,
)
from app.models.ops import DataQualityCheckResult, PipelineRun
from app.sample_data.maintenance_scenarios import MAINTENANCE_STAGE_FLOW
from app.sample_data.scenarios import STAGE_FLOW
from app.schemas.analytics import (
    CriticalRequestResponse,
    DataQualityCheckResponse,
    EquipmentDelayResponse,
    FilterMetadataResponse,
    FilterOption,
    MaintenanceCriticalRequestResponse,
    MaintenanceFilterMetadataResponse,
    MaintenanceInspectionResponse,
    MaintenanceOverviewResponse,
    MaintenanceRequestDetailResponse,
    MaintenanceSensorAlertResponse,
    MaintenanceWorkOrderSummaryResponse,
    OverviewResponse,
    PartsWaitingResponse,
    PipelineRunResponse,
    ProductionLineDelayResponse,
    PurchaseOrderSummaryResponse,
    ReceiptSummaryResponse,
    RequestDetailResponse,
    StageLeadTimeResponse,
    StageBottleneckResponse,
    TimelineEventResponse,
    VendorBottleneckResponse,
    string_list,
)


router = APIRouter()


@router.get("/overview", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> OverviewResponse:
    requests = list(db.scalars(select(PurchaseRequest)))
    current_statuses = list(db.scalars(select(RequestCurrentStatus)))
    lead_times = list(db.scalars(select(RequestStageLeadTime)))
    stage_summaries = list(
        db.scalars(
            select(BottleneckSummary).where(BottleneckSummary.dimension_type == "STAGE")
        )
    )
    latest_run = _latest_pipeline_run(db)

    duration_by_request: dict[str, float] = defaultdict(float)
    for lead_time in lead_times:
        duration_by_request[lead_time.request_id] += float(lead_time.duration_hours)

    total_delay_hours = sum(float(summary.total_delay_hours) for summary in stage_summaries)
    top_stage = max(
        stage_summaries,
        key=lambda summary: float(summary.total_delay_hours),
        default=None,
    )

    return OverviewResponse(
        total_requests=len(requests),
        open_requests=sum(1 for request in requests if request.current_status != "CLOSED"),
        delayed_requests=sum(1 for status in current_statuses if status.is_delayed),
        critical_open_requests=sum(
            1
            for status in current_statuses
            if status.criticality_level == "CRITICAL" and status.current_status != "CLOSED"
        ),
        avg_cycle_time_hours=round(mean(duration_by_request.values()), 2)
        if duration_by_request
        else 0,
        total_delay_hours=round(total_delay_hours, 2),
        top_bottleneck_stage=top_stage.stage if top_stage else None,
        latest_pipeline_run_status=latest_run.status if latest_run else None,
        data_quality_status=_data_quality_status(db, latest_run.pipeline_run_id if latest_run else None),
    )


@router.get("/bottlenecks/stages", response_model=list[StageBottleneckResponse])
def list_stage_bottlenecks(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    stage: Optional[str] = None,
    department_id: Optional[str] = None,
    vendor_id: Optional[str] = None,
    item_category: Optional[str] = None,
    criticality_level: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[StageBottleneckResponse]:
    if department_id or vendor_id or item_category or criticality_level:
        return _filtered_stage_bottlenecks(
            db=db,
            from_date=from_date,
            to_date=to_date,
            stage=stage,
            department_id=department_id,
            vendor_id=vendor_id,
            item_category=item_category,
            criticality_level=criticality_level,
        )

    stmt = select(BottleneckSummary).where(BottleneckSummary.dimension_type == "STAGE")
    if from_date:
        stmt = stmt.where(BottleneckSummary.summary_date >= from_date)
    if to_date:
        stmt = stmt.where(BottleneckSummary.summary_date <= to_date)
    if stage:
        stmt = stmt.where(BottleneckSummary.stage == stage)

    summaries = db.scalars(
        stmt.order_by(BottleneckSummary.total_delay_hours.desc(), BottleneckSummary.stage)
    ).all()
    return [
        StageBottleneckResponse(
            stage=summary.stage,
            request_count=summary.request_count,
            delayed_count=summary.delayed_count,
            delay_rate=round(summary.delayed_count / summary.request_count, 4)
            if summary.request_count
            else 0,
            avg_duration_hours=float(summary.avg_duration_hours),
            p90_duration_hours=float(summary.p90_duration_hours),
            total_delay_hours=float(summary.total_delay_hours),
        )
        for summary in summaries
    ]


@router.get("/bottlenecks/vendors", response_model=list[VendorBottleneckResponse])
def list_vendor_bottlenecks(
    vendor_id: Optional[str] = None,
    stage: Optional[str] = None,
    department_id: Optional[str] = None,
    item_category: Optional[str] = None,
    criticality_level: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[VendorBottleneckResponse]:
    if stage or department_id or item_category or criticality_level:
        return _filtered_vendor_bottlenecks(
            db=db,
            vendor_id=vendor_id,
            stage=stage,
            department_id=department_id,
            item_category=item_category,
            criticality_level=criticality_level,
        )

    stmt = select(VendorDelaySummary, Vendor).join(
        Vendor,
        Vendor.vendor_id == VendorDelaySummary.vendor_id,
    )
    if vendor_id:
        stmt = stmt.where(VendorDelaySummary.vendor_id == vendor_id)

    total_delay_by_vendor = _vendor_total_delay_hours(db)
    rows = db.execute(
        stmt.order_by(VendorDelaySummary.delay_rate.desc(), VendorDelaySummary.delayed_po_count.desc())
    ).all()

    return [
        VendorBottleneckResponse(
            vendor_id=summary.vendor_id,
            vendor_name=vendor.vendor_name,
            total_po_count=summary.total_po_count,
            delayed_po_count=summary.delayed_po_count,
            delay_rate=float(summary.delay_rate),
            avg_confirmation_hours=float(summary.avg_confirmation_hours),
            avg_delivery_delay_days=float(summary.avg_delivery_delay_days),
            reliability_tier=summary.reliability_tier,
            total_delay_hours=round(total_delay_by_vendor.get(summary.vendor_id, 0), 2),
        )
        for summary, vendor in rows
    ]


@router.get("/requests/critical", response_model=list[CriticalRequestResponse])
def list_critical_requests(
    limit: int = Query(default=25, ge=1, le=100),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    department_id: Optional[str] = None,
    vendor_id: Optional[str] = None,
    item_category: Optional[str] = None,
    criticality_level: Optional[str] = None,
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[CriticalRequestResponse]:
    stmt = (
        select(CriticalRequestQueue, PurchaseRequest, Department, RequestCurrentStatus)
        .join(PurchaseRequest, PurchaseRequest.request_id == CriticalRequestQueue.request_id)
        .join(Department, Department.department_id == PurchaseRequest.department_id)
        .join(RequestCurrentStatus, RequestCurrentStatus.request_id == PurchaseRequest.request_id)
    )
    if from_date:
        stmt = stmt.where(PurchaseRequest.needed_by_date >= from_date)
    if to_date:
        stmt = stmt.where(PurchaseRequest.needed_by_date <= to_date)
    if department_id:
        stmt = stmt.where(PurchaseRequest.department_id == department_id)
    if criticality_level:
        stmt = stmt.where(PurchaseRequest.criticality_level == criticality_level)
    if stage:
        stmt = stmt.where(RequestCurrentStatus.current_stage == stage)
    if vendor_id:
        stmt = stmt.join(PurchaseOrder, PurchaseOrder.request_id == PurchaseRequest.request_id).where(
            PurchaseOrder.vendor_id == vendor_id
        )
    if item_category:
        stmt = stmt.join(Item, Item.item_id == PurchaseRequest.item_id).where(Item.item_category == item_category)

    rows = db.execute(stmt.order_by(CriticalRequestQueue.priority_rank).limit(limit)).all()
    return [
        CriticalRequestResponse(
            priority_rank=queue.priority_rank,
            request_id=queue.request_id,
            request_number=request.request_number,
            request_title=request.request_title,
            department_id=department.department_id,
            department_name=department.department_name,
            current_stage=current.current_stage,
            current_status=current.current_status,
            days_in_current_stage=float(current.days_in_current_stage),
            needed_by_date=request.needed_by_date,
            criticality_level=request.criticality_level,
            business_impact=request.business_impact,
            criticality_score=float(queue.criticality_score),
            delay_score=float(queue.delay_score),
            business_impact_score=float(queue.business_impact_score),
            needed_by_urgency_score=float(queue.needed_by_urgency_score),
            vendor_risk_score=float(queue.vendor_risk_score),
            total_priority_score=float(queue.total_priority_score),
            recommended_action=queue.recommended_action,
            reason_summary=queue.reason_summary,
        )
        for queue, request, department, current in rows
    ]


@router.get("/requests/{request_id}", response_model=RequestDetailResponse)
def get_request_detail(request_id: str, db: Session = Depends(get_db)) -> RequestDetailResponse:
    request = db.get(PurchaseRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} was not found.")

    department = db.get(Department, request.department_id)
    current = db.get(RequestCurrentStatus, request_id)
    queue = db.get(CriticalRequestQueue, request_id)
    lead_times = _stage_lead_times_for_request(db, request_id)
    timeline = _timeline_for_request(db, request_id)
    related_po = _purchase_order_summary_for_request(db, request_id)
    receipt = _receipt_summary_for_purchase_order(db, related_po.po_id if related_po else None)

    return RequestDetailResponse(
        request=_request_summary(request, department, current, queue),
        stage_lead_times=lead_times,
        timeline=timeline,
        related_po=related_po,
        receipt=receipt,
        quality_flags=_quality_flags_for_request(
            db=db,
            request_id=request_id,
            event_ids=[event.event_id for event in timeline],
        ),
    )


@router.get("/requests/{request_id}/timeline", response_model=list[TimelineEventResponse])
def get_request_timeline(request_id: str, db: Session = Depends(get_db)) -> list[TimelineEventResponse]:
    if db.get(PurchaseRequest, request_id) is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} was not found.")
    return _timeline_for_request(db, request_id)


@router.get("/pipeline-runs", response_model=list[PipelineRunResponse])
def list_pipeline_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[PipelineRunResponse]:
    runs = db.scalars(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
    ).all()
    return [
        PipelineRunResponse(
            pipeline_run_id=run.pipeline_run_id,
            pipeline_name=run.pipeline_name,
            started_at=run.started_at,
            finished_at=run.finished_at,
            status=run.status,
            rows_extracted=run.rows_extracted,
            rows_loaded=run.rows_loaded,
            rows_rejected=run.rows_rejected,
            error_message=run.error_message,
        )
        for run in runs
    ]


@router.get("/data-quality/checks", response_model=list[DataQualityCheckResponse])
def list_data_quality_checks(
    pipeline_run_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    target_table: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[DataQualityCheckResponse]:
    stmt = select(DataQualityCheckResult)
    if pipeline_run_id:
        stmt = stmt.where(DataQualityCheckResult.pipeline_run_id == pipeline_run_id)
    if severity:
        stmt = stmt.where(DataQualityCheckResult.severity == severity)
    if status:
        stmt = stmt.where(DataQualityCheckResult.status == status)
    if target_table:
        stmt = stmt.where(DataQualityCheckResult.target_table == target_table)

    results = db.scalars(
        stmt.order_by(DataQualityCheckResult.created_at.desc(), DataQualityCheckResult.check_result_id).limit(limit)
    ).all()
    return [_data_quality_check_response(result) for result in results]


@router.get("/data-quality/checks/{check_result_id}", response_model=DataQualityCheckResponse)
def get_data_quality_check(
    check_result_id: str,
    db: Session = Depends(get_db),
) -> DataQualityCheckResponse:
    result = db.get(DataQualityCheckResult, check_result_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Data quality check {check_result_id} was not found.",
        )
    return _data_quality_check_response(result)


@router.get("/metadata/filters", response_model=FilterMetadataResponse)
def get_filter_metadata(db: Session = Depends(get_db)) -> FilterMetadataResponse:
    departments = db.scalars(select(Department).order_by(Department.department_name)).all()
    vendors = db.scalars(select(Vendor).order_by(Vendor.vendor_name)).all()
    item_categories = db.scalars(select(Item.item_category).distinct().order_by(Item.item_category)).all()

    return FilterMetadataResponse(
        departments=[
            FilterOption(id=department.department_id, name=department.department_name)
            for department in departments
        ],
        vendors=[
            FilterOption(id=vendor.vendor_id, name=vendor.vendor_name)
            for vendor in vendors
        ],
        item_categories=list(item_categories),
        criticality_levels=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        stages=STAGE_FLOW,
    )


@router.get("/v2/maintenance/overview", response_model=MaintenanceOverviewResponse)
def get_maintenance_overview(db: Session = Depends(get_db)) -> MaintenanceOverviewResponse:
    requests = list(db.scalars(select(MaintenanceRequest)))
    current_statuses = list(db.scalars(select(MaintenanceCurrentStatus)))
    stage_summaries = list(
        db.scalars(
            select(MaintenanceBottleneckSummary).where(MaintenanceBottleneckSummary.dimension_type == "STAGE")
        )
    )
    equipment_summaries = list(db.scalars(select(EquipmentDelaySummary)))
    parts_summaries = list(db.scalars(select(PartsWaitingSummary)))
    latest_run = _latest_pipeline_run(db, "maintenance_ingestion")

    top_stage = max(
        stage_summaries,
        key=lambda summary: float(summary.total_delay_hours),
        default=None,
    )
    technician_assignment = next(
        (
            summary
            for summary in stage_summaries
            if summary.stage == "TECHNICIAN_ASSIGNED"
        ),
        None,
    )

    return MaintenanceOverviewResponse(
        total_requests=len(requests),
        open_requests=sum(1 for request in requests if request.current_status != "COMPLETED"),
        delayed_requests=sum(1 for status in current_statuses if status.is_delayed),
        critical_equipment_delayed=_critical_equipment_delayed_count(db),
        avg_downtime_hours=round(
            mean(float(request.actual_downtime_hours or request.estimated_downtime_hours) for request in requests),
            2,
        )
        if requests
        else 0,
        top_bottleneck_stage=top_stage.stage if top_stage else None,
        parts_waiting_delay_hours=round(sum(float(summary.total_wait_hours) for summary in parts_summaries), 2),
        repeat_failure_equipment_count=sum(
            1 for summary in equipment_summaries if summary.repeat_failure_count > 0
        ),
        technician_assignment_delay_hours=float(technician_assignment.total_delay_hours)
        if technician_assignment
        else 0,
        latest_pipeline_run_status=latest_run.status if latest_run else None,
        data_quality_status=_data_quality_status(db, latest_run.pipeline_run_id if latest_run else None),
    )


@router.get("/v2/maintenance/bottlenecks/stages", response_model=list[StageBottleneckResponse])
def list_maintenance_stage_bottlenecks(
    stage: Optional[str] = None,
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    equipment_type: Optional[str] = None,
    technician_team: Optional[str] = None,
    part_category: Optional[str] = None,
    priority_level: Optional[str] = None,
    request_type: Optional[str] = None,
    failure_mode: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
) -> list[StageBottleneckResponse]:
    if any([line_id, equipment_id, equipment_type, technician_team, part_category, priority_level, request_type, failure_mode, from_date, to_date]):
        return _filtered_maintenance_stage_bottlenecks(
            db=db,
            stage=stage,
            line_id=line_id,
            equipment_id=equipment_id,
            equipment_type=equipment_type,
            technician_team=technician_team,
            part_category=part_category,
            priority_level=priority_level,
            request_type=request_type,
            failure_mode=failure_mode,
            from_date=from_date,
            to_date=to_date,
        )

    stmt = select(MaintenanceBottleneckSummary).where(MaintenanceBottleneckSummary.dimension_type == "STAGE")
    if stage:
        stmt = stmt.where(MaintenanceBottleneckSummary.stage == stage)
    summaries = db.scalars(
        stmt.order_by(MaintenanceBottleneckSummary.total_delay_hours.desc(), MaintenanceBottleneckSummary.stage)
    ).all()
    return [
        StageBottleneckResponse(
            stage=summary.stage,
            request_count=summary.request_count,
            delayed_count=summary.delayed_count,
            delay_rate=float(summary.delay_rate),
            avg_duration_hours=float(summary.avg_duration_hours),
            p90_duration_hours=float(summary.p90_duration_hours),
            total_delay_hours=float(summary.total_delay_hours),
        )
        for summary in summaries
    ]


@router.get("/v2/maintenance/requests/critical", response_model=list[MaintenanceCriticalRequestResponse])
def list_critical_maintenance_requests(
    limit: int = Query(default=25, ge=1, le=100),
    stage: Optional[str] = None,
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    equipment_type: Optional[str] = None,
    technician_team: Optional[str] = None,
    part_category: Optional[str] = None,
    priority_level: Optional[str] = None,
    request_type: Optional[str] = None,
    failure_mode: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[MaintenanceCriticalRequestResponse]:
    stmt = (
        select(CriticalMaintenanceQueue, MaintenanceRequest, Equipment, ProductionLine, MaintenanceCurrentStatus)
        .join(MaintenanceRequest, MaintenanceRequest.maintenance_request_id == CriticalMaintenanceQueue.maintenance_request_id)
        .join(Equipment, Equipment.equipment_id == MaintenanceRequest.equipment_id)
        .join(ProductionLine, ProductionLine.line_id == MaintenanceRequest.line_id)
        .join(MaintenanceCurrentStatus, MaintenanceCurrentStatus.maintenance_request_id == MaintenanceRequest.maintenance_request_id)
    )
    if technician_team or part_category:
        stmt = stmt.join(
            MaintenanceWorkOrder,
            MaintenanceWorkOrder.maintenance_request_id == MaintenanceRequest.maintenance_request_id,
        )
    if part_category:
        stmt = stmt.join(Part, Part.part_id == MaintenanceWorkOrder.required_part_id)
    if stage:
        stmt = stmt.where(CriticalMaintenanceQueue.current_stage == stage)
    if line_id:
        stmt = stmt.where(MaintenanceRequest.line_id == line_id)
    if equipment_id:
        stmt = stmt.where(MaintenanceRequest.equipment_id == equipment_id)
    if equipment_type:
        stmt = stmt.where(Equipment.equipment_type == equipment_type)
    if technician_team:
        stmt = stmt.where(MaintenanceWorkOrder.assigned_team == technician_team)
    if part_category:
        stmt = stmt.where(Part.part_category == part_category)
    if priority_level:
        stmt = stmt.where(MaintenanceRequest.priority_level == priority_level)
    if request_type:
        stmt = stmt.where(MaintenanceRequest.request_type == request_type)
    if failure_mode:
        stmt = stmt.where(MaintenanceRequest.failure_mode == failure_mode)

    rows = db.execute(stmt.order_by(CriticalMaintenanceQueue.priority_rank).limit(limit)).all()
    return [
        _maintenance_critical_response(queue, request, equipment, line, current)
        for queue, request, equipment, line, current in rows
    ]


@router.get("/v2/maintenance/requests/{maintenance_request_id}", response_model=MaintenanceRequestDetailResponse)
def get_maintenance_request_detail(
    maintenance_request_id: str,
    db: Session = Depends(get_db),
) -> MaintenanceRequestDetailResponse:
    request = db.get(MaintenanceRequest, maintenance_request_id)
    if request is None:
        raise HTTPException(status_code=404, detail=f"Maintenance request {maintenance_request_id} was not found.")

    equipment = db.get(Equipment, request.equipment_id)
    line = db.get(ProductionLine, request.line_id)
    current = db.get(MaintenanceCurrentStatus, maintenance_request_id)
    queue = db.get(CriticalMaintenanceQueue, maintenance_request_id)
    timeline = _maintenance_timeline_for_request(db, maintenance_request_id)

    return MaintenanceRequestDetailResponse(
        request=_maintenance_request_summary(request, equipment, line, current, queue),
        stage_lead_times=_maintenance_stage_lead_times_for_request(db, maintenance_request_id),
        timeline=timeline,
        work_orders=_maintenance_work_orders_for_request(db, maintenance_request_id),
        inspection_results=_maintenance_inspections_for_request(db, maintenance_request_id),
        sensor_alerts=_maintenance_sensor_alerts_for_request(db, maintenance_request_id),
        quality_flags=_maintenance_quality_flags_for_request(
            db=db,
            maintenance_request_id=maintenance_request_id,
            event_ids=[event.event_id for event in timeline],
        ),
    )


@router.get("/v2/maintenance/requests/{maintenance_request_id}/timeline", response_model=list[TimelineEventResponse])
def get_maintenance_request_timeline(
    maintenance_request_id: str,
    db: Session = Depends(get_db),
) -> list[TimelineEventResponse]:
    if db.get(MaintenanceRequest, maintenance_request_id) is None:
        raise HTTPException(status_code=404, detail=f"Maintenance request {maintenance_request_id} was not found.")
    return _maintenance_timeline_for_request(db, maintenance_request_id)


@router.get("/v2/maintenance/equipment/delays", response_model=list[EquipmentDelayResponse])
def list_equipment_delay_summaries(
    line_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[EquipmentDelayResponse]:
    stmt = select(EquipmentDelaySummary)
    if line_id:
        stmt = stmt.where(EquipmentDelaySummary.line_id == line_id)
    if equipment_id:
        stmt = stmt.where(EquipmentDelaySummary.equipment_id == equipment_id)
    rows = db.scalars(
        stmt.order_by(EquipmentDelaySummary.delayed_request_count.desc(), EquipmentDelaySummary.total_downtime_hours.desc())
    ).all()
    return [_equipment_delay_response(row) for row in rows]


@router.get("/v2/maintenance/lines/delays", response_model=list[ProductionLineDelayResponse])
def list_production_line_delay_summaries(
    line_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[ProductionLineDelayResponse]:
    stmt = select(ProductionLineDelaySummary)
    if line_id:
        stmt = stmt.where(ProductionLineDelaySummary.line_id == line_id)
    rows = db.scalars(
        stmt.order_by(ProductionLineDelaySummary.delayed_request_count.desc(), ProductionLineDelaySummary.total_downtime_hours.desc())
    ).all()
    return [_production_line_delay_response(row) for row in rows]


@router.get("/v2/maintenance/parts/waiting", response_model=list[PartsWaitingResponse])
def list_parts_waiting_summaries(
    part_category: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[PartsWaitingResponse]:
    stmt = select(PartsWaitingSummary)
    if part_category:
        stmt = stmt.where(PartsWaitingSummary.part_category == part_category)
    rows = db.scalars(
        stmt.order_by(PartsWaitingSummary.total_wait_hours.desc(), PartsWaitingSummary.part_name)
    ).all()
    return [_parts_waiting_response(row) for row in rows]


@router.get("/v2/maintenance/metadata/filters", response_model=MaintenanceFilterMetadataResponse)
def get_maintenance_filter_metadata(db: Session = Depends(get_db)) -> MaintenanceFilterMetadataResponse:
    lines = db.scalars(select(ProductionLine).order_by(ProductionLine.line_name)).all()
    equipment = db.scalars(select(Equipment).order_by(Equipment.equipment_name)).all()
    equipment_types = db.scalars(select(Equipment.equipment_type).distinct().order_by(Equipment.equipment_type)).all()
    technician_teams = db.scalars(
        select(MaintenanceWorkOrder.assigned_team).distinct().order_by(MaintenanceWorkOrder.assigned_team)
    ).all()
    part_categories = db.scalars(select(Part.part_category).distinct().order_by(Part.part_category)).all()
    priority_levels = db.scalars(select(MaintenanceRequest.priority_level).distinct()).all()
    request_types = db.scalars(select(MaintenanceRequest.request_type).distinct().order_by(MaintenanceRequest.request_type)).all()
    failure_modes = db.scalars(select(MaintenanceRequest.failure_mode).distinct().order_by(MaintenanceRequest.failure_mode)).all()

    return MaintenanceFilterMetadataResponse(
        production_lines=[FilterOption(id=line.line_id, name=line.line_name) for line in lines],
        equipment=[FilterOption(id=item.equipment_id, name=item.equipment_name) for item in equipment],
        equipment_types=list(equipment_types),
        technician_teams=list(technician_teams),
        part_categories=list(part_categories),
        priority_levels=sorted(priority_levels, key=lambda level: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(level)),
        request_types=list(request_types),
        failure_modes=list(failure_modes),
        stages=MAINTENANCE_STAGE_FLOW,
    )


def _filtered_maintenance_stage_bottlenecks(
    db: Session,
    stage: Optional[str],
    line_id: Optional[str],
    equipment_id: Optional[str],
    equipment_type: Optional[str],
    technician_team: Optional[str],
    part_category: Optional[str],
    priority_level: Optional[str],
    request_type: Optional[str],
    failure_mode: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> list[StageBottleneckResponse]:
    stmt = (
        select(MaintenanceStageLeadTime)
        .join(MaintenanceRequest, MaintenanceRequest.maintenance_request_id == MaintenanceStageLeadTime.maintenance_request_id)
        .join(Equipment, Equipment.equipment_id == MaintenanceRequest.equipment_id)
    )
    if technician_team or part_category:
        stmt = stmt.join(
            MaintenanceWorkOrder,
            MaintenanceWorkOrder.maintenance_request_id == MaintenanceRequest.maintenance_request_id,
        )
    if part_category:
        stmt = stmt.join(Part, Part.part_id == MaintenanceWorkOrder.required_part_id)
    if stage:
        stmt = stmt.where(MaintenanceStageLeadTime.stage == stage)
    if line_id:
        stmt = stmt.where(MaintenanceRequest.line_id == line_id)
    if equipment_id:
        stmt = stmt.where(MaintenanceRequest.equipment_id == equipment_id)
    if equipment_type:
        stmt = stmt.where(Equipment.equipment_type == equipment_type)
    if technician_team:
        stmt = stmt.where(MaintenanceWorkOrder.assigned_team == technician_team)
    if part_category:
        stmt = stmt.where(Part.part_category == part_category)
    if priority_level:
        stmt = stmt.where(MaintenanceRequest.priority_level == priority_level)
    if request_type:
        stmt = stmt.where(MaintenanceRequest.request_type == request_type)
    if failure_mode:
        stmt = stmt.where(MaintenanceRequest.failure_mode == failure_mode)
    if from_date:
        stmt = stmt.where(MaintenanceStageLeadTime.entered_at >= datetime.combine(from_date, time.min))
    if to_date:
        stmt = stmt.where(MaintenanceStageLeadTime.entered_at <= datetime.combine(to_date, time.max))

    lead_times_by_id = {
        lead_time.lead_time_id: lead_time
        for lead_time in db.scalars(stmt).all()
    }
    grouped: dict[str, list[MaintenanceStageLeadTime]] = defaultdict(list)
    for lead_time in lead_times_by_id.values():
        grouped[lead_time.stage].append(lead_time)

    responses = []
    for stage_name, records in grouped.items():
        durations = [float(record.duration_hours) for record in records]
        delay_hours = [float(record.delay_hours) for record in records]
        request_count = len(records)
        delayed_count = sum(1 for record in records if record.is_bottleneck)
        responses.append(
            StageBottleneckResponse(
                stage=stage_name,
                request_count=request_count,
                delayed_count=delayed_count,
                delay_rate=round(delayed_count / request_count, 4) if request_count else 0,
                avg_duration_hours=round(mean(durations), 2) if durations else 0,
                p90_duration_hours=round(_percentile(durations, 0.9), 2),
                total_delay_hours=round(sum(delay_hours), 2),
            )
        )

    return sorted(responses, key=lambda response: (-response.total_delay_hours, response.stage))


def _maintenance_critical_response(
    queue: CriticalMaintenanceQueue,
    request: MaintenanceRequest,
    equipment: Equipment,
    line: ProductionLine,
    current: MaintenanceCurrentStatus,
) -> MaintenanceCriticalRequestResponse:
    return MaintenanceCriticalRequestResponse(
        priority_rank=queue.priority_rank,
        maintenance_request_id=queue.maintenance_request_id,
        request_number=request.request_number,
        request_title=request.request_title,
        equipment_id=equipment.equipment_id,
        equipment_name=equipment.equipment_name,
        line_id=line.line_id,
        line_name=line.line_name,
        current_stage=current.current_stage,
        current_status=current.current_status,
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


def _maintenance_request_summary(
    request: MaintenanceRequest,
    equipment: Optional[Equipment],
    line: Optional[ProductionLine],
    current: Optional[MaintenanceCurrentStatus],
    queue: Optional[CriticalMaintenanceQueue],
) -> MaintenanceCriticalRequestResponse:
    return MaintenanceCriticalRequestResponse(
        priority_rank=queue.priority_rank if queue else 0,
        maintenance_request_id=request.maintenance_request_id,
        request_number=request.request_number,
        request_title=request.request_title,
        equipment_id=request.equipment_id,
        equipment_name=equipment.equipment_name if equipment else request.equipment_id,
        line_id=request.line_id,
        line_name=line.line_name if line else request.line_id,
        current_stage=current.current_stage if current else request.current_stage,
        current_status=current.current_status if current else request.current_status,
        hours_in_current_stage=float(current.hours_in_current_stage) if current else 0,
        needed_by_at=request.needed_by_at,
        priority_level=request.priority_level,
        business_impact=request.business_impact,
        equipment_criticality_score=float(queue.equipment_criticality_score) if queue else 0,
        downtime_score=float(queue.downtime_score) if queue else 0,
        stage_delay_score=float(queue.stage_delay_score) if queue else 0,
        production_line_impact_score=float(queue.production_line_impact_score) if queue else 0,
        needed_by_urgency_score=float(queue.needed_by_urgency_score) if queue else 0,
        repeat_failure_score=float(queue.repeat_failure_score) if queue else 0,
        parts_risk_score=float(queue.parts_risk_score) if queue else 0,
        total_priority_score=float(queue.total_priority_score) if queue else 0,
        recommended_action=queue.recommended_action if queue else _maintenance_fallback_recommended_action(request),
        reason_summary=queue.reason_summary if queue else _maintenance_fallback_reason_summary(request),
    )


def _maintenance_stage_lead_times_for_request(
    db: Session,
    maintenance_request_id: str,
) -> list[StageLeadTimeResponse]:
    lead_times = db.scalars(
        select(MaintenanceStageLeadTime)
        .where(MaintenanceStageLeadTime.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceStageLeadTime.entered_at, MaintenanceStageLeadTime.lead_time_id)
    ).all()
    return [
        StageLeadTimeResponse(
            stage=lead_time.stage,
            entered_at=lead_time.entered_at,
            exited_at=lead_time.exited_at,
            duration_hours=float(lead_time.duration_hours),
            threshold_hours=float(lead_time.threshold_hours),
            is_bottleneck=lead_time.is_bottleneck,
            delay_hours=float(lead_time.delay_hours),
        )
        for lead_time in lead_times
    ]


def _maintenance_timeline_for_request(
    db: Session,
    maintenance_request_id: str,
) -> list[TimelineEventResponse]:
    events = db.scalars(
        select(MaintenanceStageEvent)
        .where(MaintenanceStageEvent.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceStageEvent.occurred_at, MaintenanceStageEvent.event_id)
    ).all()
    return [
        TimelineEventResponse(
            event_id=event.event_id,
            stage=event.stage,
            event_type=event.event_type,
            event_status=event.event_status,
            occurred_at=event.occurred_at,
            actor_type=event.actor_type,
            reason_code=event.reason_code,
            message=_maintenance_event_message(event),
        )
        for event in events
    ]


def _maintenance_work_orders_for_request(
    db: Session,
    maintenance_request_id: str,
) -> list[MaintenanceWorkOrderSummaryResponse]:
    rows = db.execute(
        select(MaintenanceWorkOrder, Part)
        .outerjoin(Part, Part.part_id == MaintenanceWorkOrder.required_part_id)
        .where(MaintenanceWorkOrder.maintenance_request_id == maintenance_request_id)
        .order_by(MaintenanceWorkOrder.work_order_id)
    ).all()
    return [
        MaintenanceWorkOrderSummaryResponse(
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
        for work_order, part in rows
    ]


def _maintenance_inspections_for_request(
    db: Session,
    maintenance_request_id: str,
) -> list[MaintenanceInspectionResponse]:
    inspections = db.scalars(
        select(InspectionResult)
        .where(InspectionResult.maintenance_request_id == maintenance_request_id)
        .order_by(InspectionResult.inspection_started_at, InspectionResult.inspection_id)
    ).all()
    return [
        MaintenanceInspectionResponse(
            inspection_id=inspection.inspection_id,
            inspection_status=inspection.inspection_status,
            inspector_id=inspection.inspector_id,
            inspection_started_at=inspection.inspection_started_at,
            inspection_completed_at=inspection.inspection_completed_at,
            failure_reason=inspection.failure_reason,
        )
        for inspection in inspections
    ]


def _maintenance_sensor_alerts_for_request(
    db: Session,
    maintenance_request_id: str,
) -> list[MaintenanceSensorAlertResponse]:
    alerts = db.scalars(
        select(SensorAlert)
        .where(SensorAlert.linked_maintenance_request_id == maintenance_request_id)
        .order_by(SensorAlert.triggered_at, SensorAlert.sensor_alert_id)
    ).all()
    return [
        MaintenanceSensorAlertResponse(
            sensor_alert_id=alert.sensor_alert_id,
            equipment_id=alert.equipment_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            triggered_at=alert.triggered_at,
            resolved_at=alert.resolved_at,
        )
        for alert in alerts
    ]


def _equipment_delay_response(summary: EquipmentDelaySummary) -> EquipmentDelayResponse:
    return EquipmentDelayResponse(
        equipment_id=summary.equipment_id,
        equipment_name=summary.equipment_name,
        line_id=summary.line_id,
        line_name=summary.line_name,
        request_count=summary.request_count,
        delayed_request_count=summary.delayed_request_count,
        repeat_failure_count=summary.repeat_failure_count,
        total_downtime_hours=float(summary.total_downtime_hours),
        avg_repair_duration_hours=float(summary.avg_repair_duration_hours),
        top_failure_mode=summary.top_failure_mode,
    )


def _production_line_delay_response(summary: ProductionLineDelaySummary) -> ProductionLineDelayResponse:
    return ProductionLineDelayResponse(
        line_id=summary.line_id,
        line_name=summary.line_name,
        open_request_count=summary.open_request_count,
        delayed_request_count=summary.delayed_request_count,
        critical_equipment_delayed_count=summary.critical_equipment_delayed_count,
        total_downtime_hours=float(summary.total_downtime_hours),
        top_bottleneck_stage=summary.top_bottleneck_stage,
    )


def _parts_waiting_response(summary: PartsWaitingSummary) -> PartsWaitingResponse:
    return PartsWaitingResponse(
        part_id=summary.part_id,
        part_name=summary.part_name,
        part_category=summary.part_category,
        waiting_request_count=summary.waiting_request_count,
        total_wait_hours=float(summary.total_wait_hours),
        avg_wait_hours=float(summary.avg_wait_hours),
        critical_spare=summary.critical_spare,
        stock_status=summary.stock_status,
    )


def _filtered_stage_bottlenecks(
    db: Session,
    from_date: Optional[date],
    to_date: Optional[date],
    stage: Optional[str],
    department_id: Optional[str],
    vendor_id: Optional[str],
    item_category: Optional[str],
    criticality_level: Optional[str],
) -> list[StageBottleneckResponse]:
    stmt = select(RequestStageLeadTime).join(
        PurchaseRequest,
        PurchaseRequest.request_id == RequestStageLeadTime.request_id,
    )
    if vendor_id:
        stmt = stmt.join(PurchaseOrder, PurchaseOrder.request_id == PurchaseRequest.request_id)
    if item_category:
        stmt = stmt.join(Item, Item.item_id == PurchaseRequest.item_id)
    if from_date:
        stmt = stmt.where(RequestStageLeadTime.entered_at >= datetime.combine(from_date, time.min))
    if to_date:
        stmt = stmt.where(RequestStageLeadTime.entered_at <= datetime.combine(to_date, time.max))
    if stage:
        stmt = stmt.where(RequestStageLeadTime.stage == stage)
    if department_id:
        stmt = stmt.where(PurchaseRequest.department_id == department_id)
    if vendor_id:
        stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
    if item_category:
        stmt = stmt.where(Item.item_category == item_category)
    if criticality_level:
        stmt = stmt.where(PurchaseRequest.criticality_level == criticality_level)

    lead_times_by_id = {
        lead_time.lead_time_id: lead_time
        for lead_time in db.scalars(stmt).all()
    }
    grouped: dict[str, list[RequestStageLeadTime]] = defaultdict(list)
    for lead_time in lead_times_by_id.values():
        grouped[lead_time.stage].append(lead_time)

    responses = []
    for stage_name, records in grouped.items():
        durations = [float(record.duration_hours) for record in records]
        delay_hours = [float(record.delay_hours) for record in records]
        request_count = len(records)
        delayed_count = sum(1 for record in records if record.is_bottleneck)
        responses.append(
            StageBottleneckResponse(
                stage=stage_name,
                request_count=request_count,
                delayed_count=delayed_count,
                delay_rate=round(delayed_count / request_count, 4) if request_count else 0,
                avg_duration_hours=round(mean(durations), 2) if durations else 0,
                p90_duration_hours=round(_percentile(durations, 0.9), 2),
                total_delay_hours=round(sum(delay_hours), 2),
            )
        )

    return sorted(
        responses,
        key=lambda response: (-response.total_delay_hours, response.stage),
    )


def _filtered_vendor_bottlenecks(
    db: Session,
    vendor_id: Optional[str],
    stage: Optional[str],
    department_id: Optional[str],
    item_category: Optional[str],
    criticality_level: Optional[str],
) -> list[VendorBottleneckResponse]:
    stmt = (
        select(PurchaseOrder, Vendor, PurchaseRequest)
        .join(Vendor, Vendor.vendor_id == PurchaseOrder.vendor_id)
        .join(PurchaseRequest, PurchaseRequest.request_id == PurchaseOrder.request_id)
    )
    if stage:
        stmt = stmt.join(RequestCurrentStatus, RequestCurrentStatus.request_id == PurchaseRequest.request_id)
    if item_category:
        stmt = stmt.join(Item, Item.item_id == PurchaseRequest.item_id)
    if vendor_id:
        stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
    if stage:
        stmt = stmt.where(RequestCurrentStatus.current_stage == stage)
    if department_id:
        stmt = stmt.where(PurchaseRequest.department_id == department_id)
    if item_category:
        stmt = stmt.where(Item.item_category == item_category)
    if criticality_level:
        stmt = stmt.where(PurchaseRequest.criticality_level == criticality_level)

    order_rows_by_id = {
        purchase_order.po_id: (purchase_order, vendor, request)
        for purchase_order, vendor, request in db.execute(stmt).all()
    }
    if not order_rows_by_id:
        return []

    request_ids = [purchase_order.request_id for purchase_order, _, _ in order_rows_by_id.values()]
    lead_times = db.scalars(
        select(RequestStageLeadTime).where(RequestStageLeadTime.request_id.in_(request_ids))
    ).all()

    confirmation_delay_by_request: dict[str, float] = defaultdict(float)
    delivery_delay_by_request: dict[str, float] = defaultdict(float)
    confirmation_duration_by_request: dict[str, float] = {}
    total_delay_by_request: dict[str, float] = defaultdict(float)
    for lead_time in lead_times:
        delay_hours = float(lead_time.delay_hours)
        total_delay_by_request[lead_time.request_id] += delay_hours
        if lead_time.stage == "VENDOR_CONFIRMATION":
            confirmation_delay_by_request[lead_time.request_id] += delay_hours
            confirmation_duration_by_request[lead_time.request_id] = float(lead_time.duration_hours)
        if lead_time.stage == "DELIVERY":
            delivery_delay_by_request[lead_time.request_id] += delay_hours

    grouped: dict[str, list[tuple[PurchaseOrder, Vendor, PurchaseRequest]]] = defaultdict(list)
    for row in order_rows_by_id.values():
        grouped[row[0].vendor_id].append(row)

    responses = []
    for grouped_vendor_id, rows in grouped.items():
        vendor = rows[0][1]
        orders = [row[0] for row in rows]
        delayed_count = sum(
            1
            for order in orders
            if confirmation_delay_by_request.get(order.request_id, 0) > 0
            or delivery_delay_by_request.get(order.request_id, 0) > 0
        )
        confirmation_hours = [
            confirmation_duration_by_request[order.request_id]
            for order in orders
            if order.request_id in confirmation_duration_by_request
        ]
        delivery_delay_days = [
            delay_hours / 24
            for order in orders
            if (delay_hours := delivery_delay_by_request.get(order.request_id, 0)) > 0
        ]
        total_count = len(orders)
        responses.append(
            VendorBottleneckResponse(
                vendor_id=grouped_vendor_id,
                vendor_name=vendor.vendor_name,
                total_po_count=total_count,
                delayed_po_count=delayed_count,
                delay_rate=round(delayed_count / total_count if total_count else 0, 4),
                avg_confirmation_hours=round(mean(confirmation_hours) if confirmation_hours else 0, 2),
                avg_delivery_delay_days=round(mean(delivery_delay_days) if delivery_delay_days else 0, 2),
                reliability_tier=vendor.reliability_tier,
                total_delay_hours=round(
                    sum(total_delay_by_request.get(order.request_id, 0) for order in orders),
                    2,
                ),
            )
        )

    return sorted(
        responses,
        key=lambda response: (-response.delay_rate, -response.delayed_po_count, response.vendor_name),
    )


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * percentile))
    return sorted_values[index]


def _request_summary(
    request: PurchaseRequest,
    department: Optional[Department],
    current: Optional[RequestCurrentStatus],
    queue: Optional[CriticalRequestQueue],
) -> CriticalRequestResponse:
    return CriticalRequestResponse(
        priority_rank=queue.priority_rank if queue else 0,
        request_id=request.request_id,
        request_number=request.request_number,
        request_title=request.request_title,
        department_id=request.department_id,
        department_name=department.department_name if department else request.department_id,
        current_stage=current.current_stage if current else request.current_stage,
        current_status=current.current_status if current else request.current_status,
        days_in_current_stage=float(current.days_in_current_stage) if current else 0,
        needed_by_date=request.needed_by_date,
        criticality_level=request.criticality_level,
        business_impact=request.business_impact,
        criticality_score=float(queue.criticality_score) if queue else 0,
        delay_score=float(queue.delay_score) if queue else 0,
        business_impact_score=float(queue.business_impact_score) if queue else 0,
        needed_by_urgency_score=float(queue.needed_by_urgency_score) if queue else 0,
        vendor_risk_score=float(queue.vendor_risk_score) if queue else 0,
        total_priority_score=float(queue.total_priority_score) if queue else 0,
        recommended_action=queue.recommended_action if queue else _fallback_recommended_action(request),
        reason_summary=queue.reason_summary if queue else _fallback_reason_summary(request),
    )


def _stage_lead_times_for_request(db: Session, request_id: str) -> list[StageLeadTimeResponse]:
    lead_times = db.scalars(
        select(RequestStageLeadTime)
        .where(RequestStageLeadTime.request_id == request_id)
        .order_by(RequestStageLeadTime.entered_at, RequestStageLeadTime.lead_time_id)
    ).all()
    return [
        StageLeadTimeResponse(
            stage=lead_time.stage,
            entered_at=lead_time.entered_at,
            exited_at=lead_time.exited_at,
            duration_hours=float(lead_time.duration_hours),
            threshold_hours=float(lead_time.threshold_hours),
            is_bottleneck=lead_time.is_bottleneck,
            delay_hours=float(lead_time.delay_hours),
        )
        for lead_time in lead_times
    ]


def _timeline_for_request(db: Session, request_id: str) -> list[TimelineEventResponse]:
    events = db.scalars(
        select(ProcurementStageEvent)
        .where(ProcurementStageEvent.request_id == request_id)
        .order_by(ProcurementStageEvent.occurred_at, ProcurementStageEvent.event_id)
    ).all()
    return [
        TimelineEventResponse(
            event_id=event.event_id,
            stage=event.stage,
            event_type=event.event_type,
            event_status=event.event_status,
            occurred_at=event.occurred_at,
            actor_type=event.actor_type,
            reason_code=event.reason_code,
            message=_event_message(event),
        )
        for event in events
    ]


def _purchase_order_summary_for_request(
    db: Session,
    request_id: str,
) -> Optional[PurchaseOrderSummaryResponse]:
    row = db.execute(
        select(PurchaseOrder, Vendor)
        .join(Vendor, Vendor.vendor_id == PurchaseOrder.vendor_id)
        .where(PurchaseOrder.request_id == request_id)
        .order_by(PurchaseOrder.po_created_at, PurchaseOrder.po_id)
        .limit(1)
    ).first()
    if row is None:
        return None

    purchase_order, vendor = row
    return PurchaseOrderSummaryResponse(
        po_id=purchase_order.po_id,
        po_number=purchase_order.po_number,
        vendor_id=purchase_order.vendor_id,
        vendor_name=vendor.vendor_name,
        po_status=purchase_order.po_status,
        expected_delivery_date=purchase_order.expected_delivery_date,
        actual_delivery_date=purchase_order.actual_delivery_date,
    )


def _receipt_summary_for_purchase_order(
    db: Session,
    po_id: Optional[str],
) -> Optional[ReceiptSummaryResponse]:
    if po_id is None:
        return None

    receipt = db.scalar(
        select(Receipt)
        .where(Receipt.po_id == po_id)
        .order_by(Receipt.received_at, Receipt.receipt_id)
        .limit(1)
    )
    if receipt is None:
        return None
    return ReceiptSummaryResponse(
        receipt_id=receipt.receipt_id,
        received_at=receipt.received_at,
        inspection_status=receipt.inspection_status,
        inspection_completed_at=receipt.inspection_completed_at,
    )


def _quality_flags_for_request(
    db: Session,
    request_id: str,
    event_ids: list[str],
) -> list[str]:
    latest_run = _latest_pipeline_run(db)
    if latest_run is None:
        return []

    search_keys = [request_id] + event_ids
    failed_results = db.scalars(
        select(DataQualityCheckResult)
        .where(
            DataQualityCheckResult.pipeline_run_id == latest_run.pipeline_run_id,
            DataQualityCheckResult.status != "PASS",
        )
        .order_by(DataQualityCheckResult.target_table, DataQualityCheckResult.check_name)
    ).all()

    flags = []
    for result in failed_results:
        sample_failed_keys = string_list(result.sample_failed_keys)
        if any(key in sample_key for key in search_keys for sample_key in sample_failed_keys):
            flags.append(f"{result.target_table}.{result.check_name}: {result.message}")
    return flags


def _maintenance_quality_flags_for_request(
    db: Session,
    maintenance_request_id: str,
    event_ids: list[str],
) -> list[str]:
    latest_run = _latest_pipeline_run(db, "maintenance_ingestion")
    if latest_run is None:
        return []

    search_keys = [maintenance_request_id] + event_ids
    failed_results = db.scalars(
        select(DataQualityCheckResult)
        .where(
            DataQualityCheckResult.pipeline_run_id == latest_run.pipeline_run_id,
            DataQualityCheckResult.status != "PASS",
        )
        .order_by(DataQualityCheckResult.target_table, DataQualityCheckResult.check_name)
    ).all()

    flags = []
    for result in failed_results:
        sample_failed_keys = string_list(result.sample_failed_keys)
        if any(key in sample_key for key in search_keys for sample_key in sample_failed_keys):
            flags.append(f"{result.target_table}.{result.check_name}: {result.message}")
    return flags


def _data_quality_check_response(result: DataQualityCheckResult) -> DataQualityCheckResponse:
    return DataQualityCheckResponse(
        check_result_id=result.check_result_id,
        pipeline_run_id=result.pipeline_run_id,
        check_name=result.check_name,
        target_table=result.target_table,
        severity=result.severity,
        status=result.status,
        failed_row_count=result.failed_row_count,
        sample_failed_keys=string_list(result.sample_failed_keys),
        message=result.message,
        created_at=result.created_at,
    )


def _event_message(event: ProcurementStageEvent) -> Optional[str]:
    if not isinstance(event.metadata_json, dict):
        return None
    message = event.metadata_json.get("message")
    return str(message) if message else None


def _maintenance_event_message(event: MaintenanceStageEvent) -> Optional[str]:
    if not isinstance(event.metadata_json, dict):
        return None
    message = event.metadata_json.get("message")
    return str(message) if message else None


def _fallback_recommended_action(request: PurchaseRequest) -> str:
    if request.current_status == "CLOSED":
        return "No action required"
    return "Review request status"


def _fallback_reason_summary(request: PurchaseRequest) -> str:
    if request.current_status == "CLOSED":
        return f"{request.criticality_level} request is closed."
    return f"{request.criticality_level} request is currently in {request.current_stage}."


def _maintenance_fallback_recommended_action(request: MaintenanceRequest) -> str:
    if request.current_status == "COMPLETED":
        return "No action required"
    return "Review maintenance request status"


def _maintenance_fallback_reason_summary(request: MaintenanceRequest) -> str:
    if request.current_status == "COMPLETED":
        return f"{request.priority_level} maintenance request is completed."
    return f"{request.priority_level} maintenance request is currently in {request.current_stage}."


def _latest_pipeline_run(db: Session, pipeline_name: Optional[str] = None) -> Optional[PipelineRun]:
    stmt = select(PipelineRun)
    if pipeline_name:
        stmt = stmt.where(PipelineRun.pipeline_name == pipeline_name)
    return db.scalar(stmt.order_by(PipelineRun.started_at.desc()).limit(1))


def _data_quality_status(db: Session, pipeline_run_id: Optional[str]) -> str:
    if pipeline_run_id is None:
        return "PASS"

    statuses = list(
        db.scalars(
            select(DataQualityCheckResult.status).where(
                DataQualityCheckResult.pipeline_run_id == pipeline_run_id
            )
        )
    )
    if "CRITICAL" in statuses:
        return "CRITICAL"
    if "FAILED" in statuses:
        return "FAILED"
    if "WARNING" in statuses:
        return "WARNING"
    return "PASS"


def _vendor_total_delay_hours(db: Session) -> dict[str, float]:
    rows = db.scalars(
        select(BottleneckSummary).where(BottleneckSummary.dimension_type == "VENDOR")
    ).all()
    delay_by_vendor: dict[str, float] = defaultdict(float)
    for row in rows:
        delay_by_vendor[row.dimension_id] += float(row.total_delay_hours)
    return dict(delay_by_vendor)


def _critical_equipment_delayed_count(db: Session) -> int:
    rows = db.execute(
        select(MaintenanceCurrentStatus, Equipment)
        .join(Equipment, Equipment.equipment_id == MaintenanceCurrentStatus.equipment_id)
        .where(
            MaintenanceCurrentStatus.is_delayed.is_(True),
            Equipment.criticality_level == "CRITICAL",
        )
    ).all()
    return len(rows)
