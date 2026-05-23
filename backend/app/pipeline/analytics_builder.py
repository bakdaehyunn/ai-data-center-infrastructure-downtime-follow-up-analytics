from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.analytics import (
    BottleneckSummary,
    CriticalRequestQueue,
    RequestCurrentStatus,
    RequestStageLeadTime,
    VendorDelaySummary,
)
from app.models.core import (
    Item,
    ProcurementStageEvent,
    PurchaseOrder,
    PurchaseRequest,
    Receipt,
    Vendor,
)
from app.sample_data.scenarios import EXIT_EVENT_BY_STAGE, STAGE_THRESHOLDS_HOURS


@dataclass(frozen=True)
class AnalyticsBuildResult:
    request_current_status_count: int
    request_stage_lead_times_count: int
    critical_request_queue_count: int
    bottleneck_summary_count: int
    vendor_delay_summary_count: int


@dataclass(frozen=True)
class LeadTimeRecord:
    request_id: str
    stage: str
    entered_at: datetime
    exited_at: datetime | None
    duration_hours: float
    threshold_hours: float
    is_bottleneck: bool
    delay_hours: float


def build_analytics(session: Session, as_of: datetime | None = None) -> AnalyticsBuildResult:
    requests = list(session.scalars(select(PurchaseRequest)))
    events = list(session.scalars(select(ProcurementStageEvent)))
    if not requests or not events:
        _clear_analytics_tables(session)
        session.flush()
        return AnalyticsBuildResult(0, 0, 0, 0, 0)

    as_of_time = as_of or _default_as_of(events)
    _clear_analytics_tables(session)

    events_by_request = _events_by_request(events)
    lead_records = _build_lead_time_records(events_by_request, as_of_time)
    request_by_id = {request.request_id: request for request in requests}
    purchase_orders = list(session.scalars(select(PurchaseOrder)))
    po_by_request = {po.request_id: po for po in purchase_orders}
    vendor_by_id = {vendor.vendor_id: vendor for vendor in session.scalars(select(Vendor))}
    item_by_id = {item.item_id: item for item in session.scalars(select(Item))}
    receipts_by_po = _receipts_by_po(list(session.scalars(select(Receipt))))

    current_status_rows = _build_current_status_rows(
        requests=requests,
        lead_records=lead_records,
        as_of=as_of_time,
    )
    lead_time_rows = [
        RequestStageLeadTime(
            request_id=record.request_id,
            stage=record.stage,
            entered_at=record.entered_at,
            exited_at=record.exited_at,
            duration_hours=round(record.duration_hours, 2),
            threshold_hours=round(record.threshold_hours, 2),
            is_bottleneck=record.is_bottleneck,
            delay_hours=round(record.delay_hours, 2),
        )
        for record in lead_records
    ]
    vendor_rows = _build_vendor_delay_summary_rows(
        purchase_orders=purchase_orders,
        vendor_by_id=vendor_by_id,
        lead_records=lead_records,
    )
    bottleneck_rows = _build_bottleneck_summary_rows(
        lead_records=lead_records,
        request_by_id=request_by_id,
        po_by_request=po_by_request,
        item_by_id=item_by_id,
        summary_date=as_of_time.date(),
    )
    critical_rows = _build_critical_request_queue_rows(
        requests=requests,
        current_status_rows=current_status_rows,
        lead_records=lead_records,
        po_by_request=po_by_request,
        vendor_rows=vendor_rows,
        receipts_by_po=receipts_by_po,
        as_of=as_of_time,
    )

    session.add_all(current_status_rows)
    session.add_all(lead_time_rows)
    session.add_all(vendor_rows)
    session.add_all(bottleneck_rows)
    session.add_all(critical_rows)
    session.flush()

    return AnalyticsBuildResult(
        request_current_status_count=len(current_status_rows),
        request_stage_lead_times_count=len(lead_time_rows),
        critical_request_queue_count=len(critical_rows),
        bottleneck_summary_count=len(bottleneck_rows),
        vendor_delay_summary_count=len(vendor_rows),
    )


def _clear_analytics_tables(session: Session) -> None:
    for model in [
        CriticalRequestQueue,
        RequestCurrentStatus,
        RequestStageLeadTime,
        BottleneckSummary,
        VendorDelaySummary,
    ]:
        session.execute(delete(model))


