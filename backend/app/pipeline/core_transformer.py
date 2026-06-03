from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.infrastructure import (
    InfrastructureAsset,
    ValidationResult,
    InfrastructureIncident,
    IncidentStageEvent,
    FacilityWorkOrder,
    CriticalSpare,
    InfrastructureZone,
    TelemetryAlert,
    FacilitiesEngineer,
)
from app.models.raw import (
    RawValidationResult,
    RawInfrastructureIncident,
    RawIncidentStageEvent,
    RawFacilityWorkOrder,
    RawTelemetryAlert,
)
from app.pipeline.quality import REQUIRED_PAYLOAD_FIELDS


@dataclass(frozen=True)
class CoreTransformResult:
    infrastructure_zones_loaded: int
    infrastructure_assets_loaded: int
    facilities_engineers_loaded: int
    critical_spares_loaded: int
    infrastructure_incidents_loaded: int
    incident_stage_events_loaded: int
    facility_work_orders_loaded: int
    validation_results_loaded: int
    telemetry_alerts_loaded: int
    records_skipped: int


def transform_raw_to_core(session: Session, sample_dir: Path) -> CoreTransformResult:
    skipped = 0
    masters = _load_master_records(sample_dir)

    infrastructure_zones_loaded = _merge_infrastructure_zones(session, masters["infrastructure_zones"])
    infrastructure_assets_loaded = _merge_infrastructure_assets(session, masters["infrastructure_assets"])
    facilities_engineers_loaded = _merge_facilities_engineers(session, masters["facilities_engineers"])
    critical_spares_loaded = _merge_critical_spares(session, masters["critical_spares"])
    session.flush()

    valid_zone_ids = _id_set(session, InfrastructureZone.zone_id)
    valid_asset_ids = _id_set(session, InfrastructureAsset.asset_id)
    valid_engineer_ids = _id_set(session, FacilitiesEngineer.engineer_id)
    valid_spare_ids = _id_set(session, CriticalSpare.spare_id)

    infrastructure_incidents_loaded = 0
    for raw_record in session.scalars(select(RawInfrastructureIncident)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_infrastructure_incidents", payload):
            skipped += 1
            continue
        if payload["asset_id"] not in valid_asset_ids or payload["zone_id"] not in valid_zone_ids:
            skipped += 1
            continue
        session.merge(_infrastructure_request_from_payload(payload))
        infrastructure_incidents_loaded += 1
    session.flush()

    valid_request_ids = _id_set(session, InfrastructureIncident.incident_id)

    incident_stage_events_loaded = 0
    for raw_record in session.scalars(select(RawIncidentStageEvent)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_incident_stage_events", payload):
            skipped += 1
            continue
        if payload["incident_id"] not in valid_request_ids:
            skipped += 1
            continue
        session.merge(_infrastructure_stage_event_from_payload(payload))
        incident_stage_events_loaded += 1

    facility_work_orders_loaded = 0
    for raw_record in session.scalars(select(RawFacilityWorkOrder)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_facility_work_orders", payload):
            skipped += 1
            continue
        if payload["incident_id"] not in valid_request_ids:
            skipped += 1
            continue
        if payload.get("assigned_engineer_id") and payload["assigned_engineer_id"] not in valid_engineer_ids:
            skipped += 1
            continue
        if payload.get("required_spare_id") and payload["required_spare_id"] not in valid_spare_ids:
            skipped += 1
            continue
        session.merge(_infrastructure_work_order_from_payload(payload))
        facility_work_orders_loaded += 1

    validation_results_loaded = 0
    for raw_record in session.scalars(select(RawValidationResult)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_validation_results", payload):
            skipped += 1
            continue
        if payload["incident_id"] not in valid_request_ids:
            skipped += 1
            continue
        if payload.get("validator_id") and payload["validator_id"] not in valid_engineer_ids:
            skipped += 1
            continue
        session.merge(_validation_result_from_payload(payload))
        validation_results_loaded += 1

    telemetry_alerts_loaded = 0
    for raw_record in session.scalars(select(RawTelemetryAlert)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_telemetry_alerts", payload):
            skipped += 1
            continue
        if payload["asset_id"] not in valid_asset_ids:
            skipped += 1
            continue
        if payload.get("linked_incident_id") and payload["linked_incident_id"] not in valid_request_ids:
            skipped += 1
            continue
        session.merge(_telemetry_alert_from_payload(payload))
        telemetry_alerts_loaded += 1

    session.flush()
    return CoreTransformResult(
        infrastructure_zones_loaded=infrastructure_zones_loaded,
        infrastructure_assets_loaded=infrastructure_assets_loaded,
        facilities_engineers_loaded=facilities_engineers_loaded,
        critical_spares_loaded=critical_spares_loaded,
        infrastructure_incidents_loaded=infrastructure_incidents_loaded,
        incident_stage_events_loaded=incident_stage_events_loaded,
        facility_work_orders_loaded=facility_work_orders_loaded,
        validation_results_loaded=validation_results_loaded,
        telemetry_alerts_loaded=telemetry_alerts_loaded,
        records_skipped=skipped,
    )


def _load_master_records(sample_dir: Path) -> dict[str, list[dict[str, Any]]]:
    records = {}
    for name in ["infrastructure_zones", "infrastructure_assets", "facilities_engineers", "critical_spares"]:
        path = sample_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing master data file: {path}")
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise ValueError(f"Expected list records in {path}")
        records[name] = loaded
    return records


def _merge_infrastructure_zones(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            InfrastructureZone(
                zone_id=record["zone_id"],
                zone_code=record["zone_code"],
                zone_name=record["zone_name"],
                facility_area=record["facility_area"],
                zone_priority=record["zone_priority"],
                current_status=record["current_status"],
            )
        )
    return len(records)


def _merge_infrastructure_assets(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            InfrastructureAsset(
                asset_id=record["asset_id"],
                asset_code=record["asset_code"],
                asset_name=record["asset_name"],
                asset_type=record["asset_type"],
                zone_id=record["zone_id"],
                criticality_level=record["criticality_level"],
                installed_at=_parse_datetime(record["installed_at"]),
                manufacturer=record["manufacturer"],
                model_number=record["model_number"],
                current_status=record["current_status"],
            )
        )
    return len(records)


def _merge_facilities_engineers(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            FacilitiesEngineer(
                engineer_id=record["engineer_id"],
                engineer_name=record["engineer_name"],
                team_name=record["team_name"],
                skill_group=record["skill_group"],
                shift=record["shift"],
                active_status=record["active_status"],
            )
        )
    return len(records)


def _merge_critical_spares(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            CriticalSpare(
                spare_id=record["spare_id"],
                spare_number=record["spare_number"],
                spare_name=record["spare_name"],
                spare_category=record["spare_category"],
                stock_status=record["stock_status"],
                lead_time_days=float(record["lead_time_days"]),
                critical_spare=record["critical_spare"],
            )
        )
    return len(records)


def _infrastructure_request_from_payload(payload: dict[str, Any]) -> InfrastructureIncident:
    return InfrastructureIncident(
        incident_id=payload["incident_id"],
        request_number=payload["request_number"],
        asset_id=payload["asset_id"],
        zone_id=payload["zone_id"],
        request_title=payload["request_title"],
        request_type=payload["request_type"],
        priority_level=payload["priority_level"],
        failure_mode=payload["failure_mode"],
        reported_at=_parse_datetime(payload["reported_at"]),
        needed_by_at=_parse_datetime(payload["needed_by_at"]),
        current_stage=payload["current_stage"],
        current_status=payload["current_status"],
        business_impact=payload["business_impact"],
        estimated_downtime_hours=float(payload["estimated_downtime_hours"]),
        actual_downtime_hours=_parse_optional_float(payload.get("actual_downtime_hours")),
    )


def _infrastructure_stage_event_from_payload(payload: dict[str, Any]) -> IncidentStageEvent:
    return IncidentStageEvent(
        event_id=payload["event_id"],
        incident_id=payload["incident_id"],
        stage=payload["stage"],
        event_type=payload["event_type"],
        event_status=payload["event_status"],
        occurred_at=_parse_datetime(payload["occurred_at"]),
        actor_type=payload["actor_type"],
        actor_id=payload.get("actor_id"),
        reason_code=payload.get("reason_code"),
        metadata_json=payload.get("metadata_json"),
        source_system=payload["source_system"],
    )


def _infrastructure_work_order_from_payload(payload: dict[str, Any]) -> FacilityWorkOrder:
    return FacilityWorkOrder(
        work_order_id=payload["work_order_id"],
        incident_id=payload["incident_id"],
        assigned_team=payload["assigned_team"],
        assigned_engineer_id=payload.get("assigned_engineer_id"),
        work_order_status=payload["work_order_status"],
        planned_start_at=_parse_optional_datetime(payload.get("planned_start_at")),
        actual_start_at=_parse_optional_datetime(payload.get("actual_start_at")),
        actual_completed_at=_parse_optional_datetime(payload.get("actual_completed_at")),
        required_spare_id=payload.get("required_spare_id"),
    )


def _validation_result_from_payload(payload: dict[str, Any]) -> ValidationResult:
    return ValidationResult(
        validation_id=payload["validation_id"],
        incident_id=payload["incident_id"],
        validation_status=payload["validation_status"],
        validator_id=payload.get("validator_id"),
        validation_started_at=_parse_optional_datetime(payload.get("validation_started_at")),
        validation_completed_at=_parse_optional_datetime(payload.get("validation_completed_at")),
        failure_reason=payload.get("failure_reason"),
    )


def _telemetry_alert_from_payload(payload: dict[str, Any]) -> TelemetryAlert:
    return TelemetryAlert(
        telemetry_alert_id=payload["telemetry_alert_id"],
        asset_id=payload["asset_id"],
        alert_type=payload["alert_type"],
        severity=payload["severity"],
        triggered_at=_parse_datetime(payload["triggered_at"]),
        resolved_at=_parse_optional_datetime(payload.get("resolved_at")),
        linked_incident_id=payload.get("linked_incident_id"),
        metadata_json=payload.get("metadata_json"),
    )


def _has_required_fields(target_table: str, payload: dict[str, Any]) -> bool:
    return all(payload.get(field) not in (None, "") for field in REQUIRED_PAYLOAD_FIELDS[target_table])


def _id_set(session: Session, column) -> set[Any]:
    return {row[0] for row in session.execute(select(column))}


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return _parse_datetime(value) if value else None


def _parse_optional_float(value: Any | None) -> float | None:
    return float(value) if value is not None else None
