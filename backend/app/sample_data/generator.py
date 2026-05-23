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


def _source_record(record_type: str, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": SOURCE_SYSTEM,
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


def _stage_reached(profile: Any, stage: str) -> bool:
    if profile.stop_stage is None:
        return True
    return STAGE_FLOW.index(stage) <= STAGE_FLOW.index(profile.stop_stage)


def _current_stage(profile: Any) -> str:
    return profile.stop_stage or "CLOSED"


def _event_time(events: list[dict[str, Any]], stage: str, event_type: str) -> datetime | None:
    for event in events:
        if event["stage"] == stage and event["event_type"] == event_type:
            return datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
    return None


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


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _iso_or_none(value: datetime | None) -> str | None:
    return _iso(value) if value else None


if __name__ == "__main__":
    main()
