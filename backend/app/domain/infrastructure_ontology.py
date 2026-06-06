from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol


INFRASTRUCTURE_SOURCE_SYSTEM = "sample_ai_data_center_infrastructure_system"

INFRASTRUCTURE_STAGE_FLOW = (
    "INCIDENT_REPORTED",
    "FACILITIES_TRIAGE",
    "ENGINEER_ASSIGNED",
    "SPARE_VENDOR_WAITING",
    "REPAIR_IN_PROGRESS",
    "VALIDATION",
    "RESTORED",
)
ACTIVE_INFRASTRUCTURE_STAGES = tuple(
    stage for stage in INFRASTRUCTURE_STAGE_FLOW if stage != "RESTORED"
)
INFRASTRUCTURE_STAGE_SET = frozenset(INFRASTRUCTURE_STAGE_FLOW)
ACTIVE_INFRASTRUCTURE_STAGE_SET = frozenset(ACTIVE_INFRASTRUCTURE_STAGES)

INFRASTRUCTURE_STAGE_THRESHOLDS_HOURS = {
    "INCIDENT_REPORTED": 2,
    "FACILITIES_TRIAGE": 8,
    "ENGINEER_ASSIGNED": 6,
    "SPARE_VENDOR_WAITING": 18,
    "REPAIR_IN_PROGRESS": 24,
    "VALIDATION": 8,
}

INFRASTRUCTURE_EXIT_EVENT_BY_STAGE = {
    "INCIDENT_REPORTED": "INCIDENT_ACCEPTED",
    "FACILITIES_TRIAGE": "TRIAGE_COMPLETED",
    "ENGINEER_ASSIGNED": "ENGINEER_ASSIGNED",
    "SPARE_VENDOR_WAITING": "SPARE_OR_VENDOR_READY",
    "REPAIR_IN_PROGRESS": "REPAIR_COMPLETED",
    "VALIDATION": "VALIDATION_PASSED",
}

WORKFLOW_EXIT_EVENT_TYPES = frozenset(INFRASTRUCTURE_EXIT_EVENT_BY_STAGE.values())
IMPACT_MATERIAL_EVENT_TYPES = frozenset(
    {
        "REDUNDANCY_LOST",
        "REDUNDANCY_RESTORED",
        "VENDOR_ETA_UPDATED",
        "VENDOR_ETA_MISSED",
        "LOAD_SHIFTED",
        "MITIGATION_APPLIED",
    }
)
SUPPLEMENTAL_WORKFLOW_EVENT_TYPES = frozenset(
    {
        "ENTERED_STAGE",
        "INCIDENT_RESTORED",
        "VALIDATION_FAILED",
    }
)
INFRASTRUCTURE_EVENT_TYPE_SET = (
    WORKFLOW_EXIT_EVENT_TYPES
    | IMPACT_MATERIAL_EVENT_TYPES
    | SUPPLEMENTAL_WORKFLOW_EVENT_TYPES
)

EVENT_STATUS_SET = frozenset({"SUCCESS", "ACTION_REQUIRED", "FAILED"})
PRIORITY_LEVEL_SET = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
INCIDENT_STATUS_SET = frozenset({"IN_PROGRESS", "RESTORED"})
TERMINAL_STAGE = "RESTORED"
TERMINAL_STATUS = "RESTORED"
ACTIVE_STATUS = "IN_PROGRESS"

INFRASTRUCTURE_OPERATIONAL_STATUS_SET = frozenset(
    {"RUNNING", "DEGRADED", "STOPPED", "LOCKED_OUT", "AT_RISK"}
)
ASSET_CRITICALITY_SET = PRIORITY_LEVEL_SET
ZONE_PRIORITY_SET = PRIORITY_LEVEL_SET
SPARE_STOCK_STATUS_SET = frozenset({"IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"})
WORK_ORDER_STATUS_SET = frozenset(
    {
        "ASSIGNED",
        "ASSIGNMENT_PENDING",
        "WAITING_SPARE_VENDOR",
        "IN_PROGRESS",
        "REPAIR_COMPLETED",
        "RESTORED",
    }
)
VALIDATION_STATUS_SET = frozenset({"PASSED", "PENDING", "FAILED"})
TELEMETRY_SEVERITY_SET = frozenset({"INFO", "WARNING", "CRITICAL"})
REDUNDANCY_STATE_SET = frozenset({"N+1", "N", "N-1"})
MITIGATION_STATUS_SET = frozenset(
    {"NONE", "LOAD_SHIFTED", "RUNNING_DEGRADED", "VERIFIED_NORMAL"}
)
VENDOR_STATUS_SET = frozenset(
    {"NOT_REQUIRED", "ETA_CONFIRMED", "WAITING_VENDOR_DISPATCH", "ETA_MISSED"}
)

