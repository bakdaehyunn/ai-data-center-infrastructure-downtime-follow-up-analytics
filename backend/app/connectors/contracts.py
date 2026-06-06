from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorContract:
    source_name: str
    extract_file: str
    target_table: str
    cadence: str
    required_payload_fields: tuple[str, ...]
    optional_payload_fields: tuple[str, ...] = ()
    notes: str = ""


CONNECTOR_CONTRACTS = (
    ConnectorContract(
        source_name="incident_management",
        extract_file="infrastructure_incidents.json",
        target_table="raw_infrastructure_incidents",
        cadence="15 minutes during active operations",
        required_payload_fields=(
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
        ),
        optional_payload_fields=("actual_downtime_hours", "scenario_key"),
        notes="Source of record for incident identity, lifecycle status, priority, and business impact.",
    ),
    ConnectorContract(
        source_name="workflow_events",
        extract_file="incident_stage_events.json",
        target_table="raw_incident_stage_events",
        cadence="15 minutes during active operations",
        required_payload_fields=(
            "event_id",
            "incident_id",
            "stage",
            "event_type",
            "event_status",
            "occurred_at",
            "actor_type",
            "source_system",
        ),
        optional_payload_fields=("actor_id", "reason_code", "metadata_json"),
        notes="Append-only lifecycle and impact evidence used to reconstruct workflow state.",
    ),
    ConnectorContract(
        source_name="facility_work_orders",
        extract_file="facility_work_orders.json",
        target_table="raw_facility_work_orders",
        cadence="15 minutes during active operations",
        required_payload_fields=("work_order_id", "incident_id", "assigned_team", "work_order_status"),
        optional_payload_fields=(
            "assigned_engineer_id",
            "planned_start_at",
            "actual_start_at",
            "actual_completed_at",
            "required_spare_id",
        ),
        notes="Maintenance execution evidence for assignment, repair progress, and spare/vendor blockers.",
    ),
    ConnectorContract(
        source_name="validation_results",
        extract_file="validation_results.json",
        target_table="raw_validation_results",
        cadence="15 minutes during active operations",
        required_payload_fields=("validation_id", "incident_id", "validation_status"),
        optional_payload_fields=(
            "validator_id",
            "validation_started_at",
            "validation_completed_at",
            "failure_reason",
        ),
        notes="Return-to-service validation evidence after repair completion.",
    ),
    ConnectorContract(
        source_name="telemetry_alerts",
        extract_file="telemetry_alerts.json",
        target_table="raw_telemetry_alerts",
        cadence="5 to 15 minutes based on monitoring export cost",
        required_payload_fields=("telemetry_alert_id", "asset_id", "alert_type", "severity", "triggered_at"),
        optional_payload_fields=("resolved_at", "linked_incident_id", "metadata_json"),
        notes="Operational telemetry evidence linked to incident impact and trust checks.",
    ),
    ConnectorContract(
        source_name="infrastructure_topology",
        extract_file="infrastructure_dependencies.json",
        target_table="infrastructure_dependencies",
        cadence="daily or on approved configuration change",
        required_payload_fields=(
            "dependency_id",
            "dependent_asset_id",
            "dependency_asset_id",
            "dependency_type",
            "dependency_role",
            "impact_scope",
            "source_system",
        ),
        optional_payload_fields=("metadata_json",),
        notes="Read-only dependency graph extract. It must not contain credentials or live connector secrets.",
    ),
)


def connector_contracts_payload() -> list[dict[str, object]]:
    return [
        {
            "source_name": contract.source_name,
            "extract_file": contract.extract_file,
            "target_table": contract.target_table,
            "cadence": contract.cadence,
            "required_payload_fields": list(contract.required_payload_fields),
            "optional_payload_fields": list(contract.optional_payload_fields),
            "notes": contract.notes,
        }
        for contract in CONNECTOR_CONTRACTS
    ]
