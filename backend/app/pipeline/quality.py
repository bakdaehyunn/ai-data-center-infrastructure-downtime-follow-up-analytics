from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.infrastructure_ontology import (
    TERMINAL_STATUS,
    validate_asset_vocabulary,
    validate_dependency_vocabulary,
    validate_event_vocabulary,
    validate_impact_vocabulary,
    validate_incident_vocabulary,
    validate_spare_vocabulary,
    validate_stage_event_transitions,
    validate_telemetry_vocabulary,
    validate_validation_vocabulary,
    validate_work_order_vocabulary,
    validate_zone_vocabulary,
)
from app.models.infrastructure import (
    CriticalSpare,
    InfrastructureImpactSnapshot,
    InfrastructureAsset,
    InfrastructureDependency,
    InfrastructureZone,
    ValidationResult,
    InfrastructureIncident,
    IncidentStageEvent,
    FacilityWorkOrder,
    TelemetryAlert,
)
from app.models.ops import DataQualityCheckResult
from app.pipeline.raw_loader import RAW_SOURCE_SPECS
from app.sample_data.infrastructure_scenarios import INFRASTRUCTURE_SOURCE_SYSTEM


REQUIRED_PAYLOAD_FIELDS = {
    "raw_infrastructure_incidents": {
        "incident_id",
        "request_number",
        "asset_id",
        "zone_id",
        "request_title",
        "request_type",
        "priority_level",
        "failure_mode",
        "reported_at",
        "needed_by_at",
        "current_stage",
        "current_status",
        "business_impact",
        "estimated_downtime_hours",
    },
    "raw_incident_stage_events": {
        "event_id",
        "incident_id",
        "stage",
        "event_type",
        "event_status",
        "occurred_at",
        "actor_type",
        "source_system",
    },
    "raw_facility_work_orders": {
        "work_order_id",
        "incident_id",
        "assigned_team",
        "work_order_status",
    },
    "raw_validation_results": {
        "validation_id",
        "incident_id",
        "validation_status",
    },
    "raw_telemetry_alerts": {
        "telemetry_alert_id",
        "asset_id",
        "alert_type",
        "severity",
        "triggered_at",
    },
}

DATE_FIELDS = {
    "raw_infrastructure_incidents": ["reported_at", "needed_by_at"],
    "raw_incident_stage_events": ["occurred_at"],
    "raw_facility_work_orders": ["planned_start_at", "actual_start_at", "actual_completed_at"],
    "raw_validation_results": ["validation_started_at", "validation_completed_at"],
    "raw_telemetry_alerts": ["triggered_at", "resolved_at"],
}


@dataclass(frozen=True)
class QualityCheck:
    check_name: str
    target_table: str
    severity: str
    failed_keys: list[str]
    message: str

    @property
    def status(self) -> str:
        return "PASS" if not self.failed_keys else "FAILED"


def run_raw_quality_checks(
    records_by_table: dict[str, list[dict[str, Any]]],
    pipeline_run_id: str,
    start_index: int = 1,
) -> list[DataQualityCheckResult]:
    checks: list[QualityCheck] = []
    for spec in RAW_SOURCE_SPECS:
        records = records_by_table[spec.target_table]
        checks.extend(
            [
                _check_unknown_source_system(spec.target_table, records),
                _check_duplicate_source_record(spec.target_table, records),
                _check_missing_required_fields(spec.target_table, records),
                _check_invalid_date_format(spec.target_table, records),
            ]
        )

    checks.extend(_check_missing_source_references(records_by_table))
    return _quality_results_to_models(checks, pipeline_run_id, start_index)


def run_core_quality_checks(
    session: Session,
    pipeline_run_id: str,
    start_index: int = 1,
) -> list[DataQualityCheckResult]:
    checks = [
        _check_request_without_stage_event(session),
        _check_event_timestamp_out_of_order(session),
        _check_incident_vocabulary(session),
        _check_stage_event_vocabulary(session),
        _check_impact_vocabulary(session),
        _check_stage_event_transition_rules(session),
        _check_zone_vocabulary(session),
        _check_asset_vocabulary(session),
        _check_dependency_vocabulary(session),
        _check_spare_vocabulary(session),
        _check_work_order_vocabulary(session),
        _check_validation_vocabulary(session),
        _check_telemetry_vocabulary(session),
        _check_work_order_without_request(session),
        _check_validation_without_completed_work(session),
        _check_spare_waiting_without_required_spare(session),
        _check_telemetry_alert_without_known_asset(session),
    ]
    return _quality_results_to_models(checks, pipeline_run_id, start_index)


