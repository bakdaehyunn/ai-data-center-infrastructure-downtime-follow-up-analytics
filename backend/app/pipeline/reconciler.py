from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.analytics import IncidentCurrentStatus
from app.models.infrastructure import (
    ValidationResult,
    InfrastructureIncident,
    InfrastructureImpactSnapshot,
    IncidentStageEvent,
    FacilityWorkOrder,
)
from app.models.ops import InfrastructureReconciliationIssue
from app.sample_data.infrastructure_scenarios import INFRASTRUCTURE_EXIT_EVENT_BY_STAGE


IMPACT_MATERIAL_EVENT_TYPES = {
    "REDUNDANCY_LOST",
    "REDUNDANCY_RESTORED",
    "VENDOR_ETA_UPDATED",
    "VENDOR_ETA_MISSED",
    "LOAD_SHIFTED",
    "MITIGATION_APPLIED",
}
HIGH_IMPACT_MARKERS = {
    "CAPACITY",
    "COOLING",
    "GPU",
    "POWER",
    "REDUNDANCY",
}
IMPACT_RECONCILIATION_ISSUE_TYPES = {
    "impact_snapshot_missing_for_active_high_impact_incident",
    "impact_snapshot_stale_after_latest_impact_event",
    "impact_redundancy_event_snapshot_mismatch",
    "impact_vendor_eta_event_snapshot_mismatch",
    "impact_vendor_eta_past_not_missed",
    "impact_mitigation_without_event_evidence",
    "impact_thermal_context_missing_evidence",
    "impact_capacity_risk_zero_for_critical_gpu_incident",
}


@dataclass(frozen=True)
class ReconciliationResult:
    issues_created: int


@dataclass(frozen=True)
class ReconciliationIssueDraft:
    incident_id: str | None
    asset_id: str | None
    issue_type: str
    severity: str
    message: str
    evidence: dict[str, Any]


def run_reconciliation_checks(session: Session, pipeline_run_id: str) -> ReconciliationResult:
    session.execute(
        delete(InfrastructureReconciliationIssue).where(
            InfrastructureReconciliationIssue.pipeline_run_id == pipeline_run_id,
        )
    )

    requests = list(session.scalars(select(InfrastructureIncident)))
    events = list(session.scalars(select(IncidentStageEvent)))
    work_orders = list(session.scalars(select(FacilityWorkOrder)))
    validations = list(session.scalars(select(ValidationResult)))
    impact_snapshots = list(session.scalars(select(InfrastructureImpactSnapshot)))
    current_status_ids = {
        row[0]
        for row in session.execute(select(IncidentCurrentStatus.incident_id))
    }

    request_by_id = {request.incident_id: request for request in requests}
    events_by_request = _events_by_request(events)
    work_orders_by_request = _work_orders_by_request(work_orders)
    impact_by_request = _latest_impact_by_request(impact_snapshots)
    as_of = _default_as_of(events)

    drafts: list[ReconciliationIssueDraft] = []
    drafts.extend(_request_stage_evidence_issues(requests, events_by_request))
    drafts.extend(_event_sequence_issues(requests, events_by_request))
    drafts.extend(_work_order_issues(request_by_id, work_orders_by_request))
    drafts.extend(_validation_issues(request_by_id, work_orders_by_request, validations))
    drafts.extend(_analytics_output_issues(requests, current_status_ids))
    drafts.extend(_impact_context_issues(requests, events_by_request, impact_by_request, as_of))

    issues = [
        InfrastructureReconciliationIssue(
            issue_id=f"REC-{pipeline_run_id}-{index:03d}",
            pipeline_run_id=pipeline_run_id,
            incident_id=draft.incident_id,
            asset_id=draft.asset_id,
            issue_type=draft.issue_type,
            severity=draft.severity,
            status="OPEN",
            message=draft.message,
            evidence_json=draft.evidence,
        )
        for index, draft in enumerate(
            sorted(
                drafts,
                key=lambda item: (
                    item.incident_id or "",
                    item.issue_type,
                    item.severity,
                ),
            ),
            start=1,
        )
    ]
    session.add_all(issues)
    session.flush()

    return ReconciliationResult(issues_created=len(issues))


