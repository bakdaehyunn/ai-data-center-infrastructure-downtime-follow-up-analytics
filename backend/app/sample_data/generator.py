from __future__ import annotations

import argparse
import json
import random
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.sample_data.scenarios import (
    EXIT_EVENT_BY_STAGE,
    SCENARIO_PROFILES,
    SOURCE_SYSTEM,
    STAGE_FLOW,
)
from app.sample_data.maintenance_scenarios import (
    MAINTENANCE_EXIT_EVENT_BY_STAGE,
    MAINTENANCE_SCENARIO_PROFILES,
    MAINTENANCE_SOURCE_SYSTEM,
    MAINTENANCE_STAGE_FLOW,
)

DEFAULT_SEED = 20260523
DEFAULT_BASE_TIME = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)


def generate_sample_dataset(
    seed: int = DEFAULT_SEED,
    base_time: datetime = DEFAULT_BASE_TIME,
) -> dict[str, Any]:
    rng = random.Random(seed)
    masters = _generate_master_data()
    purchase_requests: list[dict[str, Any]] = []
    purchase_orders: list[dict[str, Any]] = []
    vendor_updates: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    stage_events: list[dict[str, Any]] = []

    scenario_summaries: list[dict[str, str]] = []

    for index, profile in enumerate(SCENARIO_PROFILES, start=1):
        request_id = f"REQ-{index:04d}"
        request_number = f"PR-2026-{index:04d}"
        submitted_at = base_time + timedelta(hours=(index - 1) * 9 + rng.randint(0, 2))
        needed_by_date = (submitted_at + timedelta(days=profile.needed_by_offset_days)).date()

        event_payloads = _build_stage_events(
            request_id=request_id,
            profile=profile,
            submitted_at=submitted_at,
        )
        stage_events.extend(
            _source_record(
                record_type="stage_event",
                record_id=event["event_id"],
                payload=event,
            )
            for event in event_payloads
        )

        current_stage = _current_stage(profile)
        current_status = "CLOSED" if current_stage == "CLOSED" else "IN_PROGRESS"
        purchase_requests.append(
            _source_record(
                record_type="purchase_request",
                record_id=request_id,
                payload={
                    "request_id": request_id,
                    "request_number": request_number,
                    "request_title": profile.title,
                    "request_type": "STANDARD",
                    "department_id": profile.department_id,
                    "requester_id": profile.requester_id,
                    "item_id": profile.item_id,
                    "quantity": profile.quantity,
                    "estimated_amount": profile.estimated_amount,
                    "currency": "USD",
                    "criticality_level": profile.criticality_level,
                    "business_impact": profile.business_impact,
                    "needed_by_date": needed_by_date.isoformat(),
                    "submitted_at": _iso(submitted_at),
                    "current_stage": current_stage,
                    "current_status": current_status,
                    "scenario_key": profile.scenario_key,
                },
            )
        )

        if _stage_reached(profile, "PO_CREATION"):
            po_created_at = _event_time(event_payloads, "PO_CREATION", "PO_CREATED")
            vendor_confirmed_at = _event_time(event_payloads, "VENDOR_CONFIRMATION", "VENDOR_CONFIRMED")
            delivery_entered_at = _event_time(event_payloads, "DELIVERY", "ENTERED_STAGE")
            delivery_exited_at = _event_time(event_payloads, "DELIVERY", "DELIVERED")
            po_id = f"PO-{index:04d}"
            expected_delivery_date = (
                delivery_entered_at + timedelta(days=_vendor_lead_days(profile.vendor_id))
                if delivery_entered_at
                else None
            )
            purchase_orders.append(
                _source_record(
                    record_type="purchase_order",
                    record_id=po_id,
                    payload={
                        "po_id": po_id,
                        "po_number": f"PO-2026-{index:04d}",
                        "request_id": request_id,
                        "vendor_id": profile.vendor_id,
                        "po_created_at": _iso_or_none(po_created_at),
                        "vendor_confirmed_at": _iso_or_none(vendor_confirmed_at),
                        "expected_delivery_date": expected_delivery_date.date().isoformat()
                        if expected_delivery_date
                        else None,
                        "actual_delivery_date": delivery_exited_at.date().isoformat()
                        if delivery_exited_at
                        else None,
                        "po_status": "CLOSED" if current_stage == "CLOSED" else "OPEN",
                        "scenario_key": profile.scenario_key,
                    },
                )
            )

            if _stage_reached(profile, "VENDOR_CONFIRMATION"):
                vendor_updates.append(
                    _source_record(
                        record_type="vendor_update",
                        record_id=f"VU-{index:04d}",
                        payload={
                            "vendor_update_id": f"VU-{index:04d}",
                            "po_id": po_id,
                            "vendor_id": profile.vendor_id,
                            "update_type": "CONFIRMATION"
                            if vendor_confirmed_at
                            else "AWAITING_CONFIRMATION",
                            "updated_at": _iso_or_none(vendor_confirmed_at or delivery_entered_at or po_created_at),
                            "message": _vendor_message(profile.scenario_key),
                            "scenario_key": profile.scenario_key,
                        },
                    )
                )

            if _stage_reached(profile, "RECEIVING"):
                received_at = _event_time(event_payloads, "RECEIVING", "GOODS_RECEIVED")
                inspection_completed_at = _event_time(event_payloads, "INSPECTION", "INSPECTION_PASSED")
                receipts.append(
                    _source_record(
                        record_type="receipt",
                        record_id=f"RCPT-{index:04d}",
                        payload={
                            "receipt_id": f"RCPT-{index:04d}",
                            "po_id": po_id,
                            "received_at": _iso_or_none(received_at),
                            "received_quantity": profile.quantity,
                            "inspection_status": "PASSED"
                            if inspection_completed_at
                            else "PENDING",
                            "inspection_completed_at": _iso_or_none(inspection_completed_at),
                            "rejection_reason": "Initial sample failed torque validation"
                            if profile.inspection_failed_once
                            else None,
                            "scenario_key": profile.scenario_key,
                        },
                    )
                )

        scenario_summaries.append(
            {
                "scenario_key": profile.scenario_key,
                "request_id": request_id,
                "current_stage": current_stage,
                "criticality_level": profile.criticality_level,
            }
        )

    quality_issue_records = _inject_quality_issue_records(purchase_requests, stage_events, base_time)

    return {
        "manifest": {
            "seed": seed,
            "base_time": _iso(base_time),
            "source_system": SOURCE_SYSTEM,
            "scenarios": scenario_summaries,
            "expected_quality_issues": quality_issue_records,
        },
        **masters,
        "purchase_requests": purchase_requests,
        "purchase_orders": purchase_orders,
        "vendor_updates": vendor_updates,
        "receipts": receipts,
        "stage_events": stage_events,
    }