def _default_as_of(events: list[ProcurementStageEvent]) -> datetime:
    return max(event.occurred_at for event in events) + timedelta(hours=24)


def _events_by_request(
    events: list[ProcurementStageEvent],
) -> dict[str, list[ProcurementStageEvent]]:
    grouped: dict[str, list[ProcurementStageEvent]] = defaultdict(list)
    for event in events:
        grouped[event.request_id].append(event)
    for request_events in grouped.values():
        request_events.sort(key=lambda event: (event.occurred_at, event.event_id))
    return grouped


def _build_lead_time_records(
    events_by_request: dict[str, list[ProcurementStageEvent]],
    as_of: datetime,
) -> list[LeadTimeRecord]:
    records: list[LeadTimeRecord] = []
    for request_id, events in events_by_request.items():
        for index, event in enumerate(events):
            if event.event_type != "ENTERED_STAGE":
                continue
            stage = event.stage
            exited_at = _find_stage_exit_time(events[index + 1 :], stage)
            effective_exit = exited_at or as_of
            duration_hours = max(_hours_between(event.occurred_at, effective_exit), 0)
            threshold_hours = float(STAGE_THRESHOLDS_HOURS.get(stage, 0))
            delay_hours = max(duration_hours - threshold_hours, 0)
            records.append(
                LeadTimeRecord(
                    request_id=request_id,
                    stage=stage,
                    entered_at=event.occurred_at,
                    exited_at=exited_at,
                    duration_hours=duration_hours,
                    threshold_hours=threshold_hours,
                    is_bottleneck=delay_hours > 0,
                    delay_hours=delay_hours,
                )
            )
    return records


def _find_stage_exit_time(events: list[ProcurementStageEvent], stage: str) -> datetime | None:
    expected_exit = EXIT_EVENT_BY_STAGE.get(stage)
    for event in events:
        if event.stage != stage:
            break
        if event.event_type == expected_exit or event.event_type == "CLOSED":
            return event.occurred_at
    return None


def _build_current_status_rows(
    requests: list[PurchaseRequest],
    lead_records: list[LeadTimeRecord],
    as_of: datetime,
) -> list[RequestCurrentStatus]:
    records_by_request_stage = {
        (record.request_id, record.stage): record
        for record in lead_records
    }
    rows: list[RequestCurrentStatus] = []
    for request in requests:
        current_record = records_by_request_stage.get((request.request_id, request.current_stage))
        if current_record is None:
            continue
        days_in_stage = current_record.duration_hours / 24
        delay_days = current_record.delay_hours / 24
        rows.append(
            RequestCurrentStatus(
                request_id=request.request_id,
                current_stage=request.current_stage,
                current_status=request.current_status,
                stage_entered_at=current_record.entered_at,
                days_in_current_stage=round(days_in_stage, 2),
                is_delayed=current_record.is_bottleneck or request.needed_by_date < as_of.date(),
                delay_days=round(max(delay_days, 0), 2),
                needed_by_date=request.needed_by_date,
                criticality_level=request.criticality_level,
                business_impact=request.business_impact,
                next_owner_type=_next_owner_type(request.current_stage),
                next_owner_id=None,
            )
        )
    return rows


def _build_vendor_delay_summary_rows(
    purchase_orders: list[PurchaseOrder],
    vendor_by_id: dict[str, Vendor],
    lead_records: list[LeadTimeRecord],
) -> list[VendorDelaySummary]:
    vendor_confirmation_delay = _delay_by_request_stage(lead_records, "VENDOR_CONFIRMATION")
    delivery_delay = _delivery_delay_by_request(lead_records)
    confirmation_duration = _duration_by_request_stage(lead_records, "VENDOR_CONFIRMATION")
    orders_by_vendor: dict[str, list[PurchaseOrder]] = defaultdict(list)
    for po in purchase_orders:
        orders_by_vendor[po.vendor_id].append(po)

    rows = []
    for vendor_id, orders in sorted(orders_by_vendor.items()):
        vendor = vendor_by_id[vendor_id]
        delayed_count = sum(
            1
            for order in orders
            if vendor_confirmation_delay.get(order.request_id, 0) > 0
            or delivery_delay.get(order.request_id, 0) > 0
        )
        confirmation_hours = [
            confirmation_duration[order.request_id]
            for order in orders
            if order.request_id in confirmation_duration
        ]
        delivery_delay_days = [
            delay_hours / 24
            for order in orders
            if (delay_hours := delivery_delay.get(order.request_id, 0)) > 0
        ]
        total_count = len(orders)
        rows.append(
            VendorDelaySummary(
                vendor_id=vendor_id,
                total_po_count=total_count,
                delayed_po_count=delayed_count,
                delay_rate=round(delayed_count / total_count if total_count else 0, 4),
                avg_confirmation_hours=round(mean(confirmation_hours) if confirmation_hours else 0, 2),
                avg_delivery_delay_days=round(mean(delivery_delay_days) if delivery_delay_days else 0, 2),
                reliability_tier=vendor.reliability_tier,
            )
        )
    return rows