HIGH_IMPACT_MARKERS = frozenset(
    {
        "CAPACITY",
        "COOLING",
        "GPU",
        "POWER",
        "REDUNDANCY",
    }
)

STATE_RECONCILIATION_ISSUE_TYPES = frozenset(
    {
        "state_reconstruction_missing_stage_event",
        "state_reconstruction_stage_mismatch",
        "state_reconstruction_missing_completion_event",
        "state_reconstruction_active_with_completion_event",
        "event_sequence_before_request",
        "spare_waiting_missing_required_spare",
        "validation_without_completed_work",
        "analytics_output_missing_current_status",
        "workflow_ontology_invalid_stage",
        "workflow_ontology_invalid_status",
        "workflow_ontology_invalid_priority",
        "workflow_ontology_invalid_event_type",
        "workflow_ontology_invalid_event_status",
        "workflow_ontology_invalid_stage_event_type",
        "workflow_ontology_invalid_stage_progression",
        "workflow_ontology_duplicate_stage_entry",
        "workflow_ontology_invalid_restored_state",
        "workflow_ontology_invalid_redundancy_state",
        "workflow_ontology_invalid_mitigation_status",
        "workflow_ontology_invalid_vendor_status",
        "workflow_ontology_invalid_zone_priority",
        "workflow_ontology_invalid_zone_status",
        "workflow_ontology_invalid_asset_criticality",
        "workflow_ontology_invalid_asset_status",
        "workflow_ontology_invalid_spare_stock_status",
        "workflow_ontology_invalid_work_order_status",
        "workflow_ontology_invalid_validation_status",
        "workflow_ontology_invalid_telemetry_severity",
    }
)

IMPACT_RECONCILIATION_ISSUE_TYPES = frozenset(
    {
        "impact_snapshot_missing_for_active_high_impact_incident",
        "impact_snapshot_stale_after_latest_impact_event",
        "impact_redundancy_event_snapshot_mismatch",
        "impact_vendor_eta_event_snapshot_mismatch",
        "impact_vendor_eta_past_not_missed",
        "impact_mitigation_without_event_evidence",
        "impact_thermal_context_missing_evidence",
        "impact_capacity_risk_zero_for_critical_gpu_incident",
    }
)

RECONCILIATION_ISSUE_TYPE_SET = (
    STATE_RECONCILIATION_ISSUE_TYPES | IMPACT_RECONCILIATION_ISSUE_TYPES
)

STAGE_INDEX = {stage: index for index, stage in enumerate(INFRASTRUCTURE_STAGE_FLOW)}


class IncidentLike(Protocol):
    incident_id: str
    asset_id: str
    priority_level: str
    current_stage: str
    current_status: str


class ZoneLike(Protocol):
    zone_id: str
    zone_priority: str
    current_status: str


class AssetLike(Protocol):
    asset_id: str
    criticality_level: str
    current_status: str


class SpareLike(Protocol):
    spare_id: str
    stock_status: str


class WorkOrderLike(Protocol):
    work_order_id: str
    incident_id: str
    work_order_status: str


class ValidationLike(Protocol):
    validation_id: str
    incident_id: str
    validation_status: str


class TelemetryAlertLike(Protocol):
    telemetry_alert_id: str
    linked_incident_id: str | None
    severity: str


class StageEventLike(Protocol):
    event_id: str
    incident_id: str
    stage: str
    event_type: str
    event_status: str
    occurred_at: Any


class ImpactSnapshotLike(Protocol):
    impact_snapshot_id: str
    incident_id: str
    redundancy_state: str
    mitigation_status: str
    vendor_status: str


@dataclass(frozen=True)
class OntologyIssue:
    incident_id: str | None
    asset_id: str | None
    issue_type: str
    severity: str
    message: str
    evidence: dict[str, Any]


