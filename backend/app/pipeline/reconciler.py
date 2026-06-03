from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.analytics import IncidentCurrentStatus
from app.models.infrastructure import (
    ValidationResult,
    InfrastructureIncident,
    IncidentStageEvent,
    FacilityWorkOrder,
)
from app.models.ops import InfrastructureReconciliationIssue


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
    current_status_ids = {
        row[0]
        for row in session.execute(select(IncidentCurrentStatus.incident_id))
    }

    request_by_id = {request.incident_id: request for request in requests}
    events_by_request = _events_by_request(events)
    work_orders_by_request = _work_orders_by_request(work_orders)

    drafts: list[ReconciliationIssueDraft] = []
    drafts.extend(_request_stage_evidence_issues(requests, events_by_request))
    drafts.extend(_event_sequence_issues(requests, events_by_request))
    drafts.extend(_work_order_issues(request_by_id, work_orders_by_request))
    drafts.extend(_validation_issues(request_by_id, work_orders_by_request, validations))
    drafts.extend(_analytics_output_issues(requests, current_status_ids))

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