def _build_bottleneck_summary_rows(
    lead_records: list[LeadTimeRecord],
    request_by_id: dict[str, PurchaseRequest],
    po_by_request: dict[str, PurchaseOrder],
    item_by_id: dict[str, Item],
    summary_date,
) -> list[BottleneckSummary]:
    grouped: dict[tuple[str, str, str], list[LeadTimeRecord]] = defaultdict(list)
    for record in lead_records:
        request = request_by_id.get(record.request_id)
        if request is None:
            continue
        grouped[("STAGE", record.stage, record.stage)].append(record)
        grouped[("DEPARTMENT", request.department_id, record.stage)].append(record)
        grouped[("CRITICALITY_LEVEL", request.criticality_level, record.stage)].append(record)
        item = item_by_id.get(request.item_id)
        if item:
            grouped[("ITEM_CATEGORY", item.item_category, record.stage)].append(record)
        po = po_by_request.get(request.request_id)
        if po:
            grouped[("VENDOR", po.vendor_id, record.stage)].append(record)

    rows = []
    for (dimension_type, dimension_id, stage), records in sorted(grouped.items()):
        durations = [record.duration_hours for record in records]
        delay_hours = [record.delay_hours for record in records]
        rows.append(
            BottleneckSummary(
                summary_date=summary_date,
                dimension_type=dimension_type,
                dimension_id=dimension_id,
                stage=stage,
                request_count=len(records),
                delayed_count=sum(1 for record in records if record.is_bottleneck),
                avg_duration_hours=round(mean(durations), 2),
                p90_duration_hours=round(_percentile(durations, 0.9), 2),
                total_delay_hours=round(sum(delay_hours), 2),
            )
        )
    return rows


def _build_critical_request_queue_rows(
    requests: list[PurchaseRequest],
    current_status_rows: list[RequestCurrentStatus],
    lead_records: list[LeadTimeRecord],
    po_by_request: dict[str, PurchaseOrder],
    vendor_rows: list[VendorDelaySummary],
    receipts_by_po: dict[str, list[Receipt]],
    as_of: datetime,
) -> list[CriticalRequestQueue]:
    current_by_request = {row.request_id: row for row in current_status_rows}
    current_delay_by_request = {
        record.request_id: record.delay_hours
        for record in lead_records
        if record.exited_at is None
    }
    vendor_delay_rate = {
        row.vendor_id: float(row.delay_rate)
        for row in vendor_rows
    }
    scored_rows = []
    for request in requests:
        if request.current_status == "CLOSED":
            continue
        current = current_by_request.get(request.request_id)
        if current is None:
            continue
        po = po_by_request.get(request.request_id)
        vendor_risk_score = _vendor_risk_score(po.vendor_id, vendor_delay_rate) if po else 0
        criticality_score = _criticality_score(request.criticality_level)
        delay_score = min(current_delay_by_request.get(request.request_id, 0) / 4, 30)
        business_impact_score = _business_impact_score(request.business_impact)
        needed_by_urgency_score = _needed_by_urgency_score(request.needed_by_date, as_of)
        total = criticality_score + delay_score + business_impact_score + needed_by_urgency_score + vendor_risk_score
        scored_rows.append(
            (
                total,
                CriticalRequestQueue(
                    request_id=request.request_id,
                    priority_rank=0,
                    criticality_score=round(criticality_score, 2),
                    delay_score=round(delay_score, 2),
                    business_impact_score=round(business_impact_score, 2),
                    needed_by_urgency_score=round(needed_by_urgency_score, 2),
                    vendor_risk_score=round(vendor_risk_score, 2),
                    total_priority_score=round(total, 2),
                    recommended_action=_recommended_action(request.current_stage, po, receipts_by_po),
                    reason_summary=_reason_summary(request, current),
                ),
            )
        )

    ranked = []
    for rank, (_, row) in enumerate(sorted(scored_rows, key=lambda item: item[0], reverse=True), start=1):
        row.priority_rank = rank
        ranked.append(row)
    return ranked