def validate_incident_vocabulary(incidents: Iterable[IncidentLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for incident in incidents:
        if incident.current_stage not in INFRASTRUCTURE_STAGE_SET:
            issues.append(
                OntologyIssue(
                    incident_id=incident.incident_id,
                    asset_id=incident.asset_id,
                    issue_type="workflow_ontology_invalid_stage",
                    severity="ERROR",
                    message="The incident current stage is not part of the workflow ontology.",
                    evidence={"current_stage": incident.current_stage},
                )
            )
        if incident.current_status not in INCIDENT_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=incident.incident_id,
                    asset_id=incident.asset_id,
                    issue_type="workflow_ontology_invalid_status",
                    severity="ERROR",
                    message="The incident current status is not part of the workflow ontology.",
                    evidence={"current_status": incident.current_status},
                )
            )
        if incident.priority_level not in PRIORITY_LEVEL_SET:
            issues.append(
                OntologyIssue(
                    incident_id=incident.incident_id,
                    asset_id=incident.asset_id,
                    issue_type="workflow_ontology_invalid_priority",
                    severity="ERROR",
                    message="The incident priority level is not part of the workflow ontology.",
                    evidence={"priority_level": incident.priority_level},
                )
            )
    return issues


def validate_zone_vocabulary(zones: Iterable[ZoneLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for zone in zones:
        if zone.zone_priority not in ZONE_PRIORITY_SET:
            issues.append(
                OntologyIssue(
                    incident_id=None,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_zone_priority",
                    severity="ERROR",
                    message="The infrastructure zone priority is not part of the workflow ontology.",
                    evidence={"zone_id": zone.zone_id, "zone_priority": zone.zone_priority},
                )
            )
        if zone.current_status not in INFRASTRUCTURE_OPERATIONAL_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=None,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_zone_status",
                    severity="ERROR",
                    message="The infrastructure zone status is not part of the workflow ontology.",
                    evidence={"zone_id": zone.zone_id, "current_status": zone.current_status},
                )
            )
    return issues


def validate_asset_vocabulary(assets: Iterable[AssetLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for asset in assets:
        if asset.criticality_level not in ASSET_CRITICALITY_SET:
            issues.append(
                OntologyIssue(
                    incident_id=None,
                    asset_id=asset.asset_id,
                    issue_type="workflow_ontology_invalid_asset_criticality",
                    severity="ERROR",
                    message="The infrastructure asset criticality is not part of the workflow ontology.",
                    evidence={"asset_id": asset.asset_id, "criticality_level": asset.criticality_level},
                )
            )
        if asset.current_status not in INFRASTRUCTURE_OPERATIONAL_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=None,
                    asset_id=asset.asset_id,
                    issue_type="workflow_ontology_invalid_asset_status",
                    severity="ERROR",
                    message="The infrastructure asset status is not part of the workflow ontology.",
                    evidence={"asset_id": asset.asset_id, "current_status": asset.current_status},
                )
            )
    return issues


def validate_spare_vocabulary(spares: Iterable[SpareLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for spare in spares:
        if spare.stock_status not in SPARE_STOCK_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=None,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_spare_stock_status",
                    severity="ERROR",
                    message="The critical spare stock status is not part of the workflow ontology.",
                    evidence={"spare_id": spare.spare_id, "stock_status": spare.stock_status},
                )
            )
    return issues


def validate_work_order_vocabulary(work_orders: Iterable[WorkOrderLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for work_order in work_orders:
        if work_order.work_order_status not in WORK_ORDER_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=work_order.incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_work_order_status",
                    severity="ERROR",
                    message="The facility work order status is not part of the workflow ontology.",
                    evidence={
                        "work_order_id": work_order.work_order_id,
                        "work_order_status": work_order.work_order_status,
                    },
                )
            )
    return issues


def validate_validation_vocabulary(validations: Iterable[ValidationLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for validation in validations:
        if validation.validation_status not in VALIDATION_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=validation.incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_validation_status",
                    severity="ERROR",
                    message="The validation status is not part of the workflow ontology.",
                    evidence={
                        "validation_id": validation.validation_id,
                        "validation_status": validation.validation_status,
                    },
                )
            )
    return issues