def _check_unknown_source_system(target_table: str, records: list[dict[str, Any]]) -> QualityCheck:
    failed = [
        _record_key(record)
        for record in records
        if record.get("source_system") != INFRASTRUCTURE_SOURCE_SYSTEM
    ]
    return QualityCheck(
        check_name="unknown_source_system",
        target_table=target_table,
        severity="ERROR",
        failed_keys=failed,
        message="Source system must match the expected infrastructure sample source.",
    )


def _check_duplicate_source_record(target_table: str, records: list[dict[str, Any]]) -> QualityCheck:
    seen: set[tuple[Any, Any]] = set()
    failed: list[str] = []

    for record in records:
        key = (record.get("source_system"), record.get("source_record_id"))
        if key in seen:
            failed.append(_record_key(record))
        else:
            seen.add(key)

    return QualityCheck(
        check_name="duplicate_source_record",
        target_table=target_table,
        severity="ERROR",
        failed_keys=failed,
        message="Duplicate source records are rejected before raw insertion.",
    )


def _check_missing_required_fields(target_table: str, records: list[dict[str, Any]]) -> QualityCheck:
    required_fields = REQUIRED_PAYLOAD_FIELDS[target_table]
    failed: list[str] = []

    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            failed.append(_record_key(record))
            continue
        missing_fields = [
            field
            for field in required_fields
            if payload.get(field) in (None, "")
        ]
        if missing_fields:
            failed.append(f"{_record_key(record)} missing={','.join(sorted(missing_fields))}")

    return QualityCheck(
        check_name="missing_required_fields",
        target_table=target_table,
        severity="ERROR",
        failed_keys=failed,
        message="Required payload fields must exist before core transformation.",
    )


def _check_invalid_date_format(target_table: str, records: list[dict[str, Any]]) -> QualityCheck:
    failed: list[str] = []

    for record in records:
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        for field in DATE_FIELDS[target_table]:
            value = payload.get(field)
            if value in (None, ""):
                continue
            if not _is_valid_iso_datetime_or_date(str(value)):
                failed.append(f"{_record_key(record)} field={field}")

    return QualityCheck(
        check_name="invalid_date_format",
        target_table=target_table,
        severity="ERROR",
        failed_keys=failed,
        message="Date and timestamp fields must be ISO formatted.",
    )


def _check_missing_source_references(
    records_by_table: dict[str, list[dict[str, Any]]],
) -> list[QualityCheck]:
    request_ids = _payload_id_set(records_by_table["raw_infrastructure_incidents"], "incident_id")

    event_missing_request = [
        _record_key(record)
        for record in records_by_table["raw_incident_stage_events"]
        if _payload_value(record, "incident_id") not in request_ids
    ]
    work_order_missing_request = [
        _record_key(record)
        for record in records_by_table["raw_facility_work_orders"]
        if _payload_value(record, "incident_id") not in request_ids
    ]
    validation_missing_request = [
        _record_key(record)
        for record in records_by_table["raw_validation_results"]
        if _payload_value(record, "incident_id") not in request_ids
    ]
    alert_missing_request = [
        _record_key(record)
        for record in records_by_table["raw_telemetry_alerts"]
        if _payload_value(record, "linked_incident_id") not in (None, "", *request_ids)
    ]

    return [
        QualityCheck(
            check_name="missing_infrastructure_request_reference",
            target_table="raw_incident_stage_events",
            severity="ERROR",
            failed_keys=event_missing_request,
            message="Infrastructure stage event source records must reference an existing source infrastructure request.",
        ),
        QualityCheck(
            check_name="missing_infrastructure_request_reference",
            target_table="raw_facility_work_orders",
            severity="ERROR",
            failed_keys=work_order_missing_request,
            message="Infrastructure work order source records must reference an existing source infrastructure request.",
        ),
        QualityCheck(
            check_name="missing_infrastructure_request_reference",
            target_table="raw_validation_results",
            severity="ERROR",
            failed_keys=validation_missing_request,
            message="Validation source records must reference an existing source infrastructure request.",
        ),
        QualityCheck(
            check_name="missing_infrastructure_request_reference",
            target_table="raw_telemetry_alerts",
            severity="ERROR",
            failed_keys=alert_missing_request,
            message="Linked telemetry alerts must reference an existing source infrastructure incident when populated.",
        ),
    ]


def _payload_id_set(records: list[dict[str, Any]], field_name: str) -> set[Any]:
    return {
        _payload_value(record, field_name)
        for record in records
        if _payload_value(record, field_name) not in (None, "")
    }


def _payload_value(record: dict[str, Any], field_name: str) -> Any:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    return payload.get(field_name)


def _record_key(record: dict[str, Any]) -> str:
    return f"{record.get('source_system')}:{record.get('source_record_id')}"