def _delay_by_request_stage(records: list[LeadTimeRecord], stage: str) -> dict[str, float]:
    return {
        record.request_id: record.delay_hours
        for record in records
        if record.stage == stage
    }


def _duration_by_request_stage(records: list[LeadTimeRecord], stage: str) -> dict[str, float]:
    return {
        record.request_id: record.duration_hours
        for record in records
        if record.stage == stage
    }


def _delivery_delay_by_request(records: list[LeadTimeRecord]) -> dict[str, float]:
    return _delay_by_request_stage(records, "DELIVERY")


def _receipts_by_po(receipts: list[Receipt]) -> dict[str, list[Receipt]]:
    grouped: dict[str, list[Receipt]] = defaultdict(list)
    for receipt in receipts:
        grouped[receipt.po_id].append(receipt)
    return grouped


def _hours_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * percentile))
    return sorted_values[index]


def _next_owner_type(stage: str) -> str:
    return {
        "REQUEST_SUBMITTED": "REQUESTER",
        "BUDGET_REVIEW": "BUDGET_OWNER",
        "PROCUREMENT_REVIEW": "PROCUREMENT_OPERATOR",
        "PO_CREATION": "PROCUREMENT_OPERATOR",
        "VENDOR_CONFIRMATION": "VENDOR_MANAGER",
        "DELIVERY": "VENDOR_MANAGER",
        "RECEIVING": "WAREHOUSE_OPERATOR",
        "INSPECTION": "INSPECTION_OPERATOR",
        "CLOSED": "NONE",
    }.get(stage, "UNKNOWN")


def _criticality_score(level: str) -> float:
    return {
        "LOW": 5,
        "MEDIUM": 12,
        "HIGH": 20,
        "CRITICAL": 30,
    }.get(level, 0)


def _business_impact_score(impact: str) -> float:
    if "RISK" in impact:
        return 20
    if "DELAY" in impact:
        return 16
    return 8


def _needed_by_urgency_score(needed_by_date, as_of: datetime) -> float:
    days_until_needed = (needed_by_date - as_of.date()).days
    if days_until_needed < 0:
        return 20
    if days_until_needed <= 2:
        return 14
    if days_until_needed <= 5:
        return 8
    return 2


def _vendor_risk_score(vendor_id: str, vendor_delay_rate: dict[str, float]) -> float:
    return min(vendor_delay_rate.get(vendor_id, 0) * 20, 20)


def _recommended_action(
    current_stage: str,
    purchase_order: PurchaseOrder | None,
    receipts_by_po: dict[str, list[Receipt]],
) -> str:
    if current_stage == "BUDGET_REVIEW":
        return "Escalate budget review"
    if current_stage == "PROCUREMENT_REVIEW":
        return "Resolve procurement review issue"
    if current_stage == "PO_CREATION":
        return "Prioritize PO creation"
    if current_stage == "VENDOR_CONFIRMATION":
        return "Escalate vendor confirmation"
    if current_stage == "DELIVERY":
        return "Escalate delivery status"
    if current_stage == "RECEIVING":
        return "Prioritize receiving process"
    if current_stage == "INSPECTION":
        if purchase_order and receipts_by_po.get(purchase_order.po_id):
            return "Prioritize inspection completion"
        return "Confirm receipt before inspection"
    return "Review request status"


def _reason_summary(request: PurchaseRequest, current: RequestCurrentStatus) -> str:
    if current.is_delayed:
        return (
            f"{request.criticality_level} request is delayed in {request.current_stage} "
            f"for {float(current.days_in_current_stage):.1f} days."
        )
    return (
        f"{request.criticality_level} request is currently in {request.current_stage} "
        f"and needed by {request.needed_by_date.isoformat()}."
    )
