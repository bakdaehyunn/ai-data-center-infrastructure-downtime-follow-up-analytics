from __future__ import annotations

import argparse
import json
import random
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.sample_data.infrastructure_scenarios import (
    ACTIVE_STATUS,
    INFRASTRUCTURE_EXIT_EVENT_BY_STAGE,
    INFRASTRUCTURE_SCENARIO_PROFILES,
    INFRASTRUCTURE_SOURCE_SYSTEM,
    INFRASTRUCTURE_STAGE_FLOW,
    TERMINAL_STAGE,
    TERMINAL_STATUS,
)

DEFAULT_SEED = 20260523
DEFAULT_BASE_TIME = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)


def generate_sample_dataset(
    seed: int = DEFAULT_SEED,
    base_time: datetime = DEFAULT_BASE_TIME,
) -> dict[str, Any]:
    rng = random.Random(seed)
    masters = _generate_infrastructure_master_data()
    infrastructure_incidents: list[dict[str, Any]] = []
    incident_stage_events: list[dict[str, Any]] = []
    facility_work_orders: list[dict[str, Any]] = []
    validation_results: list[dict[str, Any]] = []
    telemetry_alerts: list[dict[str, Any]] = []
    scenario_summaries: list[dict[str, str]] = []

    for index, profile in enumerate(INFRASTRUCTURE_SCENARIO_PROFILES, start=1):
        request_id = f"INC-{index:04d}"
        request_number = f"INC-2026-{index:04d}"
        reported_at = base_time + timedelta(hours=(index - 1) * 7 + rng.randint(0, 2))
        needed_by_at = reported_at + timedelta(hours=profile.needed_by_offset_hours)

        event_payloads = _build_incident_stage_events(
            incident_id=request_id,
            profile=profile,
            reported_at=reported_at,
        )
        incident_stage_events.extend(
            _infrastructure_source_record(
                record_type="infrastructure_stage_event",
                record_id=event["event_id"],
                payload=event,
            )
            for event in event_payloads
        )

        asset = _infrastructure_master_by_id(masters["infrastructure_assets"], "asset_id", profile.asset_id)
        current_stage = _current_infrastructure_stage(profile)
        current_status = TERMINAL_STATUS if current_stage == TERMINAL_STAGE else ACTIVE_STATUS
        actual_downtime_hours = (
            sum(profile.stage_durations_hours.values())
            if current_status == TERMINAL_STATUS
            else None
        )
        infrastructure_incidents.append(
            _infrastructure_source_record(
                record_type="infrastructure_request",
                record_id=request_id,
                payload={
                    "incident_id": request_id,
                    "request_number": request_number,
                    "asset_id": profile.asset_id,
                    "zone_id": asset["zone_id"],
                    "request_title": profile.title,
                    "request_type": profile.incident_type,
                    "priority_level": profile.priority_level,
                    "failure_mode": profile.failure_mode,
                    "reported_at": _iso(reported_at),
                    "needed_by_at": _iso(needed_by_at),
                    "current_stage": current_stage,
                    "current_status": current_status,
                    "business_impact": profile.business_impact,
                    "estimated_downtime_hours": profile.estimated_downtime_hours,
                    "actual_downtime_hours": actual_downtime_hours,
                    "scenario_key": profile.scenario_key,
                },
            )
        )

        if _infrastructure_stage_reached(profile, "ENGINEER_ASSIGNED"):
            work_order_id = f"MWO-{index:04d}"
            work_status = _infrastructure_work_order_status(profile)
            facility_work_orders.append(
                _infrastructure_source_record(
                    record_type="infrastructure_work_order",
                    record_id=work_order_id,
                    payload={
                        "work_order_id": work_order_id,
                        "incident_id": request_id,
                        "assigned_team": _infrastructure_team_for_engineer(profile.assigned_engineer_id),
                        "assigned_engineer_id": profile.assigned_engineer_id,
                        "work_order_status": work_status,
                        "planned_start_at": _iso_or_none(_infrastructure_event_time(event_payloads, "REPAIR_IN_PROGRESS", "ENTERED_STAGE")),
                        "actual_start_at": _iso_or_none(_infrastructure_event_time(event_payloads, "REPAIR_IN_PROGRESS", "ENTERED_STAGE")),
                        "actual_completed_at": _iso_or_none(_infrastructure_event_time(event_payloads, "REPAIR_IN_PROGRESS", "REPAIR_COMPLETED")),
                        "required_spare_id": profile.required_spare_id,
                        "scenario_key": profile.scenario_key,
                    },
                )
            )

        if _infrastructure_stage_reached(profile, "VALIDATION"):
            validation_id = f"VAL-{index:04d}"
            validation_completed_at = _infrastructure_event_time(event_payloads, "VALIDATION", "VALIDATION_PASSED")
            validation_results.append(
                _infrastructure_source_record(
                    record_type="validation_result",
                    record_id=validation_id,
                    payload={
                        "validation_id": validation_id,
                        "incident_id": request_id,
                        "validation_status": "PASSED" if validation_completed_at else "PENDING",
                        "validator_id": "ENG-VALID-01",
                        "validation_started_at": _iso_or_none(_infrastructure_event_time(event_payloads, "VALIDATION", "ENTERED_STAGE")),
                        "validation_completed_at": _iso_or_none(validation_completed_at),
                        "failure_reason": "Initial recovery failed thermal validation"
                        if profile.validation_failed_once
                        else None,
                        "scenario_key": profile.scenario_key,
                    },
                )
            )

        if profile.telemetry_alert_type:
            alert_id = f"ALERT-{index:04d}"
            telemetry_alerts.append(
                _infrastructure_source_record(
                    record_type="telemetry_alert",
                    record_id=alert_id,
                    payload={
                        "telemetry_alert_id": alert_id,
                        "asset_id": profile.asset_id,
                        "alert_type": profile.telemetry_alert_type,
                        "severity": "CRITICAL" if profile.priority_level == "CRITICAL" else "WARNING",
                        "triggered_at": _iso(reported_at - timedelta(hours=2)),
                        "resolved_at": None if current_status != TERMINAL_STATUS else _iso(reported_at + timedelta(hours=sum(profile.stage_durations_hours.values()))),
                        "linked_incident_id": request_id,
                        "metadata_json": {"scenario_key": profile.scenario_key},
                    },
                )
            )

        scenario_summaries.append(
            {
                "scenario_key": profile.scenario_key,
                "incident_id": request_id,
                "current_stage": current_stage,
                "priority_level": profile.priority_level,
            }
        )

    expected_quality_issues = _inject_infrastructure_quality_issue_records(
        infrastructure_incidents=infrastructure_incidents,
        incident_stage_events=incident_stage_events,
        facility_work_orders=facility_work_orders,
        validation_results=validation_results,
        base_time=base_time,
    )

    return {
        "manifest": {
            "seed": seed,
            "base_time": _iso(base_time),
            "source_system": INFRASTRUCTURE_SOURCE_SYSTEM,
            "scenarios": scenario_summaries,
            "expected_quality_issues": expected_quality_issues,
        },
        **masters,
        "infrastructure_incidents": infrastructure_incidents,
        "incident_stage_events": incident_stage_events,
        "facility_work_orders": facility_work_orders,
        "validation_results": validation_results,
        "telemetry_alerts": telemetry_alerts,
    }