def _request_stage_evidence_issues(
    requests: list[InfrastructureIncident],
    events_by_request: dict[str, list[IncidentStageEvent]],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request in requests:
        request_events = events_by_request.get(request.incident_id, [])
        entered_stage_events = [event for event in request_events if event.event_type == "ENTERED_STAGE"]
        latest_entered_stage = entered_stage_events[-1].stage if entered_stage_events else None
        completed_events = [event for event in request_events if event.event_type == "INCIDENT_RESTORED"]

        if latest_entered_stage is None:
            issues.append(
                ReconciliationIssueDraft(
                    incident_id=request.incident_id,
                    asset_id=request.asset_id,
                    issue_type="state_reconstruction_missing_stage_event",
                    severity="ERROR",
                    message="The incident has no entered-stage event, so the current stage cannot be reconstructed from event history.",
                    evidence={
                        "current_stage": request.current_stage,
                        "current_status": request.current_status,
                    },
                )
            )
            continue

        if request.current_stage != latest_entered_stage:
            issues.append(
                ReconciliationIssueDraft(
                    incident_id=request.incident_id,
                    asset_id=request.asset_id,
                    issue_type="state_reconstruction_stage_mismatch",
                    severity="ERROR",
                    message="The core current stage does not match the latest entered-stage event.",
                    evidence={
                        "core_current_stage": request.current_stage,
                        "latest_entered_stage": latest_entered_stage,
                        "latest_entered_event_id": entered_stage_events[-1].event_id,
                    },
                )
            )

        if request.current_status == "RESTORED" and not completed_events:
            issues.append(
                ReconciliationIssueDraft(
                    incident_id=request.incident_id,
                    asset_id=request.asset_id,
                    issue_type="state_reconstruction_missing_completion_event",
                    severity="ERROR",
                    message="The incident is marked restored, but event history has no restore event.",
                    evidence={"current_status": request.current_status},
                )
            )

        if request.current_status != "RESTORED" and completed_events:
            issues.append(
                ReconciliationIssueDraft(
                    incident_id=request.incident_id,
                    asset_id=request.asset_id,
                    issue_type="state_reconstruction_active_with_completion_event",
                    severity="ERROR",
                    message="The incident is still active, but event history contains a restore event.",
                    evidence={
                        "current_status": request.current_status,
                        "completion_event_ids": [event.event_id for event in completed_events],
                    },
                )
            )

    return issues


def _event_sequence_issues(
    requests: list[InfrastructureIncident],
    events_by_request: dict[str, list[IncidentStageEvent]],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request in requests:
        out_of_order_events = [
            event
            for event in events_by_request.get(request.incident_id, [])
            if event.occurred_at < request.reported_at
        ]
        if not out_of_order_events:
            continue
        issues.append(
            ReconciliationIssueDraft(
                incident_id=request.incident_id,
                asset_id=request.asset_id,
                issue_type="event_sequence_before_request",
                severity="ERROR",
                message="A stage event occurred before the infrastructure request was reported.",
                evidence={
                    "reported_at": request.reported_at.isoformat(),
                    "event_ids": [event.event_id for event in out_of_order_events],
                },
            )
        )
    return issues


def _work_order_issues(
    request_by_id: dict[str, InfrastructureIncident],
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request_id, work_orders in work_orders_by_request.items():
        missing_part_work_orders = [
            work_order
            for work_order in work_orders
            if work_order.work_order_status == "WAITING_SPARE_VENDOR" and not work_order.required_spare_id
        ]
        if not missing_part_work_orders:
            continue
        request = request_by_id.get(request_id)
        issues.append(
            ReconciliationIssueDraft(
                incident_id=request_id,
                asset_id=request.asset_id if request else None,
                issue_type="spare_waiting_missing_required_spare",
                severity="ERROR",
                message="A work order is waiting on a spare or vendor, but no required spare is linked.",
                evidence={
                    "work_order_ids": [work_order.work_order_id for work_order in missing_part_work_orders],
                    "work_order_status": "WAITING_SPARE_VENDOR",
                },
            )
        )
    return issues


def _validation_issues(
    request_by_id: dict[str, InfrastructureIncident],
    work_orders_by_request: dict[str, list[FacilityWorkOrder]],
    validations: list[ValidationResult],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for validation in validations:
        completed_work_orders = [
            work_order
            for work_order in work_orders_by_request.get(validation.incident_id, [])
            if work_order.work_order_status in {"REPAIR_COMPLETED", "RESTORED"}
        ]
        if completed_work_orders:
            continue
        request = request_by_id.get(validation.incident_id)
        issues.append(
            ReconciliationIssueDraft(
                incident_id=validation.incident_id,
                asset_id=request.asset_id if request else None,
                issue_type="validation_without_completed_work",
                severity="ERROR",
                message="A validation result exists before any completed infrastructure work is available.",
                evidence={
                    "validation_id": validation.validation_id,
                    "validation_status": validation.validation_status,
                },
            )
        )
    return issues


def _analytics_output_issues(
    requests: list[InfrastructureIncident],
    current_status_ids: set[str],
) -> list[ReconciliationIssueDraft]:
    return [
        ReconciliationIssueDraft(
            incident_id=request.incident_id,
            asset_id=request.asset_id,
            issue_type="analytics_output_missing_current_status",
            severity="ERROR",
            message="Analytics did not produce a current-status row for a core infrastructure incident.",
            evidence={
                "current_stage": request.current_stage,
                "current_status": request.current_status,
            },
        )
        for request in requests
        if request.incident_id not in current_status_ids
    ]


def _impact_context_issues(
    requests: list[InfrastructureIncident],
    events_by_request: dict[str, list[IncidentStageEvent]],
    impact_by_request: dict[str, InfrastructureImpactSnapshot],
    as_of: datetime,
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request in requests:
        request_events = events_by_request.get(request.incident_id, [])
        impact = impact_by_request.get(request.incident_id)
        active = request.current_status != "RESTORED"
        high_impact = _is_high_impact_incident(request)

        if active and high_impact and impact is None:
            issues.append(
                ReconciliationIssueDraft(
                    incident_id=request.incident_id,
                    asset_id=request.asset_id,
                    issue_type="impact_snapshot_missing_for_active_high_impact_incident",
                    severity="ERROR",
                    message="The active high-impact incident has no impact snapshot, so capacity, redundancy, and vendor-risk context is unverified.",
                    evidence={
                        "priority_level": request.priority_level,
                        "business_impact": request.business_impact,
                        "current_stage": request.current_stage,
                    },
                )
            )
            continue
        if impact is None:
            continue

        issues.extend(_impact_snapshot_freshness_issues(request, request_events, impact))
        issues.extend(_impact_redundancy_issues(request, request_events, impact))
        issues.extend(_impact_vendor_issues(request, request_events, impact, as_of))
        issues.extend(_impact_mitigation_issues(request, request_events, impact))
        issues.extend(_impact_thermal_issues(request, impact))
        if active and high_impact and _impact_capacity_is_unexplained_zero(impact):
            issues.append(
                ReconciliationIssueDraft(
                    incident_id=request.incident_id,
                    asset_id=request.asset_id,
                    issue_type="impact_capacity_risk_zero_for_critical_gpu_incident",
                    severity="WARNING",
                    message="The incident is active and high impact, but the latest impact snapshot reports no affected GPU or capacity risk.",
                    evidence={
                        "priority_level": request.priority_level,
                        "business_impact": request.business_impact,
                        "affected_gpu_count": impact.affected_gpu_count,
                        "estimated_capacity_risk_kw": float(impact.estimated_capacity_risk_kw),
                        "mitigation_status": impact.mitigation_status,
                    },
                )
            )

    return issues


def _impact_snapshot_freshness_issues(
    request: InfrastructureIncident,
    events: list[IncidentStageEvent],
    impact: InfrastructureImpactSnapshot,
) -> list[ReconciliationIssueDraft]:
    if request.current_status == "RESTORED":
        return []
    latest_event = _latest_event_of_types(events, IMPACT_MATERIAL_EVENT_TYPES)
    if latest_event is None or latest_event.occurred_at <= impact.snapshot_at:
        return []
    return [
        ReconciliationIssueDraft(
            incident_id=request.incident_id,
            asset_id=request.asset_id,
            issue_type="impact_snapshot_stale_after_latest_impact_event",
            severity="WARNING",
            message="A material impact event occurred after the latest impact snapshot, so the displayed impact context may be stale.",
            evidence={
                "latest_snapshot_id": impact.impact_snapshot_id,
                "latest_snapshot_at": impact.snapshot_at.isoformat(),
                "latest_event_id": latest_event.event_id,
                "latest_event_type": latest_event.event_type,
                "latest_event_at": latest_event.occurred_at.isoformat(),
            },
        )
    ]


def _impact_redundancy_issues(
    request: InfrastructureIncident,
    events: list[IncidentStageEvent],
    impact: InfrastructureImpactSnapshot,
) -> list[ReconciliationIssueDraft]:
    latest_event = _latest_event_of_types(events, {"REDUNDANCY_LOST", "REDUNDANCY_RESTORED"})
    if latest_event is None:
        return []

    lost_in_snapshot = (
        impact.redundancy_state in {"N", "N-1"}
        or impact.power_redundancy_lost
        or impact.cooling_redundancy_lost
    )
    if latest_event.event_type == "REDUNDANCY_LOST" and not lost_in_snapshot:
        message = "Event history says redundancy was lost, but the latest impact snapshot still shows normal redundancy."
    elif latest_event.event_type == "REDUNDANCY_RESTORED" and lost_in_snapshot:
        message = "Event history says redundancy was restored, but the latest impact snapshot still shows redundancy loss."
    else:
        return []

    return [
        ReconciliationIssueDraft(
            incident_id=request.incident_id,
            asset_id=request.asset_id,
            issue_type="impact_redundancy_event_snapshot_mismatch",
            severity="ERROR",
            message=message,
            evidence={
                "latest_event_id": latest_event.event_id,
                "latest_event_type": latest_event.event_type,
                "redundancy_state": impact.redundancy_state,
                "power_redundancy_lost": impact.power_redundancy_lost,
                "cooling_redundancy_lost": impact.cooling_redundancy_lost,
            },
        )
    ]


def _impact_vendor_issues(
    request: InfrastructureIncident,
    events: list[IncidentStageEvent],
    impact: InfrastructureImpactSnapshot,
    as_of: datetime,
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    latest_vendor_event = _latest_event_of_types(events, {"VENDOR_ETA_UPDATED", "VENDOR_ETA_MISSED"})
    if latest_vendor_event and latest_vendor_event.event_type == "VENDOR_ETA_MISSED" and impact.vendor_status != "ETA_MISSED":
        issues.append(
            ReconciliationIssueDraft(
                incident_id=request.incident_id,
                asset_id=request.asset_id,
                issue_type="impact_vendor_eta_event_snapshot_mismatch",
                severity="ERROR",
                message="Event history says the vendor ETA was missed, but the latest impact snapshot does not mark the vendor status as missed.",
                evidence={
                    "latest_event_id": latest_vendor_event.event_id,
                    "latest_event_type": latest_vendor_event.event_type,
                    "vendor_status": impact.vendor_status,
                    "vendor_eta_at": impact.vendor_eta_at.isoformat() if impact.vendor_eta_at else None,
                },
            )
        )

    if (
        request.current_status != "RESTORED"
        and impact.vendor_eta_at
        and impact.vendor_eta_at < as_of
        and impact.vendor_status in {"WAITING_VENDOR_DISPATCH", "ETA_CONFIRMED"}
    ):
        issues.append(
            ReconciliationIssueDraft(
                incident_id=request.incident_id,
                asset_id=request.asset_id,
                issue_type="impact_vendor_eta_past_not_missed",
                severity="WARNING",
                message="The vendor ETA is older than the analytics as-of time, but the impact snapshot has not marked the ETA as missed.",
                evidence={
                    "vendor_status": impact.vendor_status,
                    "vendor_eta_at": impact.vendor_eta_at.isoformat(),
                    "analytics_as_of": as_of.isoformat(),
                },
            )
        )
    return issues


def _impact_mitigation_issues(
    request: InfrastructureIncident,
    events: list[IncidentStageEvent],
    impact: InfrastructureImpactSnapshot,
) -> list[ReconciliationIssueDraft]:
    expected_event_type = {
        "LOAD_SHIFTED": "LOAD_SHIFTED",
        "RUNNING_DEGRADED": "MITIGATION_APPLIED",
    }.get(impact.mitigation_status)
    if expected_event_type is None:
        return []
    matching_events = [
        event
        for event in events
        if event.event_type == expected_event_type and event.occurred_at <= impact.snapshot_at
    ]
    if matching_events:
        return []
    return [
        ReconciliationIssueDraft(
            incident_id=request.incident_id,
            asset_id=request.asset_id,
            issue_type="impact_mitigation_without_event_evidence",
            severity="WARNING",
            message="The impact snapshot reports mitigation, but event history has no matching mitigation evidence before the snapshot.",
            evidence={
                "mitigation_status": impact.mitigation_status,
                "expected_event_type": expected_event_type,
                "latest_snapshot_id": impact.impact_snapshot_id,
                "latest_snapshot_at": impact.snapshot_at.isoformat(),
            },
        )
    ]


def _impact_thermal_issues(
    request: InfrastructureIncident,
    impact: InfrastructureImpactSnapshot,
) -> list[ReconciliationIssueDraft]:
    if request.current_status == "RESTORED" or impact.thermal_breach_minutes <= 0:
        return []
    readings = impact.telemetry_readings_json or []
    has_abnormal_reading = any(
        str(reading.get("status", "")).upper() in {"WARNING", "CRITICAL"}
        for reading in readings
    )
    if has_abnormal_reading:
        return []
    return [
        ReconciliationIssueDraft(
            incident_id=request.incident_id,
            asset_id=request.asset_id,
            issue_type="impact_thermal_context_missing_evidence",
            severity="WARNING",
            message="The impact snapshot reports thermal breach minutes, but no warning or critical telemetry reading is attached.",
            evidence={
                "thermal_breach_minutes": impact.thermal_breach_minutes,
                "telemetry_reading_count": len(readings),
                "latest_snapshot_id": impact.impact_snapshot_id,
            },
        )
    ]


def _impact_capacity_is_unexplained_zero(impact: InfrastructureImpactSnapshot) -> bool:
    return (
        impact.affected_gpu_count == 0
        and float(impact.estimated_capacity_risk_kw) == 0
        and impact.mitigation_status not in {"LOAD_SHIFTED", "RUNNING_DEGRADED"}
    )


def _is_high_impact_incident(request: InfrastructureIncident) -> bool:
    if request.priority_level in {"CRITICAL", "HIGH"}:
        return True
    business_impact = request.business_impact.upper()
    return any(marker in business_impact for marker in HIGH_IMPACT_MARKERS)


def _latest_event_of_types(
    events: list[IncidentStageEvent],
    event_types: set[str],
) -> IncidentStageEvent | None:
    matching = [event for event in events if event.event_type in event_types]
    if not matching:
        return None
    return max(matching, key=lambda event: (event.occurred_at, event.event_id))


def _latest_impact_by_request(
    snapshots: list[InfrastructureImpactSnapshot],
) -> dict[str, InfrastructureImpactSnapshot]:
    latest: dict[str, InfrastructureImpactSnapshot] = {}
    for snapshot in sorted(
        snapshots,
        key=lambda item: (item.incident_id, item.snapshot_at, item.impact_snapshot_id),
        reverse=True,
    ):
        latest.setdefault(snapshot.incident_id, snapshot)
    return latest


def _default_as_of(events: list[IncidentStageEvent]) -> datetime:
    workflow_events = [
        event
        for event in events
        if event.event_type == "ENTERED_STAGE"
        or event.event_type == "INCIDENT_RESTORED"
        or event.event_type in INFRASTRUCTURE_EXIT_EVENT_BY_STAGE.values()
    ]
    event_basis = workflow_events or events
    if not event_basis:
        return datetime.utcnow()
    return max(event.occurred_at for event in event_basis) + timedelta(hours=24)


def _events_by_request(
    events: list[IncidentStageEvent],
) -> dict[str, list[IncidentStageEvent]]:
    grouped: dict[str, list[IncidentStageEvent]] = defaultdict(list)
    for event in events:
        grouped[event.incident_id].append(event)
    for request_events in grouped.values():
        request_events.sort(key=lambda event: (event.occurred_at, event.event_id))
    return grouped


def _work_orders_by_request(
    work_orders: list[FacilityWorkOrder],
) -> dict[str, list[FacilityWorkOrder]]:
    grouped: dict[str, list[FacilityWorkOrder]] = defaultdict(list)
    for work_order in work_orders:
        grouped[work_order.incident_id].append(work_order)
    return grouped
