from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.analytics import (
    BottleneckSummary,
    CriticalRequestQueue,
    RequestCurrentStatus,
    RequestStageLeadTime,
    VendorDelaySummary,
)
from app.models.core import Department, Item, PurchaseOrder, PurchaseRequest, Vendor
from app.models.ops import DataQualityCheckResult, PipelineRun
from app.sample_data.scenarios import STAGE_FLOW
from app.schemas.analytics import (
    CriticalRequestResponse,
    DataQualityCheckResponse,
    FilterMetadataResponse,
    FilterOption,
    OverviewResponse,
    PipelineRunResponse,
    StageBottleneckResponse,
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
    db: Session = Depends(get_db),
) -> list[StageBottleneckResponse]:
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
    db: Session = Depends(get_db),
) -> list[VendorBottleneckResponse]:
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
            total_priority_score=float(queue.total_priority_score),
            recommended_action=queue.recommended_action,
            reason_summary=queue.reason_summary,
        )
        for queue, request, department, current in rows
    ]


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
    return [
        DataQualityCheckResponse(
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
        for result in results
    ]


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


def _latest_pipeline_run(db: Session) -> Optional[PipelineRun]:
    return db.scalar(select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1))


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