def generate_maintenance_sample_dataset(
    seed: int = DEFAULT_SEED,
    base_time: datetime = DEFAULT_BASE_TIME,
) -> dict[str, Any]:
    rng = random.Random(seed)
    masters = _generate_maintenance_master_data()
    maintenance_requests: list[dict[str, Any]] = []
    maintenance_stage_events: list[dict[str, Any]] = []
    maintenance_work_orders: list[dict[str, Any]] = []
    inspection_results: list[dict[str, Any]] = []
    sensor_alerts: list[dict[str, Any]] = []
    scenario_summaries: list[dict[str, str]] = []

    for index, profile in enumerate(MAINTENANCE_SCENARIO_PROFILES, start=1):
        request_id = f"MREQ-{index:04d}"
        request_number = f"MR-2026-{index:04d}"
        reported_at = base_time + timedelta(hours=(index - 1) * 7 + rng.randint(0, 2))
        needed_by_at = reported_at + timedelta(hours=profile.needed_by_offset_hours)

        event_payloads = _build_maintenance_stage_events(
            request_id=request_id,
            profile=profile,
            reported_at=reported_at,
        )
        maintenance_stage_events.extend(
            _maintenance_source_record(
                record_type="maintenance_stage_event",
                record_id=event["event_id"],
                payload=event,
            )
            for event in event_payloads
        )

        equipment = _maintenance_master_by_id(masters["equipment"], "equipment_id", profile.equipment_id)
        current_stage = _current_maintenance_stage(profile)
        current_status = "COMPLETED" if current_stage == "COMPLETED" else "IN_PROGRESS"
        actual_downtime_hours = (
            sum(profile.stage_durations_hours.values())
            if current_status == "COMPLETED"
            else None
        )
        maintenance_requests.append(
            _maintenance_source_record(
                record_type="maintenance_request",
                record_id=request_id,
                payload={
                    "maintenance_request_id": request_id,
                    "request_number": request_number,
                    "equipment_id": profile.equipment_id,
                    "line_id": equipment["line_id"],
                    "request_title": profile.title,
                    "request_type": profile.request_type,
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

        if _maintenance_stage_reached(profile, "TECHNICIAN_ASSIGNED"):
            work_order_id = f"MWO-{index:04d}"
            work_status = _maintenance_work_order_status(profile)
            maintenance_work_orders.append(
                _maintenance_source_record(
                    record_type="maintenance_work_order",
                    record_id=work_order_id,
                    payload={
                        "work_order_id": work_order_id,
                        "maintenance_request_id": request_id,
                        "assigned_team": _maintenance_team_for_technician(profile.assigned_technician_id),
                        "assigned_technician_id": profile.assigned_technician_id,
                        "work_order_status": work_status,
                        "planned_start_at": _iso_or_none(_maintenance_event_time(event_payloads, "MAINTENANCE_IN_PROGRESS", "ENTERED_STAGE")),
                        "actual_start_at": _iso_or_none(_maintenance_event_time(event_payloads, "MAINTENANCE_IN_PROGRESS", "ENTERED_STAGE")),
                        "actual_completed_at": _iso_or_none(_maintenance_event_time(event_payloads, "MAINTENANCE_IN_PROGRESS", "WORK_COMPLETED")),
                        "required_part_id": profile.required_part_id,
                        "scenario_key": profile.scenario_key,
                    },
                )
            )

        if _maintenance_stage_reached(profile, "INSPECTION"):
            inspection_id = f"INSP-{index:04d}"
            inspection_completed_at = _maintenance_event_time(event_payloads, "INSPECTION", "INSPECTION_PASSED")
            inspection_results.append(
                _maintenance_source_record(
                    record_type="inspection_result",
                    record_id=inspection_id,
                    payload={
                        "inspection_id": inspection_id,
                        "maintenance_request_id": request_id,
                        "inspection_status": "PASSED" if inspection_completed_at else "PENDING",
                        "inspector_id": "TECH-QA-01",
                        "inspection_started_at": _iso_or_none(_maintenance_event_time(event_payloads, "INSPECTION", "ENTERED_STAGE")),
                        "inspection_completed_at": _iso_or_none(inspection_completed_at),
                        "failure_reason": "Initial repair failed safety interlock validation"
                        if profile.inspection_failed_once
                        else None,
                        "scenario_key": profile.scenario_key,
                    },
                )
            )

        if profile.sensor_alert_type:
            alert_id = f"ALERT-{index:04d}"
            sensor_alerts.append(
                _maintenance_source_record(
                    record_type="sensor_alert",
                    record_id=alert_id,
                    payload={
                        "sensor_alert_id": alert_id,
                        "equipment_id": profile.equipment_id,
                        "alert_type": profile.sensor_alert_type,
                        "severity": "CRITICAL" if profile.priority_level == "CRITICAL" else "WARNING",
                        "triggered_at": _iso(reported_at - timedelta(hours=2)),
                        "resolved_at": None if current_status != "COMPLETED" else _iso(reported_at + timedelta(hours=sum(profile.stage_durations_hours.values()))),
                        "linked_maintenance_request_id": request_id,
                        "metadata_json": {"scenario_key": profile.scenario_key},
                    },
                )
            )

        scenario_summaries.append(
            {
                "scenario_key": profile.scenario_key,
                "maintenance_request_id": request_id,
                "current_stage": current_stage,
                "priority_level": profile.priority_level,
            }
        )

    expected_quality_issues = _inject_maintenance_quality_issue_records(
        maintenance_requests=maintenance_requests,
        maintenance_stage_events=maintenance_stage_events,
        maintenance_work_orders=maintenance_work_orders,
        inspection_results=inspection_results,
        base_time=base_time,
    )

    return {
        "manifest": {
            "seed": seed,
            "base_time": _iso(base_time),
            "source_system": MAINTENANCE_SOURCE_SYSTEM,
            "scenarios": scenario_summaries,
            "expected_quality_issues": expected_quality_issues,
        },
        **masters,
        "maintenance_requests": maintenance_requests,
        "maintenance_stage_events": maintenance_stage_events,
        "maintenance_work_orders": maintenance_work_orders,
        "inspection_results": inspection_results,
        "sensor_alerts": sensor_alerts,
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
    parser = argparse.ArgumentParser(description="Generate deterministic procurement sample data.")
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


def _generate_master_data() -> dict[str, list[dict[str, Any]]]:
    departments = [
        {"department_id": "DEPT-IT", "department_name": "IT Operations", "department_type": "IT", "cost_center": "CC-IT-100"},
        {"department_id": "DEPT-INFRA", "department_name": "Infrastructure", "department_type": "IT", "cost_center": "CC-INF-200"},
        {"department_id": "DEPT-MFG", "department_name": "Manufacturing Support", "department_type": "OPERATIONS", "cost_center": "CC-MFG-300"},
        {"department_id": "DEPT-OPS", "department_name": "Operations", "department_type": "OPERATIONS", "cost_center": "CC-OPS-400"},
        {"department_id": "DEPT-SAFETY", "department_name": "Safety", "department_type": "COMPLIANCE", "cost_center": "CC-SAF-500"},
        {"department_id": "DEPT-SEC", "department_name": "Security", "department_type": "SECURITY", "cost_center": "CC-SEC-600"},
    ]
    requesters = [
        {"requester_id": "USR-IT-01", "requester_name": "Requester IT 01", "department_id": "DEPT-IT", "role": "Operations Analyst"},
        {"requester_id": "USR-INF-01", "requester_name": "Requester Infra 01", "department_id": "DEPT-INFRA", "role": "Infra Engineer"},
        {"requester_id": "USR-INF-02", "requester_name": "Requester Infra 02", "department_id": "DEPT-INFRA", "role": "Platform Owner"},
        {"requester_id": "USR-MFG-01", "requester_name": "Requester MFG 01", "department_id": "DEPT-MFG", "role": "Maintenance Planner"},
        {"requester_id": "USR-MFG-02", "requester_name": "Requester MFG 02", "department_id": "DEPT-MFG", "role": "Line Supervisor"},
        {"requester_id": "USR-OPS-01", "requester_name": "Requester OPS 01", "department_id": "DEPT-OPS", "role": "Warehouse Lead"},
        {"requester_id": "USR-SAF-01", "requester_name": "Requester Safety 01", "department_id": "DEPT-SAFETY", "role": "Safety Manager"},
        {"requester_id": "USR-SAF-02", "requester_name": "Requester Safety 02", "department_id": "DEPT-SAFETY", "role": "Facility Inspector"},
        {"requester_id": "USR-SEC-01", "requester_name": "Requester Security 01", "department_id": "DEPT-SEC", "role": "Security Lead"},
    ]
    items = [
        {"item_id": "ITEM-MONITOR", "item_name": "Business Monitor", "item_category": "IT_EQUIPMENT", "is_critical_item": False, "standard_lead_time_days": 3},
        {"item_id": "ITEM-SAFETY-CABINET", "item_name": "Safety Storage Cabinet", "item_category": "SAFETY_EQUIPMENT", "is_critical_item": True, "standard_lead_time_days": 5},
        {"item_id": "ITEM-CALIBRATION-KIT", "item_name": "Sensor Calibration Kit", "item_category": "PRODUCTION_MATERIAL", "is_critical_item": True, "standard_lead_time_days": 4},
        {"item_id": "ITEM-NETWORK-SWITCH", "item_name": "Network Switch", "item_category": "IT_EQUIPMENT", "is_critical_item": True, "standard_lead_time_days": 5},
        {"item_id": "ITEM-SECURITY-LICENSE", "item_name": "Security Scanner License", "item_category": "SOFTWARE_LICENSE", "is_critical_item": True, "standard_lead_time_days": 1},
        {"item_id": "ITEM-REPLACEMENT-MOTOR", "item_name": "Replacement Motor", "item_category": "MAINTENANCE_PART", "is_critical_item": True, "standard_lead_time_days": 3},
        {"item_id": "ITEM-HANDHELD-SCANNER", "item_name": "Warehouse Handheld Scanner", "item_category": "IT_EQUIPMENT", "is_critical_item": False, "standard_lead_time_days": 4},
        {"item_id": "ITEM-SAFETY-VALVE", "item_name": "Fire Suppression Valve", "item_category": "SAFETY_EQUIPMENT", "is_critical_item": True, "standard_lead_time_days": 4},
        {"item_id": "ITEM-BACKUP-APPLIANCE", "item_name": "Backup Appliance", "item_category": "IT_EQUIPMENT", "is_critical_item": True, "standard_lead_time_days": 6},
    ]
    vendors = [
        {"vendor_id": "VEN-NOVA", "vendor_name": "Nova Industrial Supply", "vendor_type": "DISTRIBUTOR", "reliability_tier": "A", "default_lead_time_days": 4},
        {"vendor_id": "VEN-APEX", "vendor_name": "Apex Safety Systems", "vendor_type": "MANUFACTURER", "reliability_tier": "B", "default_lead_time_days": 5},
        {"vendor_id": "VEN-ORBIT", "vendor_name": "Orbit Components", "vendor_type": "MANUFACTURER", "reliability_tier": "C", "default_lead_time_days": 7},
        {"vendor_id": "VEN-SIGNAL", "vendor_name": "Signal Secure Tech", "vendor_type": "SOFTWARE_VENDOR", "reliability_tier": "C", "default_lead_time_days": 3},
        {"vendor_id": "VEN-HARBOR", "vendor_name": "Harbor Logistics Equipment", "vendor_type": "DISTRIBUTOR", "reliability_tier": "B", "default_lead_time_days": 4},
    ]
    return {
        "departments": departments,
        "requesters": requesters,
        "items": items,
        "vendors": vendors,
    }


def _generate_maintenance_master_data() -> dict[str, list[dict[str, Any]]]:
    production_lines = [
        {"line_id": "LINE-PKG-01", "line_code": "PKG-01", "line_name": "Packaging Line 1", "plant_area": "Packaging", "line_priority": "CRITICAL", "current_status": "DEGRADED"},
        {"line_id": "LINE-ASM-01", "line_code": "ASM-01", "line_name": "Assembly Line 1", "plant_area": "Assembly", "line_priority": "HIGH", "current_status": "RUNNING"},
        {"line_id": "LINE-PRESS-01", "line_code": "PRESS-01", "line_name": "Press Line 1", "plant_area": "Stamping", "line_priority": "HIGH", "current_status": "RUNNING"},
        {"line_id": "LINE-UTIL-01", "line_code": "UTIL-01", "line_name": "Plant Utilities", "plant_area": "Utilities", "line_priority": "CRITICAL", "current_status": "AT_RISK"},
        {"line_id": "LINE-MIX-01", "line_code": "MIX-01", "line_name": "Mixing Line 1", "plant_area": "Batch", "line_priority": "MEDIUM", "current_status": "RUNNING"},
    ]
    equipment = [
        {"equipment_id": "EQ-CNV-001", "equipment_code": "CNV-001", "equipment_name": "Infeed Conveyor", "equipment_type": "CONVEYOR", "line_id": "LINE-ASM-01", "criticality_level": "HIGH", "installed_at": "2022-03-01T00:00:00Z", "manufacturer": "MotionWorks", "model_number": "CNV-500", "current_status": "RUNNING"},
        {"equipment_id": "EQ-PRS-001", "equipment_code": "PRS-001", "equipment_name": "Hydraulic Press", "equipment_type": "PRESS", "line_id": "LINE-PRESS-01", "criticality_level": "HIGH", "installed_at": "2020-07-15T00:00:00Z", "manufacturer": "PressPro", "model_number": "HP-2200", "current_status": "DEGRADED"},
        {"equipment_id": "EQ-RBT-001", "equipment_code": "RBT-001", "equipment_name": "Robot Arm Cell", "equipment_type": "ROBOT", "line_id": "LINE-ASM-01", "criticality_level": "HIGH", "installed_at": "2021-11-03T00:00:00Z", "manufacturer": "Axis Robotics", "model_number": "AR-6X", "current_status": "STOPPED"},
        {"equipment_id": "EQ-PKG-001", "equipment_code": "PKG-001", "equipment_name": "Servo Cartoner", "equipment_type": "PACKAGING", "line_id": "LINE-PKG-01", "criticality_level": "CRITICAL", "installed_at": "2019-05-20T00:00:00Z", "manufacturer": "PackRight", "model_number": "SC-900", "current_status": "STOPPED"},
        {"equipment_id": "EQ-FIL-001", "equipment_code": "FIL-001", "equipment_name": "Filler Pump", "equipment_type": "PUMP", "line_id": "LINE-PKG-01", "criticality_level": "HIGH", "installed_at": "2021-01-10T00:00:00Z", "manufacturer": "FlowTech", "model_number": "FP-40", "current_status": "DEGRADED"},
        {"equipment_id": "EQ-SAFE-001", "equipment_code": "SAFE-001", "equipment_name": "Safety Interlock Panel", "equipment_type": "SAFETY_SYSTEM", "line_id": "LINE-PRESS-01", "criticality_level": "CRITICAL", "installed_at": "2022-09-12T00:00:00Z", "manufacturer": "SafeLogic", "model_number": "SL-12", "current_status": "LOCKED_OUT"},
        {"equipment_id": "EQ-CMP-001", "equipment_code": "CMP-001", "equipment_name": "Main Air Compressor", "equipment_type": "COMPRESSOR", "line_id": "LINE-UTIL-01", "criticality_level": "CRITICAL", "installed_at": "2018-04-01T00:00:00Z", "manufacturer": "AirCore", "model_number": "AC-700", "current_status": "AT_RISK"},
        {"equipment_id": "EQ-PKG-002", "equipment_code": "PKG-002", "equipment_name": "Label Applicator", "equipment_type": "PACKAGING", "line_id": "LINE-PKG-01", "criticality_level": "MEDIUM", "installed_at": "2023-02-08T00:00:00Z", "manufacturer": "LabelMax", "model_number": "LM-300", "current_status": "DEGRADED"},
        {"equipment_id": "EQ-MIX-001", "equipment_code": "MIX-001", "equipment_name": "Mixer Motor", "equipment_type": "MIXER", "line_id": "LINE-MIX-01", "criticality_level": "MEDIUM", "installed_at": "2020-10-18T00:00:00Z", "manufacturer": "BatchPro", "model_number": "BM-80", "current_status": "RUNNING"},
    ]
    technicians = [
        {"technician_id": "TECH-MECH-01", "technician_name": "Mechanical Technician 01", "team_name": "Mechanical Reliability", "skill_group": "MECHANICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"technician_id": "TECH-MECH-02", "technician_name": "Mechanical Technician 02", "team_name": "Mechanical Reliability", "skill_group": "MECHANICAL", "shift": "SWING", "active_status": "ACTIVE"},
        {"technician_id": "TECH-MECH-03", "technician_name": "Mechanical Technician 03", "team_name": "Utilities Maintenance", "skill_group": "MECHANICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"technician_id": "TECH-ELEC-01", "technician_name": "Electrical Technician 01", "team_name": "Controls Maintenance", "skill_group": "ELECTRICAL", "shift": "DAY", "active_status": "ACTIVE"},
        {"technician_id": "TECH-ELEC-02", "technician_name": "Electrical Technician 02", "team_name": "Controls Maintenance", "skill_group": "ELECTRICAL", "shift": "NIGHT", "active_status": "ACTIVE"},
        {"technician_id": "TECH-QA-01", "technician_name": "Maintenance Inspector 01", "team_name": "Maintenance QA", "skill_group": "INSPECTION", "shift": "DAY", "active_status": "ACTIVE"},
    ]
    parts = [
        {"part_id": "PART-BEARING-6205", "part_number": "BRG-6205", "part_name": "Conveyor Bearing 6205", "part_category": "BEARING", "stock_status": "IN_STOCK", "lead_time_days": 1, "critical_spare": False},
        {"part_id": "PART-HYD-SEAL", "part_number": "HYD-SEAL-44", "part_name": "Hydraulic Seal Kit", "part_category": "HYDRAULIC", "stock_status": "LOW_STOCK", "lead_time_days": 3, "critical_spare": True},
        {"part_id": "PART-ENCODER-RBT", "part_number": "ENC-RBT-X4", "part_name": "Robot Axis Encoder", "part_category": "ELECTRONICS", "stock_status": "IN_STOCK", "lead_time_days": 2, "critical_spare": True},
        {"part_id": "PART-SERVO-7KW", "part_number": "SRV-7KW", "part_name": "7kW Servo Motor", "part_category": "MOTOR", "stock_status": "OUT_OF_STOCK", "lead_time_days": 14, "critical_spare": True},
        {"part_id": "PART-PUMP-SEAL", "part_number": "PMP-SEAL-20", "part_name": "Pump Mechanical Seal", "part_category": "PUMP", "stock_status": "IN_STOCK", "lead_time_days": 2, "critical_spare": True},
        {"part_id": "PART-SAFETY-RELAY", "part_number": "SFR-24V", "part_name": "Safety Relay", "part_category": "SAFETY", "stock_status": "LOW_STOCK", "lead_time_days": 5, "critical_spare": True},
        {"part_id": "PART-FILTER-CMP", "part_number": "CMP-FLTR-9", "part_name": "Compressor Intake Filter", "part_category": "FILTER", "stock_status": "OUT_OF_STOCK", "lead_time_days": 7, "critical_spare": True},
        {"part_id": "PART-BELT-GUIDE", "part_number": "BLT-GDE-2", "part_name": "Belt Guide Assembly", "part_category": "CONVEYOR", "stock_status": "IN_STOCK", "lead_time_days": 2, "critical_spare": False},
        {"part_id": "PART-LABEL-SENSOR", "part_number": "LBL-SNS-01", "part_name": "Label Photoeye Sensor", "part_category": "SENSOR", "stock_status": "LOW_STOCK", "lead_time_days": 4, "critical_spare": False},
        {"part_id": "PART-MOTOR-MOUNT", "part_number": "MTR-MNT-88", "part_name": "Mixer Motor Mount", "part_category": "MECHANICAL", "stock_status": "IN_STOCK", "lead_time_days": 1, "critical_spare": False},
    ]
    return {
        "production_lines": production_lines,
        "equipment": equipment,
        "technicians": technicians,
        "parts": parts,
    }


def _build_stage_events(
    request_id: str,
    profile: Any,
    submitted_at: datetime,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    current_time = submitted_at

    for stage in STAGE_FLOW:
        if not _stage_reached(profile, stage):
            break

        events.append(
            _stage_event_payload(
                request_id=request_id,
                sequence=len(events) + 1,
                stage=stage,
                event_type="ENTERED_STAGE",
                event_status="SUCCESS",
                occurred_at=current_time,
                reason_code=None,
            )
        )

        if stage == "PROCUREMENT_REVIEW" and profile.correction_in_procurement_review:
            correction_time = current_time + timedelta(hours=24)
            events.append(
                _stage_event_payload(
                    request_id=request_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="RETURNED_FOR_CORRECTION",
                    event_status="ACTION_REQUIRED",
                    occurred_at=correction_time,
                    reason_code="MISSING_SPECIFICATION",
                )
            )

        if stage == "INSPECTION" and profile.inspection_failed_once:
            failed_time = current_time + timedelta(hours=12)
            events.append(
                _stage_event_payload(
                    request_id=request_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="INSPECTION_FAILED",
                    event_status="ACTION_REQUIRED",
                    occurred_at=failed_time,
                    reason_code="SAMPLE_VALIDATION_FAILED",
                )
            )

        if profile.stop_stage == stage:
            break

        if stage == "CLOSED":
            events.append(
                _stage_event_payload(
                    request_id=request_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="CLOSED",
                    event_status="SUCCESS",
                    occurred_at=current_time,
                    reason_code=None,
                )
            )
            break

        duration = profile.stage_durations_hours.get(stage, 4)
        current_time = current_time + timedelta(hours=duration)
        events.append(
            _stage_event_payload(
                request_id=request_id,
                sequence=len(events) + 1,
                stage=stage,
                event_type=EXIT_EVENT_BY_STAGE[stage],
                event_status="SUCCESS",
                occurred_at=current_time,
                reason_code=None,
            )
        )

    return events


def _build_maintenance_stage_events(
    request_id: str,
    profile: Any,
    reported_at: datetime,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    current_time = reported_at

    for stage in MAINTENANCE_STAGE_FLOW:
        if not _maintenance_stage_reached(profile, stage):
            break

        events.append(
            _maintenance_stage_event_payload(
                request_id=request_id,
                sequence=len(events) + 1,
                stage=stage,
                event_type="ENTERED_STAGE",
                event_status="SUCCESS",
                occurred_at=current_time,
                reason_code=None,
            )
        )

        if stage == "INSPECTION" and profile.inspection_failed_once:
            failed_time = current_time + timedelta(hours=6)
            events.append(
                _maintenance_stage_event_payload(
                    request_id=request_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="INSPECTION_FAILED",
                    event_status="ACTION_REQUIRED",
                    occurred_at=failed_time,
                    reason_code="REPAIR_VALIDATION_FAILED",
                )
            )

        if profile.stop_stage == stage:
            break

        if stage == "COMPLETED":
            events.append(
                _maintenance_stage_event_payload(
                    request_id=request_id,
                    sequence=len(events) + 1,
                    stage=stage,
                    event_type="REQUEST_COMPLETED",
                    event_status="SUCCESS",
                    occurred_at=current_time,
                    reason_code=None,
                )
            )
            break

        duration = profile.stage_durations_hours.get(stage, 4)
        current_time = current_time + timedelta(hours=duration)
        events.append(
            _maintenance_stage_event_payload(
                request_id=request_id,
                sequence=len(events) + 1,
                stage=stage,
                event_type=MAINTENANCE_EXIT_EVENT_BY_STAGE[stage],
                event_status="SUCCESS",
                occurred_at=current_time,
                reason_code=None,
            )
        )

    return events


def _inject_quality_issue_records(
    purchase_requests: list[dict[str, Any]],
    stage_events: list[dict[str, Any]],
    base_time: datetime,
) -> list[dict[str, str]]:
    issues = []

    duplicate_record = deepcopy(purchase_requests[0])
    duplicate_record["payload"]["request_id"] = "REQ-QA-DUPLICATE"
    duplicate_record["payload"]["scenario_key"] = "qa_duplicate_source_record"
    purchase_requests.append(duplicate_record)
    issues.append({"check_name": "duplicate_source_record", "target_file": "purchase_requests.json"})

    missing_required_field = _source_record(
        record_type="purchase_request",
        record_id="REQ-QA-MISSING-FIELD",
        payload={
            "request_id": "REQ-QA-MISSING-FIELD",
            "request_number": "PR-2026-QA-MISSING",
            "department_id": "DEPT-IT",
            "requester_id": "USR-IT-01",
            "item_id": "ITEM-MONITOR",
            "scenario_key": "qa_missing_required_field",
        },
    )
    purchase_requests.append(missing_required_field)
    issues.append({"check_name": "missing_required_fields", "target_file": "purchase_requests.json"})

    missing_stage_request = _source_record(
        record_type="purchase_request",
        record_id="REQ-QA-NO-STAGE",
        payload={
            "request_id": "REQ-QA-NO-STAGE",
            "request_number": "PR-2026-QA-NO-STAGE",
            "request_title": "Request missing all stage events",
            "request_type": "STANDARD",
            "department_id": "DEPT-OPS",
            "requester_id": "USR-OPS-01",
            "item_id": "ITEM-HANDHELD-SCANNER",
            "quantity": 1,
            "estimated_amount": 1500,
            "currency": "USD",
            "criticality_level": "LOW",
            "business_impact": "DATA_QUALITY_TEST",
            "needed_by_date": (base_time.date()).isoformat(),
            "submitted_at": _iso(base_time),
            "current_stage": "REQUEST_SUBMITTED",
            "current_status": "IN_PROGRESS",
            "scenario_key": "qa_request_without_stage_event",
        },
    )
    purchase_requests.append(missing_stage_request)
    issues.append({"check_name": "request_without_stage_event", "target_file": "stage_events.json"})

    out_of_order_event = _source_record(
        record_type="stage_event",
        record_id="EVT-QA-OUT-OF-ORDER",
        payload=_stage_event_payload(
            request_id="REQ-0001",
            sequence=999,
            stage="BUDGET_REVIEW",
            event_type="APPROVED",
            event_status="SUCCESS",
            occurred_at=base_time - timedelta(days=10),
            reason_code="QA_OUT_OF_ORDER",
        ),
    )
    stage_events.append(out_of_order_event)
    issues.append({"check_name": "event_timestamp_out_of_order", "target_file": "stage_events.json"})

    return issues


def _inject_maintenance_quality_issue_records(
    maintenance_requests: list[dict[str, Any]],
    maintenance_stage_events: list[dict[str, Any]],
    maintenance_work_orders: list[dict[str, Any]],
    inspection_results: list[dict[str, Any]],
    base_time: datetime,
) -> list[dict[str, str]]:
    issues = []

    duplicate_record = deepcopy(maintenance_requests[0])
    duplicate_record["payload"]["maintenance_request_id"] = "MREQ-QA-DUPLICATE"
    duplicate_record["payload"]["scenario_key"] = "qa_maintenance_duplicate_source_record"
    maintenance_requests.append(duplicate_record)
    issues.append({"check_name": "duplicate_source_record", "target_file": "maintenance_requests.json"})

    maintenance_requests.append(
        _maintenance_source_record(
            record_type="maintenance_request",
            record_id="MREQ-QA-MISSING-FIELD",
            payload={
                "maintenance_request_id": "MREQ-QA-MISSING-FIELD",
                "request_number": "MR-2026-QA-MISSING",
                "equipment_id": "EQ-CNV-001",
                "scenario_key": "qa_maintenance_missing_required_field",
            },
        )
    )
    issues.append({"check_name": "missing_required_fields", "target_file": "maintenance_requests.json"})

    maintenance_requests.append(
        _maintenance_source_record(
            record_type="maintenance_request",
            record_id="MREQ-QA-NO-STAGE",
            payload={
                "maintenance_request_id": "MREQ-QA-NO-STAGE",
                "request_number": "MR-2026-QA-NO-STAGE",
                "equipment_id": "EQ-CNV-001",
                "line_id": "LINE-ASM-01",
                "request_title": "Maintenance request missing stage events",
                "request_type": "CORRECTIVE",
                "priority_level": "LOW",
                "failure_mode": "DATA_QUALITY_TEST",
                "reported_at": _iso(base_time),
                "needed_by_at": _iso(base_time + timedelta(hours=24)),
                "current_stage": "MAINTENANCE_REQUEST_SUBMITTED",
                "current_status": "IN_PROGRESS",
                "business_impact": "DATA_QUALITY_TEST",
                "estimated_downtime_hours": 1,
                "actual_downtime_hours": None,
                "scenario_key": "qa_maintenance_request_without_stage_event",
            },
        )
    )
    issues.append({"check_name": "maintenance_request_without_stage_event", "target_file": "maintenance_stage_events.json"})

    maintenance_stage_events.append(
        _maintenance_source_record(
            record_type="maintenance_stage_event",
            record_id="MEVT-QA-OUT-OF-ORDER",
            payload=_maintenance_stage_event_payload(
                request_id="MREQ-0001",
                sequence=999,
                stage="MAINTENANCE_REVIEW",
                event_type="REVIEW_APPROVED",
                event_status="SUCCESS",
                occurred_at=base_time - timedelta(days=10),
                reason_code="QA_OUT_OF_ORDER",
            ),
        )
    )
    issues.append({"check_name": "stage_event_timestamp_out_of_order", "target_file": "maintenance_stage_events.json"})

    maintenance_work_orders.append(
        _maintenance_source_record(
            record_type="maintenance_work_order",
            record_id="MWO-QA-NO-PART",
            payload={
                "work_order_id": "MWO-QA-NO-PART",
                "maintenance_request_id": "MREQ-0004",
                "assigned_team": "Controls Maintenance",
                "assigned_technician_id": "TECH-ELEC-01",
                "work_order_status": "WAITING_PARTS",
                "planned_start_at": None,
                "actual_start_at": None,
                "actual_completed_at": None,
                "required_part_id": None,
                "scenario_key": "qa_parts_waiting_without_required_part",
            },
        )
    )
    issues.append({"check_name": "parts_waiting_without_required_part", "target_file": "maintenance_work_orders.json"})

    inspection_results.append(
        _maintenance_source_record(
            record_type="inspection_result",
            record_id="INSP-QA-NO-WORK",
            payload={
                "inspection_id": "INSP-QA-NO-WORK",
                "maintenance_request_id": "MREQ-0002",
                "inspection_status": "PASSED",
                "inspector_id": "TECH-QA-01",
                "inspection_started_at": _iso(base_time + timedelta(hours=1)),
                "inspection_completed_at": _iso(base_time + timedelta(hours=2)),
                "failure_reason": None,
                "scenario_key": "qa_inspection_without_completed_work",
            },
        )
    )
    issues.append({"check_name": "inspection_without_completed_work", "target_file": "inspection_results.json"})

    return issues


def _source_record(record_type: str, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": SOURCE_SYSTEM,
        "source_record_id": f"SRC-{record_type.upper()}-{record_id}",
        "payload": payload,
    }


def _maintenance_source_record(record_type: str, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": MAINTENANCE_SOURCE_SYSTEM,
        "source_record_id": f"SRC-{record_type.upper()}-{record_id}",
        "payload": payload,
    }


def _stage_event_payload(
    request_id: str,
    sequence: int,
    stage: str,
    event_type: str,
    event_status: str,
    occurred_at: datetime,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "event_id": f"EVT-{request_id}-{sequence:03d}",
        "request_id": request_id,
        "stage": stage,
        "event_type": event_type,
        "event_status": event_status,
        "occurred_at": _iso(occurred_at),
        "actor_type": _actor_type_for_stage(stage),
        "actor_id": _actor_id_for_stage(stage),
        "reason_code": reason_code,
        "metadata_json": {},
        "source_system": SOURCE_SYSTEM,
    }


def _maintenance_stage_event_payload(
    request_id: str,
    sequence: int,
    stage: str,
    event_type: str,
    event_status: str,
    occurred_at: datetime,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "event_id": f"MEVT-{request_id}-{sequence:03d}",
        "maintenance_request_id": request_id,
        "stage": stage,
        "event_type": event_type,
        "event_status": event_status,
        "occurred_at": _iso(occurred_at),
        "actor_type": _maintenance_actor_type_for_stage(stage),
        "actor_id": _maintenance_actor_id_for_stage(stage),
        "reason_code": reason_code,
        "metadata_json": {},
        "source_system": MAINTENANCE_SOURCE_SYSTEM,
    }


def _stage_reached(profile: Any, stage: str) -> bool:
    if profile.stop_stage is None:
        return True
    return STAGE_FLOW.index(stage) <= STAGE_FLOW.index(profile.stop_stage)


def _current_stage(profile: Any) -> str:
    return profile.stop_stage or "CLOSED"


def _maintenance_stage_reached(profile: Any, stage: str) -> bool:
    if profile.stop_stage is None:
        return True
    return MAINTENANCE_STAGE_FLOW.index(stage) <= MAINTENANCE_STAGE_FLOW.index(profile.stop_stage)


def _current_maintenance_stage(profile: Any) -> str:
    return profile.stop_stage or "COMPLETED"


def _event_time(events: list[dict[str, Any]], stage: str, event_type: str) -> datetime | None:
    for event in events:
        if event["stage"] == stage and event["event_type"] == event_type:
            return datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    return None


def _maintenance_event_time(events: list[dict[str, Any]], stage: str, event_type: str) -> datetime | None:
    for event in events:
        if event["stage"] == stage and event["event_type"] == event_type:
            return datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    return None


def _maintenance_master_by_id(records: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for record in records:
        if record[key] == value:
            return record
    raise KeyError(value)


def _maintenance_team_for_technician(technician_id: str | None) -> str:
    return {
        "TECH-MECH-01": "Mechanical Reliability",
        "TECH-MECH-02": "Mechanical Reliability",
        "TECH-MECH-03": "Utilities Maintenance",
        "TECH-ELEC-01": "Controls Maintenance",
        "TECH-ELEC-02": "Controls Maintenance",
        "TECH-QA-01": "Maintenance QA",
        None: "Unassigned",
    }[technician_id]


def _maintenance_work_order_status(profile: Any) -> str:
    if profile.stop_stage == "TECHNICIAN_ASSIGNED":
        return "ASSIGNMENT_PENDING"
    if profile.stop_stage == "PARTS_WAITING":
        return "WAITING_PARTS"
    if profile.stop_stage == "MAINTENANCE_IN_PROGRESS":
        return "IN_PROGRESS"
    if profile.stop_stage == "INSPECTION":
        return "WORK_COMPLETED"
    return "COMPLETED"


def _vendor_lead_days(vendor_id: str) -> int:
    return {
        "VEN-NOVA": 4,
        "VEN-APEX": 5,
        "VEN-ORBIT": 7,
        "VEN-SIGNAL": 3,
        "VEN-HARBOR": 4,
    }[vendor_id]


def _vendor_message(scenario_key: str) -> str:
    if "vendor_confirmation_delay" in scenario_key or "critical_request_delayed" in scenario_key:
        return "Vendor has not confirmed availability within expected threshold."
    if "delivery_delay" in scenario_key:
        return "Vendor reported delivery risk due to stock transfer delay."
    return "Vendor update received."


def _actor_type_for_stage(stage: str) -> str:
    return {
        "REQUEST_SUBMITTED": "REQUESTER",
        "BUDGET_REVIEW": "BUDGET_OWNER",
        "PROCUREMENT_REVIEW": "PROCUREMENT_OPERATOR",
        "PO_CREATION": "PROCUREMENT_OPERATOR",
        "VENDOR_CONFIRMATION": "VENDOR",
        "DELIVERY": "VENDOR",
        "RECEIVING": "WAREHOUSE_OPERATOR",
        "INSPECTION": "INSPECTION_OPERATOR",
        "CLOSED": "SYSTEM",
    }[stage]


def _actor_id_for_stage(stage: str) -> str:
    return {
        "REQUEST_SUBMITTED": "REQUESTER",
        "BUDGET_REVIEW": "BUDGET-TEAM",
        "PROCUREMENT_REVIEW": "PROC-TEAM",
        "PO_CREATION": "PROC-TEAM",
        "VENDOR_CONFIRMATION": "VENDOR",
        "DELIVERY": "VENDOR",
        "RECEIVING": "WAREHOUSE",
        "INSPECTION": "QA-TEAM",
        "CLOSED": "SYSTEM",
    }[stage]


def _maintenance_actor_type_for_stage(stage: str) -> str:
    return {
        "MAINTENANCE_REQUEST_SUBMITTED": "REQUESTER",
        "MAINTENANCE_REVIEW": "MAINTENANCE_PLANNER",
        "TECHNICIAN_ASSIGNED": "SUPERVISOR",
        "PARTS_WAITING": "STOREROOM",
        "MAINTENANCE_IN_PROGRESS": "TECHNICIAN",
        "INSPECTION": "INSPECTOR",
        "COMPLETED": "SYSTEM",
    }[stage]


def _maintenance_actor_id_for_stage(stage: str) -> str:
    return {
        "MAINTENANCE_REQUEST_SUBMITTED": "LINE-SUPERVISOR",
        "MAINTENANCE_REVIEW": "MAINT-PLANNER",
        "TECHNICIAN_ASSIGNED": "MAINT-SUPERVISOR",
        "PARTS_WAITING": "STOREROOM",
        "MAINTENANCE_IN_PROGRESS": "TECHNICIAN",
        "INSPECTION": "TECH-QA-01",
        "COMPLETED": "SYSTEM",
    }[stage]


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _iso_or_none(value: datetime | None) -> str | None:
    return _iso(value) if value else None


if __name__ == "__main__":
    main()