def validate_telemetry_vocabulary(alerts: Iterable[TelemetryAlertLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for alert in alerts:
        if alert.severity not in TELEMETRY_SEVERITY_SET:
            issues.append(
                OntologyIssue(
                    incident_id=alert.linked_incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_telemetry_severity",
                    severity="ERROR",
                    message="The telemetry alert severity is not part of the workflow ontology.",
                    evidence={
                        "telemetry_alert_id": alert.telemetry_alert_id,
                        "severity": alert.severity,
                    },
                )
            )
    return issues


def validate_event_vocabulary(events: Iterable[StageEventLike]) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for event in events:
        if event.stage not in INFRASTRUCTURE_STAGE_SET:
            issues.append(
                OntologyIssue(
                    incident_id=event.incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_stage",
                    severity="ERROR",
                    message="A stage event uses a stage that is not part of the workflow ontology.",
                    evidence={"event_id": event.event_id, "stage": event.stage},
                )
            )
        if event.event_type not in INFRASTRUCTURE_EVENT_TYPE_SET:
            issues.append(
                OntologyIssue(
                    incident_id=event.incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_event_type",
                    severity="ERROR",
                    message="A stage event uses an event type that is not part of the workflow ontology.",
                    evidence={"event_id": event.event_id, "event_type": event.event_type},
                )
            )
        if event.event_status not in EVENT_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=event.incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_event_status",
                    severity="ERROR",
                    message="A stage event uses an event status that is not part of the workflow ontology.",
                    evidence={"event_id": event.event_id, "event_status": event.event_status},
                )
            )
    return issues


def validate_impact_vocabulary(
    snapshots: Iterable[ImpactSnapshotLike],
    incident_asset_by_id: dict[str, str] | None = None,
) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    incident_asset_by_id = incident_asset_by_id or {}
    for snapshot in snapshots:
        asset_id = incident_asset_by_id.get(snapshot.incident_id)
        if snapshot.redundancy_state not in REDUNDANCY_STATE_SET:
            issues.append(
                OntologyIssue(
                    incident_id=snapshot.incident_id,
                    asset_id=asset_id,
                    issue_type="workflow_ontology_invalid_redundancy_state",
                    severity="ERROR",
                    message="The impact snapshot redundancy state is not part of the workflow ontology.",
                    evidence={
                        "impact_snapshot_id": snapshot.impact_snapshot_id,
                        "redundancy_state": snapshot.redundancy_state,
                    },
                )
            )
        if snapshot.mitigation_status not in MITIGATION_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=snapshot.incident_id,
                    asset_id=asset_id,
                    issue_type="workflow_ontology_invalid_mitigation_status",
                    severity="ERROR",
                    message="The impact snapshot mitigation status is not part of the workflow ontology.",
                    evidence={
                        "impact_snapshot_id": snapshot.impact_snapshot_id,
                        "mitigation_status": snapshot.mitigation_status,
                    },
                )
            )
        if snapshot.vendor_status not in VENDOR_STATUS_SET:
            issues.append(
                OntologyIssue(
                    incident_id=snapshot.incident_id,
                    asset_id=asset_id,
                    issue_type="workflow_ontology_invalid_vendor_status",
                    severity="ERROR",
                    message="The impact snapshot vendor status is not part of the workflow ontology.",
                    evidence={
                        "impact_snapshot_id": snapshot.impact_snapshot_id,
                        "vendor_status": snapshot.vendor_status,
                    },
                )
            )
    return issues


def validate_stage_event_transitions(
    events_by_incident: dict[str, list[StageEventLike]],
    incidents_by_id: dict[str, IncidentLike] | None = None,
) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    incidents_by_id = incidents_by_id or {}
    for incident_id, events in events_by_incident.items():
        known_events = sorted(
            [event for event in events if event.stage in INFRASTRUCTURE_STAGE_SET],
            key=lambda event: (event.occurred_at, event.event_id),
        )
        if not known_events:
            continue
        issues.extend(_invalid_stage_event_type_issues(incident_id, known_events))
        entered_events = [event for event in known_events if event.event_type == "ENTERED_STAGE"]
        issues.extend(_duplicate_stage_entry_issues(incident_id, entered_events))
        issues.extend(_invalid_stage_progression_issues(incident_id, entered_events))

        incident = incidents_by_id.get(incident_id)
        restored_events = [event for event in known_events if event.event_type == "INCIDENT_RESTORED"]
        if incident is not None:
            issues.extend(_invalid_restored_state_issues(incident, entered_events, restored_events))
    return issues


