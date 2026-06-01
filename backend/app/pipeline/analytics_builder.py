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
from app.models.core import (
    Item,
    ProcurementStageEvent,
    PurchaseOrder,
    PurchaseRequest,
    Receipt,
    Vendor,
)
from app.models.maintenance import (
    Equipment,
    MaintenanceRequest,
    MaintenanceStageEvent,
    MaintenanceWorkOrder,
    Part,
    ProductionLine,
)
from app.sample_data.maintenance_scenarios import (
    MAINTENANCE_EXIT_EVENT_BY_STAGE,
    MAINTENANCE_STAGE_THRESHOLDS_HOURS,
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
class MaintenanceAnalyticsBuildResult:
    maintenance_current_status_count: int
    maintenance_stage_lead_times_count: int
    critical_maintenance_queue_count: int
    maintenance_bottleneck_summary_count: int
    equipment_delay_summary_count: int
    production_line_delay_summary_count: int
    parts_waiting_summary_count: int


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


def build_maintenance_analytics(
    session: Session,
    as_of: datetime | None = None,
) -> MaintenanceAnalyticsBuildResult:
    requests = list(session.scalars(select(MaintenanceRequest)))
    events = list(session.scalars(select(MaintenanceStageEvent)))
    if not requests or not events:
        _clear_maintenance_analytics_tables(session)
        session.flush()
        return MaintenanceAnalyticsBuildResult(0, 0, 0, 0, 0, 0, 0)

    as_of_time = as_of or _default_maintenance_as_of(events)
    _clear_maintenance_analytics_tables(session)

    events_by_request = _maintenance_events_by_request(events)
    lead_records = _build_maintenance_lead_time_records(events_by_request, as_of_time)
    request_by_id = {request.maintenance_request_id: request for request in requests}
    equipment_by_id = {equipment.equipment_id: equipment for equipment in session.scalars(select(Equipment))}
    line_by_id = {line.line_id: line for line in session.scalars(select(ProductionLine))}
    work_orders = list(session.scalars(select(MaintenanceWorkOrder)))
    work_orders_by_request = _maintenance_work_orders_by_request(work_orders)
    part_by_id = {part.part_id: part for part in session.scalars(select(Part))}

    current_status_rows = _build_maintenance_current_status_rows(
        requests=requests,
        equipment_by_id=equipment_by_id,
        lead_records=lead_records,
        as_of=as_of_time,
        work_orders_by_request=work_orders_by_request,
    )
    lead_time_rows = [
        MaintenanceStageLeadTime(
            maintenance_request_id=record.request_id,
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
    bottleneck_rows = _build_maintenance_bottleneck_summary_rows(
        lead_records=lead_records,
        request_by_id=request_by_id,
        equipment_by_id=equipment_by_id,
        line_by_id=line_by_id,
        work_orders_by_request=work_orders_by_request,
        part_by_id=part_by_id,
        summary_date=as_of_time.date(),
    )
    equipment_rows = _build_equipment_delay_summary_rows(
        requests=requests,
        equipment_by_id=equipment_by_id,
        line_by_id=line_by_id,
        lead_records=lead_records,
        current_status_rows=current_status_rows,
    )
    line_rows = _build_production_line_delay_summary_rows(
        requests=requests,
        equipment_by_id=equipment_by_id,
        line_by_id=line_by_id,
        lead_records=lead_records,
        current_status_rows=current_status_rows,
    )
    parts_rows = _build_parts_waiting_summary_rows(
        lead_records=lead_records,
        request_by_id=request_by_id,
        work_orders_by_request=work_orders_by_request,
        part_by_id=part_by_id,
    )
    critical_rows = _build_critical_maintenance_queue_rows(
        requests=requests,
        equipment_by_id=equipment_by_id,
        line_by_id=line_by_id,
        current_status_rows=current_status_rows,
        lead_records=lead_records,
        work_orders_by_request=work_orders_by_request,
        part_by_id=part_by_id,
        as_of=as_of_time,
    )

    session.add_all(current_status_rows)
    session.add_all(lead_time_rows)
    session.add_all(bottleneck_rows)
    session.add_all(equipment_rows)
    session.add_all(line_rows)
    session.add_all(parts_rows)
    session.add_all(critical_rows)
    session.flush()

    return MaintenanceAnalyticsBuildResult(
        maintenance_current_status_count=len(current_status_rows),
        maintenance_stage_lead_times_count=len(lead_time_rows),
        critical_maintenance_queue_count=len(critical_rows),
        maintenance_bottleneck_summary_count=len(bottleneck_rows),
        equipment_delay_summary_count=len(equipment_rows),
        production_line_delay_summary_count=len(line_rows),
        parts_waiting_summary_count=len(parts_rows),
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


def _clear_maintenance_analytics_tables(session: Session) -> None:
    for model in [
        CriticalMaintenanceQueue,
        MaintenanceCurrentStatus,
        MaintenanceStageLeadTime,
        MaintenanceBottleneckSummary,
        EquipmentDelaySummary,
        ProductionLineDelaySummary,
        PartsWaitingSummary,
    ]:
        session.execute(delete(model))


def _default_as_of(events: list[ProcurementStageEvent]) -> datetime:
    return max(event.occurred_at for event in events) + timedelta(hours=24)


def _default_maintenance_as_of(events: list[MaintenanceStageEvent]) -> datetime:
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


def _maintenance_events_by_request(
    events: list[MaintenanceStageEvent],
) -> dict[str, list[MaintenanceStageEvent]]:
    grouped: dict[str, list[MaintenanceStageEvent]] = defaultdict(list)
    for event in events:
        grouped[event.maintenance_request_id].append(event)
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


def _build_maintenance_lead_time_records(
    events_by_request: dict[str, list[MaintenanceStageEvent]],
    as_of: datetime,
) -> list[LeadTimeRecord]:
    records: list[LeadTimeRecord] = []
    for request_id, events in events_by_request.items():
        for index, event in enumerate(events):
            if event.event_type != "ENTERED_STAGE":
                continue
            stage = event.stage
            exited_at = _find_maintenance_stage_exit_time(events[index + 1 :], stage)
            effective_exit = exited_at or as_of
            duration_hours = max(_hours_between(event.occurred_at, effective_exit), 0)
            threshold_hours = float(MAINTENANCE_STAGE_THRESHOLDS_HOURS.get(stage, 0))
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


def _find_maintenance_stage_exit_time(events: list[MaintenanceStageEvent], stage: str) -> datetime | None:
    expected_exit = MAINTENANCE_EXIT_EVENT_BY_STAGE.get(stage)
    for event in events:
        if event.stage != stage:
            break
        if event.event_type == expected_exit or event.event_type == "REQUEST_COMPLETED":
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


def _build_maintenance_current_status_rows(
    requests: list[MaintenanceRequest],
    equipment_by_id: dict[str, Equipment],
    lead_records: list[LeadTimeRecord],
    as_of: datetime,
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
) -> list[MaintenanceCurrentStatus]:
    records_by_request_stage = {
        (record.request_id, record.stage): record
        for record in lead_records
    }
    rows: list[MaintenanceCurrentStatus] = []
    for request in requests:
        current_record = records_by_request_stage.get((request.maintenance_request_id, request.current_stage))
        equipment = equipment_by_id.get(request.equipment_id)
        if current_record is None or equipment is None:
            continue
        rows.append(
            MaintenanceCurrentStatus(
                maintenance_request_id=request.maintenance_request_id,
                equipment_id=request.equipment_id,
                line_id=request.line_id,
                current_stage=request.current_stage,
                current_status=request.current_status,
                stage_entered_at=current_record.entered_at,
                hours_in_current_stage=round(current_record.duration_hours, 2),
                is_delayed=current_record.is_bottleneck or request.needed_by_at < as_of,
                delay_hours=round(max(current_record.delay_hours, 0), 2),
                needed_by_at=request.needed_by_at,
                priority_level=request.priority_level,
                business_impact=request.business_impact,
                next_owner_type=_maintenance_next_owner_type(request.current_stage),
                next_owner_id=_maintenance_next_owner_id(request, work_orders_by_request),
            )
        )
    return rows


def _build_maintenance_bottleneck_summary_rows(
    lead_records: list[LeadTimeRecord],
    request_by_id: dict[str, MaintenanceRequest],
    equipment_by_id: dict[str, Equipment],
    line_by_id: dict[str, ProductionLine],
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
    part_by_id: dict[str, Part],
    summary_date,
) -> list[MaintenanceBottleneckSummary]:
    grouped: dict[tuple[str, str, str], list[LeadTimeRecord]] = defaultdict(list)
    for record in lead_records:
        request = request_by_id.get(record.request_id)
        if request is None:
            continue
        equipment = equipment_by_id.get(request.equipment_id)
        line = line_by_id.get(request.line_id)
        grouped[("STAGE", record.stage, record.stage)].append(record)
        grouped[("PRIORITY_LEVEL", request.priority_level, record.stage)].append(record)
        grouped[("REQUEST_TYPE", request.request_type, record.stage)].append(record)
        grouped[("FAILURE_MODE", request.failure_mode, record.stage)].append(record)
        if equipment:
            grouped[("EQUIPMENT", equipment.equipment_id, record.stage)].append(record)
            grouped[("EQUIPMENT_TYPE", equipment.equipment_type, record.stage)].append(record)
            grouped[("EQUIPMENT_CRITICALITY", equipment.criticality_level, record.stage)].append(record)
        if line:
            grouped[("PRODUCTION_LINE", line.line_id, record.stage)].append(record)
        for work_order in work_orders_by_request.get(request.maintenance_request_id, []):
            grouped[("TECHNICIAN_TEAM", work_order.assigned_team, record.stage)].append(record)
            if work_order.required_part_id and work_order.required_part_id in part_by_id:
                part = part_by_id[work_order.required_part_id]
                grouped[("PART_CATEGORY", part.part_category, record.stage)].append(record)

    rows = []
    for (dimension_type, dimension_id, stage), records in sorted(grouped.items()):
        durations = [record.duration_hours for record in records]
        delay_hours = [record.delay_hours for record in records]
        delayed_count = sum(1 for record in records if record.is_bottleneck)
        rows.append(
            MaintenanceBottleneckSummary(
                summary_date=summary_date,
                dimension_type=dimension_type,
                dimension_id=dimension_id,
                stage=stage,
                request_count=len(records),
                delayed_count=delayed_count,
                delay_rate=round(delayed_count / len(records) if records else 0, 4),
                avg_duration_hours=round(mean(durations), 2),
                p90_duration_hours=round(_percentile(durations, 0.9), 2),
                total_delay_hours=round(sum(delay_hours), 2),
            )
        )
    return rows


def _build_equipment_delay_summary_rows(
    requests: list[MaintenanceRequest],
    equipment_by_id: dict[str, Equipment],
    line_by_id: dict[str, ProductionLine],
    lead_records: list[LeadTimeRecord],
    current_status_rows: list[MaintenanceCurrentStatus],
) -> list[EquipmentDelaySummary]:
    request_ids_with_lead_times = {record.request_id for record in lead_records}
    requests_by_equipment: dict[str, list[MaintenanceRequest]] = defaultdict(list)
    for request in requests:
        if request.equipment_id in equipment_by_id and request.maintenance_request_id in request_ids_with_lead_times:
            requests_by_equipment[request.equipment_id].append(request)
    delayed_request_ids = {row.maintenance_request_id for row in current_status_rows if row.is_delayed}
    delay_by_request = _total_delay_by_request(lead_records)
    repair_duration_by_request = _duration_by_request_stage(lead_records, "MAINTENANCE_IN_PROGRESS")

    rows: list[EquipmentDelaySummary] = []
    for equipment_id, equipment_requests in sorted(requests_by_equipment.items()):
        equipment = equipment_by_id[equipment_id]
        line = line_by_id[equipment.line_id]
        failure_modes = [request.failure_mode for request in equipment_requests]
        repair_durations = [
            repair_duration_by_request[request.maintenance_request_id]
            for request in equipment_requests
            if request.maintenance_request_id in repair_duration_by_request
        ]
        rows.append(
            EquipmentDelaySummary(
                equipment_id=equipment_id,
                equipment_name=equipment.equipment_name,
                line_id=line.line_id,
                line_name=line.line_name,
                request_count=len(equipment_requests),
                delayed_request_count=sum(
                    1 for request in equipment_requests if request.maintenance_request_id in delayed_request_ids
                ),
                repeat_failure_count=len(equipment_requests) if len(equipment_requests) > 1 else 0,
                total_downtime_hours=round(
                    sum(float(request.actual_downtime_hours or request.estimated_downtime_hours) for request in equipment_requests)
                    + sum(delay_by_request.get(request.maintenance_request_id, 0) for request in equipment_requests),
                    2,
                ),
                avg_repair_duration_hours=round(mean(repair_durations) if repair_durations else 0, 2),
                top_failure_mode=_most_common(failure_modes),
            )
        )
    return rows


def _build_production_line_delay_summary_rows(
    requests: list[MaintenanceRequest],
    equipment_by_id: dict[str, Equipment],
    line_by_id: dict[str, ProductionLine],
    lead_records: list[LeadTimeRecord],
    current_status_rows: list[MaintenanceCurrentStatus],
) -> list[ProductionLineDelaySummary]:
    request_ids_with_lead_times = {record.request_id for record in lead_records}
    requests_by_line: dict[str, list[MaintenanceRequest]] = defaultdict(list)
    for request in requests:
        if request.line_id in line_by_id and request.maintenance_request_id in request_ids_with_lead_times:
            requests_by_line[request.line_id].append(request)
    current_by_request = {row.maintenance_request_id: row for row in current_status_rows}
    delayed_request_ids = {row.maintenance_request_id for row in current_status_rows if row.is_delayed}
    delay_by_request = _total_delay_by_request(lead_records)
    bottleneck_stage_by_request = _top_bottleneck_stage_by_request(lead_records)

    rows: list[ProductionLineDelaySummary] = []
    for line_id, line_requests in sorted(requests_by_line.items()):
        line = line_by_id[line_id]
        bottleneck_stages = [
            bottleneck_stage_by_request[request.maintenance_request_id]
            for request in line_requests
            if request.maintenance_request_id in bottleneck_stage_by_request
        ]
        rows.append(
            ProductionLineDelaySummary(
                line_id=line_id,
                line_name=line.line_name,
                open_request_count=sum(1 for request in line_requests if request.current_status != "COMPLETED"),
                delayed_request_count=sum(
                    1 for request in line_requests if request.maintenance_request_id in delayed_request_ids
                ),
                critical_equipment_delayed_count=sum(
                    1
                    for request in line_requests
                    if request.maintenance_request_id in delayed_request_ids
                    and equipment_by_id[request.equipment_id].criticality_level == "CRITICAL"
                ),
                total_downtime_hours=round(
                    sum(float(request.actual_downtime_hours or request.estimated_downtime_hours) for request in line_requests)
                    + sum(delay_by_request.get(request.maintenance_request_id, 0) for request in line_requests),
                    2,
                ),
                top_bottleneck_stage=_most_common(bottleneck_stages) if bottleneck_stages else "NONE",
            )
        )
    return rows


def _build_parts_waiting_summary_rows(
    lead_records: list[LeadTimeRecord],
    request_by_id: dict[str, MaintenanceRequest],
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
    part_by_id: dict[str, Part],
) -> list[PartsWaitingSummary]:
    parts_waiting_records = [
        record
        for record in lead_records
        if record.stage == "PARTS_WAITING" and record.delay_hours > 0
    ]
    records_by_part: dict[str, list[LeadTimeRecord]] = defaultdict(list)
    for record in parts_waiting_records:
        request = request_by_id.get(record.request_id)
        if request is None:
            continue
        for work_order in work_orders_by_request.get(request.maintenance_request_id, []):
            if work_order.required_part_id and work_order.required_part_id in part_by_id:
                records_by_part[work_order.required_part_id].append(record)

    rows: list[PartsWaitingSummary] = []
    for part_id, records in sorted(records_by_part.items()):
        part = part_by_id[part_id]
        wait_hours = [record.duration_hours for record in records]
        rows.append(
            PartsWaitingSummary(
                part_id=part_id,
                part_name=part.part_name,
                part_category=part.part_category,
                waiting_request_count=len({record.request_id for record in records}),
                total_wait_hours=round(sum(wait_hours), 2),
                avg_wait_hours=round(mean(wait_hours), 2),
                critical_spare=part.critical_spare,
                stock_status=part.stock_status,
            )
        )
    return rows


def _build_critical_maintenance_queue_rows(
    requests: list[MaintenanceRequest],
    equipment_by_id: dict[str, Equipment],
    line_by_id: dict[str, ProductionLine],
    current_status_rows: list[MaintenanceCurrentStatus],
    lead_records: list[LeadTimeRecord],
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
    part_by_id: dict[str, Part],
    as_of: datetime,
) -> list[CriticalMaintenanceQueue]:
    current_by_request = {row.maintenance_request_id: row for row in current_status_rows}
    current_delay_by_request = {
        record.request_id: record.delay_hours
        for record in lead_records
        if record.exited_at is None
    }
    repeat_failure_count_by_equipment = _repeat_failure_count_by_equipment(requests)

    scored_rows = []
    for request in requests:
        if request.current_status == "COMPLETED":
            continue
        current = current_by_request.get(request.maintenance_request_id)
        equipment = equipment_by_id.get(request.equipment_id)
        line = line_by_id.get(request.line_id)
        if current is None or equipment is None or line is None:
            continue
        equipment_criticality_score = _equipment_criticality_score(equipment.criticality_level)
        downtime_score = min(float(request.estimated_downtime_hours) * 1.2, 30)
        stage_delay_score = min(current_delay_by_request.get(request.maintenance_request_id, 0) / 3, 35)
        production_line_impact_score = _production_line_impact_score(line.line_priority)
        needed_by_urgency_score = _maintenance_needed_by_urgency_score(request.needed_by_at, as_of)
        repeat_failure_score = min(max(repeat_failure_count_by_equipment.get(request.equipment_id, 1) - 1, 0) * 8, 16)
        parts_risk_score = _parts_risk_score(request, work_orders_by_request, part_by_id)
        total = (
            equipment_criticality_score
            + downtime_score
            + stage_delay_score
            + production_line_impact_score
            + needed_by_urgency_score
            + repeat_failure_score
            + parts_risk_score
        )
        scored_rows.append(
            (
                total,
                CriticalMaintenanceQueue(
                    maintenance_request_id=request.maintenance_request_id,
                    priority_rank=0,
                    equipment_id=request.equipment_id,
                    line_id=request.line_id,
                    current_stage=request.current_stage,
                    equipment_criticality_score=round(equipment_criticality_score, 2),
                    downtime_score=round(downtime_score, 2),
                    stage_delay_score=round(stage_delay_score, 2),
                    production_line_impact_score=round(production_line_impact_score, 2),
                    needed_by_urgency_score=round(needed_by_urgency_score, 2),
                    repeat_failure_score=round(repeat_failure_score, 2),
                    parts_risk_score=round(parts_risk_score, 2),
                    total_priority_score=round(total, 2),
                    recommended_action=_maintenance_recommended_action(request, work_orders_by_request, part_by_id),
                    reason_summary=_maintenance_reason_summary(request, current, equipment, line),
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


def _total_delay_by_request(records: list[LeadTimeRecord]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for record in records:
        totals[record.request_id] += record.delay_hours
    return dict(totals)


def _top_bottleneck_stage_by_request(records: list[LeadTimeRecord]) -> dict[str, str]:
    top: dict[str, tuple[str, float]] = {}
    for record in records:
        if record.delay_hours <= 0:
            continue
        current = top.get(record.request_id)
        if current is None or record.delay_hours > current[1]:
            top[record.request_id] = (record.stage, record.delay_hours)
    return {request_id: stage for request_id, (stage, _) in top.items()}


def _delivery_delay_by_request(records: list[LeadTimeRecord]) -> dict[str, float]:
    return _delay_by_request_stage(records, "DELIVERY")


def _receipts_by_po(receipts: list[Receipt]) -> dict[str, list[Receipt]]:
    grouped: dict[str, list[Receipt]] = defaultdict(list)
    for receipt in receipts:
        grouped[receipt.po_id].append(receipt)
    return grouped


def _maintenance_work_orders_by_request(
    work_orders: list[MaintenanceWorkOrder],
) -> dict[str, list[MaintenanceWorkOrder]]:
    grouped: dict[str, list[MaintenanceWorkOrder]] = defaultdict(list)
    for work_order in work_orders:
        grouped[work_order.maintenance_request_id].append(work_order)
    return grouped


def _repeat_failure_count_by_equipment(requests: list[MaintenanceRequest]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for request in requests:
        counts[request.equipment_id] += 1
    return dict(counts)


def _hours_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0
    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * percentile))
    return sorted_values[index]


def _most_common(values: list[str]) -> str:
    if not values:
        return "NONE"
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


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


def _maintenance_next_owner_type(stage: str) -> str:
    return {
        "MAINTENANCE_REQUEST_SUBMITTED": "REQUESTER",
        "MAINTENANCE_REVIEW": "MAINTENANCE_PLANNER",
        "TECHNICIAN_ASSIGNED": "MAINTENANCE_SUPERVISOR",
        "PARTS_WAITING": "STOREROOM",
        "MAINTENANCE_IN_PROGRESS": "TECHNICIAN",
        "INSPECTION": "INSPECTOR",
        "COMPLETED": "NONE",
    }.get(stage, "UNKNOWN")


def _maintenance_next_owner_id(
    request: MaintenanceRequest,
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
) -> str | None:
    work_orders = work_orders_by_request.get(request.maintenance_request_id, [])
    if request.current_stage == "MAINTENANCE_IN_PROGRESS":
        for work_order in work_orders:
            if work_order.assigned_technician_id:
                return work_order.assigned_technician_id
    if request.current_stage in {"TECHNICIAN_ASSIGNED", "PARTS_WAITING"} and work_orders:
        return work_orders[0].assigned_team
    return None


def _criticality_score(level: str) -> float:
    return {
        "LOW": 5,
        "MEDIUM": 12,
        "HIGH": 20,
        "CRITICAL": 30,
    }.get(level, 0)


def _equipment_criticality_score(level: str) -> float:
    return {
        "LOW": 5,
        "MEDIUM": 12,
        "HIGH": 22,
        "CRITICAL": 35,
    }.get(level, 0)


def _production_line_impact_score(priority: str) -> float:
    return {
        "LOW": 4,
        "MEDIUM": 8,
        "HIGH": 16,
        "CRITICAL": 24,
    }.get(priority, 0)


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


def _maintenance_needed_by_urgency_score(needed_by_at: datetime, as_of: datetime) -> float:
    hours_until_needed = (needed_by_at - as_of).total_seconds() / 3600
    if hours_until_needed < 0:
        return 24
    if hours_until_needed <= 12:
        return 18
    if hours_until_needed <= 24:
        return 12
    if hours_until_needed <= 72:
        return 6
    return 2


def _parts_risk_score(
    request: MaintenanceRequest,
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
    part_by_id: dict[str, Part],
) -> float:
    score = 0.0
    for work_order in work_orders_by_request.get(request.maintenance_request_id, []):
        part = part_by_id.get(work_order.required_part_id) if work_order.required_part_id else None
        if work_order.work_order_status == "WAITING_PARTS":
            score = max(score, 14)
        if part and part.stock_status == "OUT_OF_STOCK":
            score = max(score, 18)
        elif part and part.stock_status == "LOW_STOCK":
            score = max(score, 10)
        if part and part.critical_spare:
            score += 4
    return min(score, 22)


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


def _maintenance_recommended_action(
    request: MaintenanceRequest,
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
    part_by_id: dict[str, Part],
) -> str:
    if request.current_stage == "MAINTENANCE_REVIEW":
        return "Escalate maintenance review"
    if request.current_stage == "TECHNICIAN_ASSIGNED":
        return "Assign technician or rebalance maintenance team"
    if request.current_stage == "PARTS_WAITING":
        for work_order in work_orders_by_request.get(request.maintenance_request_id, []):
            part = part_by_id.get(work_order.required_part_id) if work_order.required_part_id else None
            if part and part.stock_status == "OUT_OF_STOCK":
                return "Expedite required part or approve substitute"
        return "Confirm required part availability"
    if request.current_stage == "MAINTENANCE_IN_PROGRESS":
        return "Escalate active repair completion"
    if request.current_stage == "INSPECTION":
        return "Prioritize post-maintenance inspection"
    return "Review maintenance request status"


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


def _maintenance_reason_summary(
    request: MaintenanceRequest,
    current: MaintenanceCurrentStatus,
    equipment: Equipment,
    line: ProductionLine,
) -> str:
    if current.is_delayed:
        return (
            f"{equipment.criticality_level} equipment on {line.line_name} is delayed in "
            f"{request.current_stage} for {float(current.hours_in_current_stage):.1f} hours."
        )
    return (
        f"{equipment.criticality_level} equipment request is in {request.current_stage} "
        f"and needed by {request.needed_by_at.isoformat()}."
    )
