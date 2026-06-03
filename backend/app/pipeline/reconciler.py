from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.analytics import MaintenanceCurrentStatus
from app.models.maintenance import (
    InspectionResult,
    MaintenanceRequest,
    MaintenanceStageEvent,
    MaintenanceWorkOrder,
)
from app.models.ops import MaintenanceReconciliationIssue


@dataclass(frozen=True)
class ReconciliationResult:
    issues_created: int


@dataclass(frozen=True)
class ReconciliationIssueDraft:
    maintenance_request_id: str | None
    equipment_id: str | None
    issue_type: str
    severity: str
    message: str
    evidence: dict[str, Any]


def run_reconciliation_checks(session: Session, pipeline_run_id: str) -> ReconciliationResult:
    session.execute(
        delete(MaintenanceReconciliationIssue).where(
            MaintenanceReconciliationIssue.pipeline_run_id == pipeline_run_id,
        )
    )

    requests = list(session.scalars(select(MaintenanceRequest)))
    events = list(session.scalars(select(MaintenanceStageEvent)))
    work_orders = list(session.scalars(select(MaintenanceWorkOrder)))
    inspections = list(session.scalars(select(InspectionResult)))
    current_status_ids = {
        row[0]
        for row in session.execute(select(MaintenanceCurrentStatus.maintenance_request_id))
    }

    request_by_id = {request.maintenance_request_id: request for request in requests}
    events_by_request = _events_by_request(events)
    work_orders_by_request = _work_orders_by_request(work_orders)

    drafts: list[ReconciliationIssueDraft] = []
    drafts.extend(_request_stage_evidence_issues(requests, events_by_request))
    drafts.extend(_event_sequence_issues(requests, events_by_request))
    drafts.extend(_work_order_issues(request_by_id, work_orders_by_request))
    drafts.extend(_inspection_issues(request_by_id, work_orders_by_request, inspections))
    drafts.extend(_analytics_output_issues(requests, current_status_ids))

    issues = [
        MaintenanceReconciliationIssue(
            issue_id=f"REC-{pipeline_run_id}-{index:03d}",
            pipeline_run_id=pipeline_run_id,
            maintenance_request_id=draft.maintenance_request_id,
            equipment_id=draft.equipment_id,
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
                    item.maintenance_request_id or "",
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
    requests: list[MaintenanceRequest],
    events_by_request: dict[str, list[MaintenanceStageEvent]],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request in requests:
        request_events = events_by_request.get(request.maintenance_request_id, [])
        entered_stage_events = [event for event in request_events if event.event_type == "ENTERED_STAGE"]
        latest_entered_stage = entered_stage_events[-1].stage if entered_stage_events else None
        completed_events = [event for event in request_events if event.event_type == "REQUEST_COMPLETED"]

        if latest_entered_stage is None:
            issues.append(
                ReconciliationIssueDraft(
                    maintenance_request_id=request.maintenance_request_id,
                    equipment_id=request.equipment_id,
                    issue_type="state_reconstruction_missing_stage_event",
                    severity="ERROR",
                    message="The request has no entered-stage event, so the current stage cannot be reconstructed from event history.",
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
                    maintenance_request_id=request.maintenance_request_id,
                    equipment_id=request.equipment_id,
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

        if request.current_status == "COMPLETED" and not completed_events:
            issues.append(
                ReconciliationIssueDraft(
                    maintenance_request_id=request.maintenance_request_id,
                    equipment_id=request.equipment_id,
                    issue_type="state_reconstruction_missing_completion_event",
                    severity="ERROR",
                    message="The request is marked completed, but event history has no completion event.",
                    evidence={"current_status": request.current_status},
                )
            )

        if request.current_status != "COMPLETED" and completed_events:
            issues.append(
                ReconciliationIssueDraft(
                    maintenance_request_id=request.maintenance_request_id,
                    equipment_id=request.equipment_id,
                    issue_type="state_reconstruction_active_with_completion_event",
                    severity="ERROR",
                    message="The request is still active, but event history contains a completion event.",
                    evidence={
                        "current_status": request.current_status,
                        "completion_event_ids": [event.event_id for event in completed_events],
                    },
                )
            )

    return issues


def _event_sequence_issues(
    requests: list[MaintenanceRequest],
    events_by_request: dict[str, list[MaintenanceStageEvent]],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request in requests:
        out_of_order_events = [
            event
            for event in events_by_request.get(request.maintenance_request_id, [])
            if event.occurred_at < request.reported_at
        ]
        if not out_of_order_events:
            continue
        issues.append(
            ReconciliationIssueDraft(
                maintenance_request_id=request.maintenance_request_id,
                equipment_id=request.equipment_id,
                issue_type="event_sequence_before_request",
                severity="ERROR",
                message="A stage event occurred before the maintenance request was reported.",
                evidence={
                    "reported_at": request.reported_at.isoformat(),
                    "event_ids": [event.event_id for event in out_of_order_events],
                },
            )
        )
    return issues


def _work_order_issues(
    request_by_id: dict[str, MaintenanceRequest],
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for request_id, work_orders in work_orders_by_request.items():
        missing_part_work_orders = [
            work_order
            for work_order in work_orders
            if work_order.work_order_status == "WAITING_PARTS" and not work_order.required_part_id
        ]
        if not missing_part_work_orders:
            continue
        request = request_by_id.get(request_id)
        issues.append(
            ReconciliationIssueDraft(
                maintenance_request_id=request_id,
                equipment_id=request.equipment_id if request else None,
                issue_type="parts_waiting_missing_required_part",
                severity="ERROR",
                message="A work order is waiting for parts, but no required part is linked.",
                evidence={
                    "work_order_ids": [work_order.work_order_id for work_order in missing_part_work_orders],
                    "work_order_status": "WAITING_PARTS",
                },
            )
        )
    return issues


def _inspection_issues(
    request_by_id: dict[str, MaintenanceRequest],
    work_orders_by_request: dict[str, list[MaintenanceWorkOrder]],
    inspections: list[InspectionResult],
) -> list[ReconciliationIssueDraft]:
    issues: list[ReconciliationIssueDraft] = []
    for inspection in inspections:
        completed_work_orders = [
            work_order
            for work_order in work_orders_by_request.get(inspection.maintenance_request_id, [])
            if work_order.work_order_status in {"WORK_COMPLETED", "COMPLETED"}
        ]
        if completed_work_orders:
            continue
        request = request_by_id.get(inspection.maintenance_request_id)
        issues.append(
            ReconciliationIssueDraft(
                maintenance_request_id=inspection.maintenance_request_id,
                equipment_id=request.equipment_id if request else None,
                issue_type="inspection_without_completed_work",
                severity="ERROR",
                message="An inspection result exists before any completed maintenance work is available.",
                evidence={
                    "inspection_id": inspection.inspection_id,
                    "inspection_status": inspection.inspection_status,
                },
            )
        )
    return issues


def _analytics_output_issues(
    requests: list[MaintenanceRequest],
    current_status_ids: set[str],
) -> list[ReconciliationIssueDraft]:
    return [
        ReconciliationIssueDraft(
            maintenance_request_id=request.maintenance_request_id,
            equipment_id=request.equipment_id,
            issue_type="analytics_output_missing_current_status",
            severity="ERROR",
            message="Analytics did not produce a current-status row for a core maintenance request.",
            evidence={
                "current_stage": request.current_stage,
                "current_status": request.current_status,
            },
        )
        for request in requests
        if request.maintenance_request_id not in current_status_ids
    ]


def _events_by_request(
    events: list[MaintenanceStageEvent],
) -> dict[str, list[MaintenanceStageEvent]]:
    grouped: dict[str, list[MaintenanceStageEvent]] = defaultdict(list)
    for event in events:
        grouped[event.maintenance_request_id].append(event)
    for request_events in grouped.values():
        request_events.sort(key=lambda event: (event.occurred_at, event.event_id))
    return grouped


def _work_orders_by_request(
    work_orders: list[MaintenanceWorkOrder],
) -> dict[str, list[MaintenanceWorkOrder]]:
    grouped: dict[str, list[MaintenanceWorkOrder]] = defaultdict(list)
    for work_order in work_orders:
        grouped[work_order.maintenance_request_id].append(work_order)
    return grouped