def _invalid_stage_event_type_issues(
    incident_id: str,
    events: list[StageEventLike],
) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for event in events:
        if event.event_type not in INFRASTRUCTURE_EVENT_TYPE_SET:
            continue
        expected_exit = INFRASTRUCTURE_EXIT_EVENT_BY_STAGE.get(event.stage)
        allowed = {"ENTERED_STAGE", "INCIDENT_RESTORED"} | IMPACT_MATERIAL_EVENT_TYPES
        if event.stage == "VALIDATION":
            allowed.add("VALIDATION_FAILED")
        if expected_exit:
            allowed.add(expected_exit)
        if event.event_type not in allowed:
            issues.append(
                OntologyIssue(
                    incident_id=incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_stage_event_type",
                    severity="ERROR",
                    message="A stage event type is not allowed for the event stage.",
                    evidence={
                        "event_id": event.event_id,
                        "stage": event.stage,
                        "event_type": event.event_type,
                        "allowed_event_types": sorted(allowed),
                    },
                )
            )
    return issues


def _duplicate_stage_entry_issues(
    incident_id: str,
    entered_events: list[StageEventLike],
) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    stage_entry_ids: dict[str, list[str]] = {}
    for event in entered_events:
        stage_entry_ids.setdefault(event.stage, []).append(event.event_id)
    for stage, event_ids in sorted(stage_entry_ids.items()):
        if len(event_ids) <= 1:
            continue
        issues.append(
            OntologyIssue(
                incident_id=incident_id,
                asset_id=None,
                issue_type="workflow_ontology_duplicate_stage_entry",
                severity="ERROR",
                message="An incident has duplicate entered-stage evidence for a workflow stage.",
                evidence={"stage": stage, "event_ids": event_ids},
            )
        )
    return issues


def _invalid_stage_progression_issues(
    incident_id: str,
    entered_events: list[StageEventLike],
) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    if not entered_events:
        return issues
    entered_stage_indexes = [
        STAGE_INDEX[event.stage]
        for event in entered_events
        if event.stage in STAGE_INDEX
    ]
    if not entered_stage_indexes:
        return issues
    if entered_stage_indexes[0] != 0:
        issues.append(
            OntologyIssue(
                incident_id=incident_id,
                asset_id=None,
                issue_type="workflow_ontology_invalid_stage_progression",
                severity="ERROR",
                message="The incident did not enter the workflow through INCIDENT_REPORTED.",
                evidence={"first_entered_stage": entered_events[0].stage},
            )
        )
    for previous, current in zip(entered_events, entered_events[1:]):
        if previous.stage not in STAGE_INDEX or current.stage not in STAGE_INDEX:
            continue
        previous_index = STAGE_INDEX[previous.stage]
        current_index = STAGE_INDEX[current.stage]
        if current_index != previous_index + 1:
            issues.append(
                OntologyIssue(
                    incident_id=incident_id,
                    asset_id=None,
                    issue_type="workflow_ontology_invalid_stage_progression",
                    severity="ERROR",
                    message="The incident entered workflow stages out of order or skipped a required stage.",
                    evidence={
                        "previous_event_id": previous.event_id,
                        "previous_stage": previous.stage,
                        "current_event_id": current.event_id,
                        "current_stage": current.stage,
                    },
                )
            )
    return issues


def _invalid_restored_state_issues(
    incident: IncidentLike,
    entered_events: list[StageEventLike],
    restored_events: list[StageEventLike],
) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    entered_stages = {event.stage for event in entered_events}
    if incident.current_status != TERMINAL_STATUS and TERMINAL_STAGE in entered_stages:
        issues.append(
            OntologyIssue(
                incident_id=incident.incident_id,
                asset_id=incident.asset_id,
                issue_type="workflow_ontology_invalid_restored_state",
                severity="ERROR",
                message="The incident is active but event history entered the terminal RESTORED stage.",
                evidence={
                    "current_status": incident.current_status,
                    "restored_entered_event_ids": [
                        event.event_id for event in entered_events if event.stage == TERMINAL_STAGE
                    ],
                },
            )
        )
    if (
        incident.current_status == TERMINAL_STATUS
        and TERMINAL_STAGE not in entered_stages
        and not restored_events
    ):
        issues.append(
            OntologyIssue(
                incident_id=incident.incident_id,
                asset_id=incident.asset_id,
                issue_type="workflow_ontology_invalid_restored_state",
                severity="ERROR",
                message="The incident is restored but has no terminal restore evidence.",
                evidence={
                    "current_status": incident.current_status,
                    "entered_stages": sorted(entered_stages),
                    "restored_event_count": len(restored_events),
                },
            )
        )
    return issues