def write_sample_dataset(dataset: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for name, records in dataset.items():
        path = output_dir / f"{name}.json"
        path.write_text(
            json.dumps(records, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic infrastructure downtime follow-up sample data.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/sample_data"),
    )
    args = parser.parse_args()

    dataset = generate_sample_dataset(seed=args.seed)
    written = write_sample_dataset(dataset, args.output_dir)
    print(f"Wrote {len(written)} sample data files to {args.output_dir}")


def _generate_infrastructure_master_data() -> dict[str, list[dict[str, Any]]]:
    infrastructure_zones = [
        {"zone_id": "ZONE-GPU-A", "zone_code": "GPU-A", "zone_name": "GPU Hall A", "facility_area": "AI Compute Hall", "zone_priority": "CRITICAL", "current_status": "DEGRADED"},
        {"zone_id": "ZONE-POWER-A", "zone_code": "PWR-A", "zone_name": "Power Path A", "facility_area": "Electrical Room", "zone_priority": "HIGH", "current_status": "RUNNING"},
        {"zone_id": "ZONE-COOL-A", "zone_code": "COOL-A", "zone_name": "Cooling Loop A", "facility_area": "Mechanical Yard", "zone_priority": "HIGH", "current_status": "RUNNING"},
        {"zone_id": "ZONE-BACKUP", "zone_code": "BKP-01", "zone_name": "Backup Power Yard", "facility_area": "Generator Yard", "zone_priority": "CRITICAL", "current_status": "AT_RISK"},
        {"zone_id": "ZONE-DCIM", "zone_code": "DCIM-01", "zone_name": "Monitoring and Telemetry", "facility_area": "Operations", "zone_priority": "MEDIUM", "current_status": "RUNNING"},
    ]
    infrastructure_assets = [
        {"asset_id": "ASSET-CRAH-01", "asset_code": "CRAH-01", "asset_name": "CRAH Fan Array A1", "asset_type": "CRAH", "zone_id": "ZONE-GPU-A", "criticality_level": "HIGH", "installed_at": "2022-03-01T00:00:00Z", "manufacturer": "CoolCore", "model_number": "CRAH-500", "current_status": "RUNNING"},
        {"asset_id": "ASSET-UPS-01", "asset_code": "UPS-01", "asset_name": "UPS Module Bank A", "asset_type": "UPS", "zone_id": "ZONE-POWER-A", "criticality_level": "HIGH", "installed_at": "2020-07-15T00:00:00Z", "manufacturer": "PowerPro", "model_number": "UPS-2200", "current_status": "DEGRADED"},
        {"asset_id": "ASSET-PDU-01", "asset_code": "PDU-01", "asset_name": "Rack PDU Branch Panel A", "asset_type": "PDU", "zone_id": "ZONE-POWER-A", "criticality_level": "HIGH", "installed_at": "2021-11-03T00:00:00Z", "manufacturer": "VoltAxis", "model_number": "PDU-6X", "current_status": "STOPPED"},
        {"asset_id": "ASSET-CHILLER-01", "asset_code": "CHLR-01", "asset_name": "Chiller Plant Compressor A", "asset_type": "CHILLER", "zone_id": "ZONE-COOL-A", "criticality_level": "CRITICAL", "installed_at": "2019-05-20T00:00:00Z", "manufacturer": "ThermalRight", "model_number": "CH-900", "current_status": "STOPPED"},
        {"asset_id": "ASSET-CDU-01", "asset_code": "CDU-01", "asset_name": "Liquid Cooling CDU A", "asset_type": "CDU", "zone_id": "ZONE-COOL-A", "criticality_level": "HIGH", "installed_at": "2021-01-10T00:00:00Z", "manufacturer": "FlowGrid", "model_number": "CDU-40", "current_status": "DEGRADED"},
        {"asset_id": "ASSET-CRAH-02", "asset_code": "CRAH-02", "asset_name": "CRAH Thermal Control B", "asset_type": "CRAH", "zone_id": "ZONE-GPU-A", "criticality_level": "CRITICAL", "installed_at": "2022-09-12T00:00:00Z", "manufacturer": "CoolCore", "model_number": "CRAH-12", "current_status": "LOCKED_OUT"},
        {"asset_id": "ASSET-GEN-01", "asset_code": "GEN-01", "asset_name": "Backup Generator Fuel System", "asset_type": "GENERATOR", "zone_id": "ZONE-BACKUP", "criticality_level": "CRITICAL", "installed_at": "2018-04-01T00:00:00Z", "manufacturer": "GenCore", "model_number": "GEN-700", "current_status": "AT_RISK"},
        {"asset_id": "ASSET-RACK-01", "asset_code": "RACK-01", "asset_name": "GPU Rack Sensor Row A", "asset_type": "GPU_RACK", "zone_id": "ZONE-GPU-A", "criticality_level": "MEDIUM", "installed_at": "2023-02-08T00:00:00Z", "manufacturer": "RackSense", "model_number": "RS-300", "current_status": "DEGRADED"},
        {"asset_id": "ASSET-SWGR-01", "asset_code": "SWGR-01", "asset_name": "Switchgear Meter Gateway", "asset_type": "SWITCHGEAR", "zone_id": "ZONE-DCIM", "criticality_level": "MEDIUM", "installed_at": "2020-10-18T00:00:00Z", "manufacturer": "GridWatch", "model_number": "GW-80", "current_status": "RUNNING"},
    ]
    facilities_engineers = [
        {"engineer_id": "ENG-MECH-01", "engineer_name": "Mechanical Facilities Engineer 01", "team_name": "Cooling Reliability", "skill_group": "MECHANICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"engineer_id": "ENG-MECH-02", "engineer_name": "Mechanical Facilities Engineer 02", "team_name": "Chiller Plant", "skill_group": "MECHANICAL", "shift": "SWING", "active_status": "ACTIVE"},
        {"engineer_id": "ENG-MECH-03", "engineer_name": "Liquid Cooling Engineer 01", "team_name": "Liquid Cooling", "skill_group": "MECHANICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"engineer_id": "ENG-MECH-04", "engineer_name": "Generator Systems Engineer 01", "team_name": "Backup Power", "skill_group": "MECHANICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"engineer_id": "ENG-ELEC-01", "engineer_name": "Electrical Facilities Engineer 01", "team_name": "Power Systems", "skill_group": "ELECTRICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"engineer_id": "ENG-ELEC-02", "engineer_name": "Electrical Facilities Engineer 02", "team_name": "Power Systems", "skill_group": "ELECTRICAL", "shift": "NIGHT", "active_status": "ACTIVE"},
        {"engineer_id": "ENG-VALID-01", "engineer_name": "Infrastructure Validation Engineer 01", "team_name": "Facilities Validation", "skill_group": "VALIDATION", "shift": "DAY", "active_status": "ACTIVE"},
    ]
    critical_spares = [
        {"spare_id": "SPARE-CRAH-FAN", "spare_number": "CRAH-FAN-01", "spare_name": "CRAH Fan Module", "spare_category": "COOLING", "stock_status": "IN_STOCK", "lead_time_days": 1, "critical_spare": False},
        {"spare_id": "SPARE-UPS-MODULE", "spare_number": "UPS-MOD-44", "spare_name": "UPS Power Module", "spare_category": "POWER", "stock_status": "LOW_STOCK", "lead_time_days": 3, "critical_spare": True},
        {"spare_id": "SPARE-BREAKER-MODULE", "spare_number": "BRK-PDU-X4", "spare_name": "PDU Breaker Module", "spare_category": "ELECTRICAL", "stock_status": "IN_STOCK", "lead_time_days": 2, "critical_spare": True},
        {"spare_id": "SPARE-CHILLER-COMPRESSOR", "spare_number": "CHLR-CMP-7", "spare_name": "Chiller Compressor Assembly", "spare_category": "COOLING", "stock_status": "OUT_OF_STOCK", "lead_time_days": 14, "critical_spare": True},
        {"spare_id": "SPARE-COOLANT-PUMP-SEAL", "spare_number": "CDU-SEAL-20", "spare_name": "CDU Coolant Pump Seal", "spare_category": "LIQUID_COOLING", "stock_status": "IN_STOCK", "lead_time_days": 2, "critical_spare": True},
        {"spare_id": "SPARE-TEMP-SENSOR", "spare_number": "TMP-SNS-24V", "spare_name": "Thermal Validation Sensor", "spare_category": "SENSOR", "stock_status": "LOW_STOCK", "lead_time_days": 5, "critical_spare": True},
        {"spare_id": "SPARE-FUEL-PUMP", "spare_number": "GEN-FP-9", "spare_name": "Generator Fuel Pump", "spare_category": "GENERATOR", "stock_status": "OUT_OF_STOCK", "lead_time_days": 7, "critical_spare": True},
        {"spare_id": "SPARE-RACK-TEMP-SENSOR", "spare_number": "RACK-TMP-2", "spare_name": "Rack Inlet Temperature Sensor", "spare_category": "SENSOR", "stock_status": "IN_STOCK", "lead_time_days": 2, "critical_spare": False},
        {"spare_id": "SPARE-POWER-METER", "spare_number": "PWR-MTR-01", "spare_name": "Switchgear Power Meter", "spare_category": "METERING", "stock_status": "LOW_STOCK", "lead_time_days": 4, "critical_spare": False},
    ]
    return {
        "infrastructure_zones": infrastructure_zones,
        "infrastructure_assets": infrastructure_assets,
        "facilities_engineers": facilities_engineers,
        "critical_spares": critical_spares,
    }


def _build_incident_stage_events(
    incident_id: str,
    profile: Any,
    reported_at: datetime,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    current_time = reported_at

    for stage in INFRASTRUCTURE_STAGE_FLOW:
        if not _infrastructure_stage_reached(profile, stage):
            break

        events.append(
            _infrastructure_stage_event_payload(
                incident_id=incident_id,
                sequence=len(events) + 1,
                stage=stage,
                event_type="ENTERED_STAGE",
                event_status="SUCCESS",
                occurred_at=current_time,
                reason_code=None,
            )
        )

        if stage == "VALIDATION" and profile.validation_failed_once:
            failed_time = current_time + timedelta(hours=6)
            events.append(
                _infrastructure_stage_event_payload(
                    incident_id=incident_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="VALIDATION_FAILED",
                    event_status="ACTION_REQUIRED",
                    occurred_at=failed_time,
                    reason_code="REPAIR_VALIDATION_FAILED",
                )
            )

        if profile.stop_stage == stage:
            break

        if stage == TERMINAL_STAGE:
            events.append(
                _infrastructure_stage_event_payload(
                    incident_id=incident_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="INCIDENT_RESTORED",
                    event_status="SUCCESS",
                    occurred_at=current_time,
                    reason_code=None,
                )
            )
            break

        duration = profile.stage_durations_hours.get(stage, 4)
        current_time = current_time + timedelta(hours=duration)
        events.append(
            _infrastructure_stage_event_payload(
                incident_id=incident_id,
                sequence=len(events) + 1,
                stage=stage,
                event_type=INFRASTRUCTURE_EXIT_EVENT_BY_STAGE[stage],
                event_status="SUCCESS",
                occurred_at=current_time,
                reason_code=None,
            )
        )

    return events


def _inject_infrastructure_quality_issue_records(
    infrastructure_incidents: list[dict[str, Any]],
    incident_stage_events: list[dict[str, Any]],
    facility_work_orders: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    base_time: datetime,
) -> list[dict[str, str]]:
    issues = []

    duplicate_record = deepcopy(infrastructure_incidents[0])
    duplicate_record["payload"]["incident_id"] = "INC-QA-DUPLICATE"
    duplicate_record["payload"]["scenario_key"] = "qa_infrastructure_duplicate_source_record"
    infrastructure_incidents.append(duplicate_record)
    issues.append({"check_name": "duplicate_source_record", "target_file": "infrastructure_incidents.json"})

    infrastructure_incidents.append(
        _infrastructure_source_record(
            record_type="infrastructure_request",
            record_id="INC-QA-MISSING-FIELD",
            payload={
                "incident_id": "INC-QA-MISSING-FIELD",
                "request_number": "INC-2026-QA-MISSING",
                "asset_id": "ASSET-CRAH-01",
                "scenario_key": "qa_infrastructure_missing_required_field",
            },
        )
    )
    issues.append({"check_name": "missing_required_fields", "target_file": "infrastructure_incidents.json"})

    infrastructure_incidents.append(
        _infrastructure_source_record(
            record_type="infrastructure_request",
            record_id="INC-QA-NO-STAGE",
            payload={
                "incident_id": "INC-QA-NO-STAGE",
                "request_number": "INC-2026-QA-NO-STAGE",
                "asset_id": "ASSET-CRAH-01",
                "zone_id": "ZONE-GPU-A",
                "request_title": "Infrastructure incident missing stage events",
                "request_type": "CORRECTIVE",
                "priority_level": "LOW",
                "failure_mode": "DATA_QUALITY_TEST",
                "reported_at": _iso(base_time),
                "needed_by_at": _iso(base_time + timedelta(hours=24)),
                "current_stage": "INCIDENT_REPORTED",
                "current_status": ACTIVE_STATUS,
                "business_impact": "DATA_QUALITY_TEST",
                "estimated_downtime_hours": 1,
                "actual_downtime_hours": None,
                "scenario_key": "qa_infrastructure_request_without_stage_event",
            },
        )
    )
    issues.append({"check_name": "infrastructure_incident_without_stage_event", "target_file": "incident_stage_events.json"})

    incident_stage_events.append(
        _infrastructure_source_record(
            record_type="infrastructure_stage_event",
            record_id="IEVT-QA-OUT-OF-ORDER",
            payload=_infrastructure_stage_event_payload(
                incident_id="INC-0001",
                sequence=999,
                stage="FACILITIES_TRIAGE",
                event_type="TRIAGE_COMPLETED",
                event_status="SUCCESS",
                occurred_at=base_time - timedelta(days=10),
                reason_code="QA_OUT_OF_ORDER",
            ),
        )
    )
    issues.append({"check_name": "stage_event_timestamp_out_of_order", "target_file": "incident_stage_events.json"})

    facility_work_orders.append(
        _infrastructure_source_record(
            record_type="infrastructure_work_order",
            record_id="MWO-QA-NO-PART",
            payload={
                "work_order_id": "MWO-QA-NO-PART",
                "incident_id": "INC-0004",
                "assigned_team": "Chiller Plant",
                "assigned_engineer_id": "ENG-MECH-02",
                "work_order_status": "WAITING_SPARE_VENDOR",
                "planned_start_at": None,
                "actual_start_at": None,
                "actual_completed_at": None,
                "required_spare_id": None,
                "scenario_key": "qa_spare_waiting_without_required_spare",
            },
        )
    )
    issues.append({"check_name": "spare_waiting_without_required_spare", "target_file": "facility_work_orders.json"})

    validation_results.append(
        _infrastructure_source_record(
            record_type="validation_result",
            record_id="INSP-QA-NO-WORK",
            payload={
                "validation_id": "INSP-QA-NO-WORK",
                "incident_id": "INC-0002",
                "validation_status": "PASSED",
                "validator_id": "ENG-VALID-01",
                "validation_started_at": _iso(base_time + timedelta(hours=1)),
                "validation_completed_at": _iso(base_time + timedelta(hours=2)),
                "failure_reason": None,
                "scenario_key": "qa_validation_without_completed_work",
            },
        )
    )
    issues.append({"check_name": "validation_without_completed_work", "target_file": "validation_results.json"})

    return issues


def _infrastructure_source_record(record_type: str, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": INFRASTRUCTURE_SOURCE_SYSTEM,
        "source_record_id": f"SRC-{record_type.upper()}-{record_id}",
        "payload": payload,
    }


def _infrastructure_stage_event_payload(
    incident_id: str,
    sequence: int,
    stage: str,
    event_type: str,
    event_status: str,
    occurred_at: datetime,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "event_id": f"IEVT-{incident_id}-{sequence:03d}",
        "incident_id": incident_id,
        "stage": stage,
        "event_type": event_type,
        "event_status": event_status,
        "occurred_at": _iso(occurred_at),
        "actor_type": _infrastructure_actor_type_for_stage(stage),
        "actor_id": _infrastructure_actor_id_for_stage(stage),
        "reason_code": reason_code,
        "metadata_json": {},
        "source_system": INFRASTRUCTURE_SOURCE_SYSTEM,
    }


def _infrastructure_stage_reached(profile: Any, stage: str) -> bool:
    if profile.stop_stage is None:
        return True
    return INFRASTRUCTURE_STAGE_FLOW.index(stage) <= INFRASTRUCTURE_STAGE_FLOW.index(profile.stop_stage)


def _current_infrastructure_stage(profile: Any) -> str:
    return profile.stop_stage or TERMINAL_STAGE


def _infrastructure_event_time(events: list[dict[str, Any]], stage: str, event_type: str) -> datetime | None:
    for event in events:
        if event["stage"] == stage and event["event_type"] == event_type:
            return datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    return None


def _infrastructure_master_by_id(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for record in records:
        if record[key] == value:
            return record
    raise KeyError(value)


def _infrastructure_team_for_engineer(engineer_id: str | None) -> str:
    return {
        "ENG-MECH-01": "Cooling Reliability",
        "ENG-MECH-02": "Chiller Plant",
        "ENG-MECH-03": "Liquid Cooling",
        "ENG-MECH-04": "Backup Power",
        "ENG-ELEC-01": "Power Systems",
        "ENG-ELEC-02": "Power Systems",
        "ENG-VALID-01": "Facilities Validation",
        None: "Unassigned",
    }[engineer_id]


def _infrastructure_work_order_status(profile: Any) -> str:
    if profile.stop_stage == "ENGINEER_ASSIGNED":
        return "ASSIGNMENT_PENDING"
    if profile.stop_stage == "SPARE_VENDOR_WAITING":
        return "WAITING_SPARE_VENDOR"
    if profile.stop_stage == "REPAIR_IN_PROGRESS":
        return "IN_PROGRESS"
    if profile.stop_stage == "VALIDATION":
        return "REPAIR_COMPLETED"
    return TERMINAL_STATUS


def _infrastructure_actor_type_for_stage(stage: str) -> str:
    return {
        "INCIDENT_REPORTED": "MONITORING",
        "FACILITIES_TRIAGE": "FACILITIES_PLANNER",
        "ENGINEER_ASSIGNED": "FACILITIES_SUPERVISOR",
        "SPARE_VENDOR_WAITING": "STOREROOM_OR_VENDOR",
        "REPAIR_IN_PROGRESS": "FACILITIES_ENGINEER",
        "VALIDATION": "VALIDATION_ENGINEER",
        "RESTORED": "SYSTEM",
    }[stage]


def _infrastructure_actor_id_for_stage(stage: str) -> str:
    return {
        "INCIDENT_REPORTED": "DCIM",
        "FACILITIES_TRIAGE": "FAC-PLANNER",
        "ENGINEER_ASSIGNED": "FAC-SUPERVISOR",
        "SPARE_VENDOR_WAITING": "STOREROOM",
        "REPAIR_IN_PROGRESS": "FACILITIES_ENGINEER",
        "VALIDATION": "ENG-VALID-01",
        "RESTORED": "SYSTEM",
    }[stage]


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _iso_or_none(value: datetime | None) -> str | None:
    return _iso(value) if value else None


if __name__ == "__main__":
    main()
