from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.infrastructure_ontology import (
    INFRASTRUCTURE_EXIT_EVENT_BY_STAGE,
    INFRASTRUCTURE_STAGE_THRESHOLDS_HOURS,
    TERMINAL_STAGE,
    TERMINAL_STATUS,
)
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
    InfrastructureImpactSnapshot,
    InfrastructureIncident,
    IncidentStageEvent,
    FacilityWorkOrder,
    CriticalSpare,
    InfrastructureZone,
)

@dataclass(frozen=True)
class AnalyticsBuildResult:
    incident_current_status_count: int
    incident_stage_lead_times_count: int
    downtime_follow_up_queue_count: int
    infrastructure_bottleneck_summary_count: int
    asset_delay_summary_count: int
    zone_delay_summary_count: int
    spare_waiting_summary_count: int


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


def build_analytics(
    session: Session,
    as_of: datetime | None = None,
) -> AnalyticsBuildResult:
    requests = list(session.scalars(select(InfrastructureIncident)))
    events = list(session.scalars(select(IncidentStageEvent)))
    if not requests or not events:
        _clear_analytics_tables(session)
        session.flush()
        return AnalyticsBuildResult(0, 0, 0, 0, 0, 0, 0)

    as_of_time = as_of or _default_as_of(events)
    _clear_analytics_tables(session)

    events_by_request = _events_by_request(events)
    lead_records = _build_lead_time_records(events_by_request, as_of_time)
    request_by_id = {request.incident_id: request for request in requests}
    asset_by_id = {asset.asset_id: asset for asset in session.scalars(select(InfrastructureAsset))}
    zone_by_id = {zone.zone_id: zone for zone in session.scalars(select(InfrastructureZone))}
    work_orders = list(session.scalars(select(FacilityWorkOrder)))
    work_orders_by_request = _work_orders_by_request(work_orders)
    part_by_id = {part.spare_id: part for part in session.scalars(select(CriticalSpare))}
    impact_by_request = _latest_impact_by_request(list(session.scalars(select(InfrastructureImpactSnapshot))))

    current_status_rows = _build_current_status_rows(
        requests=requests,
        asset_by_id=asset_by_id,
        lead_records=lead_records,
        as_of=as_of_time,
        work_orders_by_request=work_orders_by_request,
    )
    lead_time_rows = [
        IncidentStageLeadTime(
            incident_id=record.request_id,
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
    bottleneck_rows = _build_bottleneck_summary_rows(
        lead_records=lead_records,
        request_by_id=request_by_id,
        asset_by_id=asset_by_id,
        zone_by_id=zone_by_id,
        work_orders_by_request=work_orders_by_request,
        part_by_id=part_by_id,
        summary_date=as_of_time.date(),
    )
    asset_rows = _build_asset_delay_summary_rows(
        requests=requests,
        asset_by_id=asset_by_id,
        zone_by_id=zone_by_id,
        lead_records=lead_records,
        current_status_rows=current_status_rows,
    )
    zone_rows = _build_zone_delay_summary_rows(
        requests=requests,
        asset_by_id=asset_by_id,
        zone_by_id=zone_by_id,
        lead_records=lead_records,
        current_status_rows=current_status_rows,
    )
    spare_rows = _build_spare_waiting_summary_rows(
        lead_records=lead_records,
        request_by_id=request_by_id,
        work_orders_by_request=work_orders_by_request,
        part_by_id=part_by_id,
    )
    follow_up_rows = _build_downtime_follow_up_queue_rows(
        requests=requests,
        asset_by_id=asset_by_id,
        zone_by_id=zone_by_id,
        current_status_rows=current_status_rows,
        lead_records=lead_records,
        work_orders_by_request=work_orders_by_request,
        part_by_id=part_by_id,
        impact_by_request=impact_by_request,
        as_of=as_of_time,
    )

    session.add_all(current_status_rows)
    session.add_all(lead_time_rows)
    session.add_all(bottleneck_rows)
    session.add_all(asset_rows)
    session.add_all(zone_rows)
    session.add_all(spare_rows)
    session.add_all(follow_up_rows)
    session.flush()

    return AnalyticsBuildResult(
        incident_current_status_count=len(current_status_rows),
        incident_stage_lead_times_count=len(lead_time_rows),
        downtime_follow_up_queue_count=len(follow_up_rows),
        infrastructure_bottleneck_summary_count=len(bottleneck_rows),
        asset_delay_summary_count=len(asset_rows),
        zone_delay_summary_count=len(zone_rows),
        spare_waiting_summary_count=len(spare_rows),
    )


def _clear_analytics_tables(session: Session) -> None:
    for model in [
        DowntimeFollowUpQueue,
        IncidentCurrentStatus,
        IncidentStageLeadTime,
        InfrastructureBottleneckSummary,
        AssetDelaySummary,
        ZoneDelaySummary,
        SpareWaitingSummary,
    ]:
        session.execute(delete(model))


def _default_as_of(events: list[IncidentStageEvent]) -> datetime:
    workflow_events = [
        event
        for event in events
        if event.event_type == "ENTERED_STAGE"
        or event.event_type == "INCIDENT_RESTORED"
        or event.event_type in INFRASTRUCTURE_EXIT_EVENT_BY_STAGE.values()
    ]
    return max(event.occurred_at for event in workflow_events or events) + timedelta(hours=24)


def _events_by_request(
    events: list[IncidentStageEvent],
) -> dict[str, list[IncidentStageEvent]]:
    grouped: dict[str, list[IncidentStageEvent]] = defaultdict(list)
    for event in events:
        grouped[event.incident_id].append(event)
    for request_events in grouped.values():
        request_events.sort(key=lambda event: (event.occurred_at, event.event_id))
    return grouped


def _build_lead_time_records(
    events_by_request: dict[str, list[IncidentStageEvent]],
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
            threshold_hours = float(INFRASTRUCTURE_STAGE_THRESHOLDS_HOURS.get(stage, 0))
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


def _find_stage_exit_time(events: list[IncidentStageEvent], stage: str) -> datetime | None:
    expected_exit = INFRASTRUCTURE_EXIT_EVENT_BY_STAGE.get(stage)
    for event in events:
        if event.stage != stage:
            break
        if event.event_type == expected_exit or event.event_type == "INCIDENT_RESTORED":
            return event.occurred_at
    return None


def _build_current_status_rows(
    requests: list[InfrastructureIncident],
    asset_by_id: dict[str, InfrastructureAsset],
    lead_records: list[LeadTimeRecord],
    as_of: datetime,
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
) -> list[IncidentCurrentStatus]:
    records_by_request_stage = {
        (record.request_id, record.stage): record
        for record in lead_records
    }
    rows: list[IncidentCurrentStatus] = []
    for request in requests:
        current_record = records_by_request_stage.get((request.incident_id, request.current_stage))
        asset = asset_by_id.get(request.asset_id)
        if current_record is None or asset is None:
            continue
        rows.append(
            IncidentCurrentStatus(
                incident_id=request.incident_id,
                asset_id=request.asset_id,
                zone_id=request.zone_id,
                current_stage=request.current_stage,
                current_status=request.current_status,
                stage_entered_at=current_record.entered_at,
                hours_in_current_stage=round(current_record.duration_hours, 2),
                is_delayed=current_record.is_bottleneck or request.needed_by_at < as_of,
                delay_hours=round(max(current_record.delay_hours, 0), 2),
                needed_by_at=request.needed_by_at,
                priority_level=request.priority_level,
                business_impact=request.business_impact,
                next_owner_type=_next_owner_type(request.current_stage),
                next_owner_id=_next_owner_id(request, work_orders_by_request),
            )
        )
    return rows


def _build_bottleneck_summary_rows(
    lead_records: list[LeadTimeRecord],
    request_by_id: dict[str, InfrastructureIncident],
    asset_by_id: dict[str, InfrastructureAsset],
    zone_by_id: dict[str, InfrastructureZone],
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
    part_by_id: dict[str, CriticalSpare],
    summary_date,
) -> list[InfrastructureBottleneckSummary]:
    grouped: dict[tuple[str, str, str], list[LeadTimeRecord]] = defaultdict(list)
    for record in lead_records:
        if record.stage == TERMINAL_STAGE:
            continue
        request = request_by_id.get(record.request_id)
        if request is None:
            continue
        asset = asset_by_id.get(request.asset_id)
        zone = zone_by_id.get(request.zone_id)
        grouped[("STAGE", record.stage, record.stage)].append(record)
        grouped[("PRIORITY_LEVEL", request.priority_level, record.stage)].append(record)
        grouped[("REQUEST_TYPE", request.request_type, record.stage)].append(record)
        grouped[("FAILURE_MODE", request.failure_mode, record.stage)].append(record)
        if asset:
            grouped[("ASSET", asset.asset_id, record.stage)].append(record)
            grouped[("ASSET_TYPE", asset.asset_type, record.stage)].append(record)
            grouped[("ASSET_CRITICALITY", asset.criticality_level, record.stage)].append(record)
        if zone:
            grouped[("INFRASTRUCTURE_ZONE", zone.zone_id, record.stage)].append(record)
        for work_order in work_orders_by_request.get(request.incident_id, []):
            grouped[("FACILITIES_TEAM", work_order.assigned_team, record.stage)].append(record)
            if work_order.required_spare_id and work_order.required_spare_id in part_by_id:
                part = part_by_id[work_order.required_spare_id]
                grouped[("SPARE_CATEGORY", part.spare_category, record.stage)].append(record)

    rows = []
    for (dimension_type, dimension_id, stage), records in sorted(grouped.items()):
        durations = [record.duration_hours for record in records]
        delay_hours = [record.delay_hours for record in records]
        delayed_count = sum(1 for record in records if record.is_bottleneck)
        rows.append(
            InfrastructureBottleneckSummary(
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


def _build_asset_delay_summary_rows(
    requests: list[InfrastructureIncident],
    asset_by_id: dict[str, InfrastructureAsset],
    zone_by_id: dict[str, InfrastructureZone],
    lead_records: list[LeadTimeRecord],
    current_status_rows: list[IncidentCurrentStatus],
) -> list[AssetDelaySummary]:
    request_ids_with_lead_times = {record.request_id for record in lead_records}
    requests_by_asset: dict[str, list[InfrastructureIncident]] = defaultdict(list)
    for request in requests:
        if request.asset_id in asset_by_id and request.incident_id in request_ids_with_lead_times:
            requests_by_asset[request.asset_id].append(request)
    delayed_request_ids = {row.incident_id for row in current_status_rows if row.is_delayed}
    delay_by_request = _total_delay_by_request(lead_records)
    repair_duration_by_request = _duration_by_request_stage(lead_records, "REPAIR_IN_PROGRESS")

    rows: list[AssetDelaySummary] = []
    for asset_id, asset_requests in sorted(requests_by_asset.items()):
        asset = asset_by_id[asset_id]
        zone = zone_by_id[asset.zone_id]
        failure_modes = [request.failure_mode for request in asset_requests]
        repair_durations = [
            repair_duration_by_request[request.incident_id]
            for request in asset_requests
            if request.incident_id in repair_duration_by_request
        ]
        rows.append(
            AssetDelaySummary(
                asset_id=asset_id,
                asset_name=asset.asset_name,
                zone_id=zone.zone_id,
                zone_name=zone.zone_name,
                request_count=len(asset_requests),
                delayed_request_count=sum(
                    1 for request in asset_requests if request.incident_id in delayed_request_ids
                ),
                repeat_failure_count=len(asset_requests) if len(asset_requests) > 1 else 0,
                total_downtime_hours=round(
                    sum(float(request.actual_downtime_hours or request.estimated_downtime_hours) for request in asset_requests)
                    + sum(delay_by_request.get(request.incident_id, 0) for request in asset_requests),
                    2,
                ),
                avg_repair_duration_hours=round(mean(repair_durations) if repair_durations else 0, 2),
                top_failure_mode=_most_common(failure_modes),
            )
        )
    return rows


def _build_zone_delay_summary_rows(
    requests: list[InfrastructureIncident],
    asset_by_id: dict[str, InfrastructureAsset],
    zone_by_id: dict[str, InfrastructureZone],
    lead_records: list[LeadTimeRecord],
    current_status_rows: list[IncidentCurrentStatus],
) -> list[ZoneDelaySummary]:
    request_ids_with_lead_times = {record.request_id for record in lead_records}
    requests_by_zone: dict[str, list[InfrastructureIncident]] = defaultdict(list)
    for request in requests:
        if request.zone_id in zone_by_id and request.incident_id in request_ids_with_lead_times:
            requests_by_zone[request.zone_id].append(request)
    delayed_request_ids = {row.incident_id for row in current_status_rows if row.is_delayed}
    delay_by_request = _total_delay_by_request(lead_records)
    bottleneck_stage_by_request = _top_bottleneck_stage_by_request(lead_records)

    rows: list[ZoneDelaySummary] = []
    for zone_id, zone_requests in sorted(requests_by_zone.items()):
        zone = zone_by_id[zone_id]
        bottleneck_stages = [
            bottleneck_stage_by_request[request.incident_id]
            for request in zone_requests
            if request.incident_id in bottleneck_stage_by_request
        ]
        rows.append(
            ZoneDelaySummary(
                zone_id=zone_id,
                zone_name=zone.zone_name,
                open_request_count=sum(1 for request in zone_requests if request.current_status != TERMINAL_STATUS),
                delayed_request_count=sum(
                    1 for request in zone_requests if request.incident_id in delayed_request_ids
                ),
                critical_asset_delayed_count=sum(
                    1
                    for request in zone_requests
                    if request.incident_id in delayed_request_ids
                    and asset_by_id[request.asset_id].criticality_level == "CRITICAL"
                ),
                total_downtime_hours=round(
                    sum(float(request.actual_downtime_hours or request.estimated_downtime_hours) for request in zone_requests)
                    + sum(delay_by_request.get(request.incident_id, 0) for request in zone_requests),
                    2,
                ),
                top_bottleneck_stage=_most_common(bottleneck_stages) if bottleneck_stages else "NONE",
            )
        )
    return rows


def _build_spare_waiting_summary_rows(
    lead_records: list[LeadTimeRecord],
    request_by_id: dict[str, InfrastructureIncident],
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
    part_by_id: dict[str, CriticalSpare],
) -> list[SpareWaitingSummary]:
    spare_waiting_records = [
        record
        for record in lead_records
        if record.stage == "SPARE_VENDOR_WAITING" and record.delay_hours > 0
    ]
    records_by_part: dict[str, list[LeadTimeRecord]] = defaultdict(list)
    for record in spare_waiting_records:
        request = request_by_id.get(record.request_id)
        if request is None:
            continue
        for work_order in work_orders_by_request.get(request.incident_id, []):
            if work_order.required_spare_id and work_order.required_spare_id in part_by_id:
                records_by_part[work_order.required_spare_id].append(record)

    rows: list[SpareWaitingSummary] = []
    for spare_id, records in sorted(records_by_part.items()):
        part = part_by_id[spare_id]
        wait_hours = [record.duration_hours for record in records]
        rows.append(
            SpareWaitingSummary(
                spare_id=spare_id,
                spare_name=part.spare_name,
                spare_category=part.spare_category,
                waiting_request_count=len({record.request_id for record in records}),
                total_wait_hours=round(sum(wait_hours), 2),
                avg_wait_hours=round(mean(wait_hours), 2),
                critical_spare=part.critical_spare,
                stock_status=part.stock_status,
            )
        )
    return rows


def _build_downtime_follow_up_queue_rows(
    requests: list[InfrastructureIncident],
    asset_by_id: dict[str, InfrastructureAsset],
    zone_by_id: dict[str, InfrastructureZone],
    current_status_rows: list[IncidentCurrentStatus],
    lead_records: list[LeadTimeRecord],
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
    part_by_id: dict[str, CriticalSpare],
    impact_by_request: dict[str, InfrastructureImpactSnapshot],
    as_of: datetime,
) -> list[DowntimeFollowUpQueue]:
    current_by_request = {row.incident_id: row for row in current_status_rows}
    current_delay_by_request = {
        record.request_id: record.delay_hours
        for record in lead_records
        if record.exited_at is None
    }
    repeat_failure_count_by_asset = _repeat_failure_count_by_asset(requests)

    scored_rows = []
    for request in requests:
        if request.current_status == TERMINAL_STATUS:
            continue
        current = current_by_request.get(request.incident_id)
        asset = asset_by_id.get(request.asset_id)
        zone = zone_by_id.get(request.zone_id)
        if current is None or asset is None or zone is None:
            continue
        asset_criticality_score = _asset_criticality_score(asset.criticality_level)
        downtime_score = min(float(request.estimated_downtime_hours) * 1.2, 30)
        stage_delay_score = min(current_delay_by_request.get(request.incident_id, 0) / 3, 35)
        infrastructure_zone_impact_score = _infrastructure_zone_impact_score(zone.zone_priority)
        needed_by_urgency_score = _needed_by_urgency_score(request.needed_by_at, as_of)
        repeat_failure_score = min(max(repeat_failure_count_by_asset.get(request.asset_id, 1) - 1, 0) * 8, 16)
        spare_risk_score = _spare_risk_score(request, work_orders_by_request, part_by_id)
        impact = impact_by_request.get(request.incident_id)
        capacity_risk_score = _capacity_risk_score(impact)
        redundancy_risk_score = _redundancy_risk_score(impact)
        thermal_risk_score = _thermal_risk_score(impact)
        vendor_eta_risk_score = _vendor_eta_risk_score(impact, as_of)
        mitigation_credit_score = _mitigation_credit_score(impact)
        total = (
            asset_criticality_score
            + downtime_score
            + stage_delay_score
            + infrastructure_zone_impact_score
            + needed_by_urgency_score
            + repeat_failure_score
            + spare_risk_score
            + capacity_risk_score
            + redundancy_risk_score
            + thermal_risk_score
            + vendor_eta_risk_score
            - mitigation_credit_score
        )
        scored_rows.append(
            (
                total,
                DowntimeFollowUpQueue(
                    incident_id=request.incident_id,
                    priority_rank=0,
                    asset_id=request.asset_id,
                    zone_id=request.zone_id,
                    current_stage=request.current_stage,
                    asset_criticality_score=round(asset_criticality_score, 2),
                    downtime_score=round(downtime_score, 2),
                    stage_delay_score=round(stage_delay_score, 2),
                    infrastructure_zone_impact_score=round(infrastructure_zone_impact_score, 2),
                    needed_by_urgency_score=round(needed_by_urgency_score, 2),
                    repeat_failure_score=round(repeat_failure_score, 2),
                    spare_risk_score=round(spare_risk_score, 2),
                    capacity_risk_score=round(capacity_risk_score, 2),
                    redundancy_risk_score=round(redundancy_risk_score, 2),
                    thermal_risk_score=round(thermal_risk_score, 2),
                    vendor_eta_risk_score=round(vendor_eta_risk_score, 2),
                    mitigation_credit_score=round(mitigation_credit_score, 2),
                    total_priority_score=round(total, 2),
                    recommended_action=_recommended_action(request, work_orders_by_request, part_by_id, impact),
                    reason_summary=_reason_summary(request, current, asset, zone, impact),
                ),
            )
        )

    ranked = []
    for rank, (_, row) in enumerate(sorted(scored_rows, key=lambda item: item[0], reverse=True), start=1):
        row.priority_rank = rank
        ranked.append(row)
    return ranked


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


def _work_orders_by_request(
    work_orders: list[FacilityWorkOrder],
) -> dict[str, list[FacilityWorkOrder]]:
    grouped: dict[str, list[FacilityWorkOrder]] = defaultdict(list)
    for work_order in work_orders:
        grouped[work_order.incident_id].append(work_order)
    return grouped


def _latest_impact_by_request(
    snapshots: list[InfrastructureImpactSnapshot],
) -> dict[str, InfrastructureImpactSnapshot]:
    latest: dict[str, InfrastructureImpactSnapshot] = {}
    for snapshot in snapshots:
        current = latest.get(snapshot.incident_id)
        if current is None or snapshot.snapshot_at > current.snapshot_at:
            latest[snapshot.incident_id] = snapshot
    return latest


def _repeat_failure_count_by_asset(requests: list[InfrastructureIncident]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for request in requests:
        counts[request.asset_id] += 1
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
        "INCIDENT_REPORTED": "MONITORING",
        "FACILITIES_TRIAGE": "FACILITIES_PLANNER",
        "ENGINEER_ASSIGNED": "FACILITIES_SUPERVISOR",
        "SPARE_VENDOR_WAITING": "SPARES_OR_VENDOR",
        "REPAIR_IN_PROGRESS": "FACILITIES_ENGINEER",
        "VALIDATION": "VALIDATION_ENGINEER",
        "RESTORED": "NONE",
    }.get(stage, "UNKNOWN")


def _next_owner_id(
    request: InfrastructureIncident,
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
) -> str | None:
    work_orders = work_orders_by_request.get(request.incident_id, [])
    if request.current_stage == "REPAIR_IN_PROGRESS":
        for work_order in work_orders:
            if work_order.assigned_engineer_id:
                return work_order.assigned_engineer_id
    if request.current_stage in {"ENGINEER_ASSIGNED", "SPARE_VENDOR_WAITING"} and work_orders:
        return work_orders[0].assigned_team
    return None


def _asset_criticality_score(level: str) -> float:
    return {
        "LOW": 5,
        "MEDIUM": 12,
        "HIGH": 22,
        "CRITICAL": 35,
    }.get(level, 0)


def _infrastructure_zone_impact_score(priority: str) -> float:
    return {
        "LOW": 4,
        "MEDIUM": 8,
        "HIGH": 16,
        "CRITICAL": 24,
    }.get(priority, 0)


def _needed_by_urgency_score(needed_by_at: datetime, as_of: datetime) -> float:
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


def _spare_risk_score(
    request: InfrastructureIncident,
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
    part_by_id: dict[str, CriticalSpare],
) -> float:
    score = 0.0
    for work_order in work_orders_by_request.get(request.incident_id, []):
        part = part_by_id.get(work_order.required_spare_id) if work_order.required_spare_id else None
        if work_order.work_order_status == "WAITING_SPARE_VENDOR":
            score = max(score, 14)
        if part and part.stock_status == "OUT_OF_STOCK":
            score = max(score, 18)
        elif part and part.stock_status == "LOW_STOCK":
            score = max(score, 10)
        if part and part.critical_spare:
            score += 4
    return min(score, 22)


def _capacity_risk_score(impact: InfrastructureImpactSnapshot | None) -> float:
    if impact is None:
        return 0
    gpu_score = min(float(impact.affected_gpu_count) / 10, 24)
    power_score = min(float(impact.estimated_capacity_risk_kw) / 100, 12)
    return min(gpu_score + power_score, 30)


def _redundancy_risk_score(impact: InfrastructureImpactSnapshot | None) -> float:
    if impact is None:
        return 0
    if impact.redundancy_state == "N-1":
        return 24
    if impact.power_redundancy_lost or impact.cooling_redundancy_lost:
        return 18
    if impact.redundancy_state == "N":
        return 12
    return 0


def _thermal_risk_score(impact: InfrastructureImpactSnapshot | None) -> float:
    if impact is None:
        return 0
    return min(float(impact.thermal_breach_minutes) / 6, 18)


def _vendor_eta_risk_score(impact: InfrastructureImpactSnapshot | None, as_of: datetime) -> float:
    if impact is None:
        return 0
    if impact.vendor_status == "ETA_MISSED":
        return 22
    if impact.vendor_eta_at and impact.vendor_eta_at < as_of and impact.vendor_status != "NOT_REQUIRED":
        return 18
    if impact.vendor_status == "WAITING_VENDOR_DISPATCH":
        return 14
    if impact.vendor_status == "ETA_CONFIRMED":
        return 6
    return 0


def _mitigation_credit_score(impact: InfrastructureImpactSnapshot | None) -> float:
    if impact is None:
        return 0
    return {
        "LOAD_SHIFTED": 8,
        "RUNNING_DEGRADED": 4,
        "VERIFIED_NORMAL": 2,
        "NONE": 0,
    }.get(impact.mitigation_status, 0)


def _recommended_action(
    request: InfrastructureIncident,
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
    part_by_id: dict[str, CriticalSpare],
    impact: InfrastructureImpactSnapshot | None = None,
) -> str:
    if request.current_stage == "FACILITIES_TRIAGE":
        return "Complete facilities triage and confirm owning team"
    if request.current_stage == "ENGINEER_ASSIGNED":
        return "Assign facilities engineer or rebalance team"
    if request.current_stage == "SPARE_VENDOR_WAITING":
        if impact and impact.vendor_status == "ETA_MISSED":
            return "Escalate missed vendor ETA and confirm recovery path"
        for work_order in work_orders_by_request.get(request.incident_id, []):
            part = part_by_id.get(work_order.required_spare_id) if work_order.required_spare_id else None
            if part and part.stock_status == "OUT_OF_STOCK":
                return "Expedite critical spare or vendor dispatch"
        return "Confirm spare availability or vendor ETA"
    if request.current_stage == "REPAIR_IN_PROGRESS":
        return "Unblock repair completion and confirm mitigation status"
    if request.current_stage == "VALIDATION":
        return "Prioritize restore validation"
    return "Review infrastructure incident status"


def _reason_summary(
    request: InfrastructureIncident,
    current: IncidentCurrentStatus,
    asset: InfrastructureAsset,
    zone: InfrastructureZone,
    impact: InfrastructureImpactSnapshot | None = None,
) -> str:
    impact_summary = _impact_rationale(impact)
    if current.is_delayed:
        return (
            f"{asset.criticality_level} asset in {zone.zone_name} is delayed in "
            f"{request.current_stage} for {float(current.hours_in_current_stage):.1f} hours."
            f"{impact_summary}"
        )
    return (
        f"{asset.criticality_level} infrastructure incident is in {request.current_stage} "
        f"and needed by {request.needed_by_at.isoformat()}."
        f"{impact_summary}"
    )


def _impact_rationale(impact: InfrastructureImpactSnapshot | None) -> str:
    if impact is None:
        return ""

    details: list[str] = []
    if impact.affected_gpu_count or impact.estimated_capacity_risk_kw:
        details.append(
            f"{impact.affected_gpu_count} affected GPUs and "
            f"{float(impact.estimated_capacity_risk_kw):.0f} kW at risk"
        )
    if impact.redundancy_state == "N-1" or impact.power_redundancy_lost or impact.cooling_redundancy_lost:
        details.append(f"{impact.redundancy_state} redundancy exposure")
    if impact.thermal_breach_minutes:
        details.append(f"{impact.thermal_breach_minutes} thermal breach minutes")
    if impact.vendor_status not in {"NOT_REQUIRED", "ETA_CONFIRMED"}:
        details.append(f"vendor status {impact.vendor_status}")
    if impact.mitigation_status != "NONE":
        details.append(f"mitigation {impact.mitigation_status}")

    if not details:
        return ""
    return f" Impact rationale: {'; '.join(details)}."