def _is_valid_iso_datetime_or_date(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _check_request_without_stage_event(session: Session) -> QualityCheck:
    request_ids_with_events = {
        row[0]
        for row in session.execute(select(IncidentStageEvent.incident_id).distinct())
    }
    failed = [
        request.incident_id
        for request in session.scalars(select(InfrastructureIncident))
        if request.incident_id not in request_ids_with_events
    ]
    return QualityCheck(
        check_name="infrastructure_incident_without_stage_event",
        target_table="infrastructure_incidents",
        severity="ERROR",
        failed_keys=failed,
        message="Every core infrastructure incident should have at least one stage event.",
    )


def _check_event_timestamp_out_of_order(session: Session) -> QualityCheck:
    requests = {
        request.incident_id: request
        for request in session.scalars(select(InfrastructureIncident))
    }
    failed = []
    for event in session.scalars(select(IncidentStageEvent)):
        request = requests.get(event.incident_id)
        if request and event.occurred_at < request.reported_at:
            failed.append(event.event_id)

    return QualityCheck(
        check_name="stage_event_timestamp_out_of_order",
        target_table="incident_stage_events",
        severity="ERROR",
        failed_keys=failed,
        message="Infrastructure stage event timestamps should not occur before request reporting.",
    )


def _check_work_order_without_request(session: Session) -> QualityCheck:
    request_ids = {
        row[0]
        for row in session.execute(select(InfrastructureIncident.incident_id))
    }
    failed = [
        work_order.work_order_id
        for work_order in session.scalars(select(FacilityWorkOrder))
        if work_order.incident_id not in request_ids
    ]
    return QualityCheck(
        check_name="work_order_without_request",
        target_table="facility_work_orders",
        severity="CRITICAL",
        failed_keys=failed,
        message="Every infrastructure work order should reference an existing core infrastructure request.",
    )


def _check_validation_without_completed_work(session: Session) -> QualityCheck:
    completed_work_request_ids = {
        row[0]
        for row in session.execute(
            select(FacilityWorkOrder.incident_id).where(
                FacilityWorkOrder.work_order_status.in_(["REPAIR_COMPLETED", TERMINAL_STATUS]),
            )
        )
    }
    failed = [
        validation.validation_id
        for validation in session.scalars(select(ValidationResult))
        if validation.incident_id not in completed_work_request_ids
    ]
    return QualityCheck(
        check_name="validation_without_completed_work",
        target_table="validation_results",
        severity="ERROR",
        failed_keys=failed,
        message="Validation records should only exist after infrastructure work is completed.",
    )


def _check_spare_waiting_without_required_spare(session: Session) -> QualityCheck:
    failed = [
        work_order.work_order_id
        for work_order in session.scalars(select(FacilityWorkOrder))
        if work_order.work_order_status == "WAITING_SPARE_VENDOR" and not work_order.required_spare_id
    ]
    return QualityCheck(
        check_name="spare_waiting_without_required_spare",
        target_table="facility_work_orders",
        severity="ERROR",
        failed_keys=failed,
        message="Work orders waiting on a spare or vendor should identify the required spare when applicable.",
    )


def _check_incident_vocabulary(session: Session) -> QualityCheck:
    issues = validate_incident_vocabulary(session.scalars(select(InfrastructureIncident)))
    return QualityCheck(
        check_name="workflow_ontology_incident_vocabulary",
        target_table="infrastructure_incidents",
        severity="ERROR",
        failed_keys=[
            f"{issue.incident_id} {issue.issue_type}"
            for issue in issues
        ],
        message="Incident stage, status, and priority values must match the workflow ontology vocabulary.",
    )


def _check_stage_event_vocabulary(session: Session) -> QualityCheck:
    issues = validate_event_vocabulary(session.scalars(select(IncidentStageEvent)))
    return QualityCheck(
        check_name="workflow_ontology_stage_event_vocabulary",
        target_table="incident_stage_events",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('event_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Stage event stages, event types, and event statuses must match the workflow ontology vocabulary.",
    )


def _check_impact_vocabulary(session: Session) -> QualityCheck:
    incidents = {
        incident.incident_id: incident.asset_id
        for incident in session.scalars(select(InfrastructureIncident))
    }
    issues = validate_impact_vocabulary(
        session.scalars(select(InfrastructureImpactSnapshot)),
        incidents,
    )
    return QualityCheck(
        check_name="workflow_ontology_impact_vocabulary",
        target_table="infrastructure_impact_snapshots",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('impact_snapshot_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Impact redundancy, mitigation, and vendor states must match the workflow ontology vocabulary.",
    )


def _check_stage_event_transition_rules(session: Session) -> QualityCheck:
    incidents = {
        incident.incident_id: incident
        for incident in session.scalars(select(InfrastructureIncident))
    }
    events_by_incident: dict[str, list[IncidentStageEvent]] = {}
    for event in session.scalars(select(IncidentStageEvent)):
        events_by_incident.setdefault(event.incident_id, []).append(event)
    for events in events_by_incident.values():
        events.sort(key=lambda event: (event.occurred_at, event.event_id))
    issues = validate_stage_event_transitions(events_by_incident, incidents)
    return QualityCheck(
        check_name="workflow_ontology_transition_rules",
        target_table="incident_stage_events",
        severity="ERROR",
        failed_keys=[
            f"{issue.incident_id} {issue.issue_type} {issue.evidence.get('event_id', '')}".strip()
            for issue in issues
        ],
        message="Stage event history must follow the workflow ontology transition rules.",
    )


def _check_zone_vocabulary(session: Session) -> QualityCheck:
    issues = validate_zone_vocabulary(session.scalars(select(InfrastructureZone)))
    return QualityCheck(
        check_name="workflow_ontology_zone_vocabulary",
        target_table="infrastructure_zones",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('zone_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Zone priority and operational status values must match the workflow ontology vocabulary.",
    )


def _check_asset_vocabulary(session: Session) -> QualityCheck:
    issues = validate_asset_vocabulary(session.scalars(select(InfrastructureAsset)))
    return QualityCheck(
        check_name="workflow_ontology_asset_vocabulary",
        target_table="infrastructure_assets",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('asset_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Asset criticality and operational status values must match the workflow ontology vocabulary.",
    )


def _check_dependency_vocabulary(session: Session) -> QualityCheck:
    asset_ids = {
        asset_id
        for asset_id, in session.execute(select(InfrastructureAsset.asset_id))
    }
    issues = validate_dependency_vocabulary(
        session.scalars(select(InfrastructureDependency)).all(),
        asset_ids,
    )
    return QualityCheck(
        check_name="workflow_ontology_dependency_vocabulary",
        target_table="infrastructure_dependencies",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('dependency_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Infrastructure topology dependency edges must reference known assets and use allowed type and role values.",
    )


def _check_spare_vocabulary(session: Session) -> QualityCheck:
    issues = validate_spare_vocabulary(session.scalars(select(CriticalSpare)))
    return QualityCheck(
        check_name="workflow_ontology_spare_vocabulary",
        target_table="critical_spares",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('spare_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Critical spare stock status values must match the workflow ontology vocabulary.",
    )


def _check_work_order_vocabulary(session: Session) -> QualityCheck:
    issues = validate_work_order_vocabulary(session.scalars(select(FacilityWorkOrder)))
    return QualityCheck(
        check_name="workflow_ontology_work_order_vocabulary",
        target_table="facility_work_orders",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('work_order_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Facility work order status values must match the workflow ontology vocabulary.",
    )


def _check_validation_vocabulary(session: Session) -> QualityCheck:
    issues = validate_validation_vocabulary(session.scalars(select(ValidationResult)))
    return QualityCheck(
        check_name="workflow_ontology_validation_vocabulary",
        target_table="validation_results",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('validation_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Validation status values must match the workflow ontology vocabulary.",
    )


def _check_telemetry_vocabulary(session: Session) -> QualityCheck:
    issues = validate_telemetry_vocabulary(session.scalars(select(TelemetryAlert)))
    return QualityCheck(
        check_name="workflow_ontology_telemetry_vocabulary",
        target_table="telemetry_alerts",
        severity="ERROR",
        failed_keys=[
            f"{issue.evidence.get('telemetry_alert_id')} {issue.issue_type}"
            for issue in issues
        ],
        message="Telemetry severity values must match the workflow ontology vocabulary.",
    )


def _check_telemetry_alert_without_known_asset(session: Session) -> QualityCheck:
    asset_ids = {
        row[0]
        for row in session.execute(select(InfrastructureAsset.asset_id))
    }
    failed = [
        alert.telemetry_alert_id
        for alert in session.scalars(select(TelemetryAlert))
        if alert.asset_id not in asset_ids
    ]
    return QualityCheck(
        check_name="telemetry_alert_without_known_asset",
        target_table="telemetry_alerts",
        severity="ERROR",
        failed_keys=failed,
        message="Telemetry alerts should reference known infrastructure assets.",
    )


def _quality_results_to_models(
    checks: list[QualityCheck],
    pipeline_run_id: str,
    start_index: int,
) -> list[DataQualityCheckResult]:
    return [
        DataQualityCheckResult(
            check_result_id=f"DQ-{pipeline_run_id}-{index:03d}",
            pipeline_run_id=pipeline_run_id,
            check_name=check.check_name,
            target_table=check.target_table,
            severity=check.severity,
            status=check.status,
            failed_row_count=len(check.failed_keys),
            sample_failed_keys=check.failed_keys[:10],
            message=check.message,
        )
        for index, check in enumerate(checks, start=start_index)
    ]
