from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import (
    Department,
    Item,
    ProcurementStageEvent,
    PurchaseOrder,
    PurchaseRequest,
    Receipt,
    Requester,
    Vendor,
)
from app.models.maintenance import (
    Equipment,
    InspectionResult,
    MaintenanceRequest,
    MaintenanceStageEvent,
    MaintenanceWorkOrder,
    Part,
    ProductionLine,
    SensorAlert,
    Technician,
)
from app.models.raw import (
    RawInspectionResult,
    RawMaintenanceRequest,
    RawMaintenanceStageEvent,
    RawMaintenanceWorkOrder,
    RawPurchaseOrder,
    RawPurchaseRequest,
    RawReceipt,
    RawSensorAlert,
    RawStageEvent,
)
from app.pipeline.quality import MAINTENANCE_REQUIRED_PAYLOAD_FIELDS, REQUIRED_PAYLOAD_FIELDS


@dataclass(frozen=True)
class CoreTransformResult:
    departments_loaded: int
    requesters_loaded: int
    items_loaded: int
    vendors_loaded: int
    purchase_requests_loaded: int
    purchase_orders_loaded: int
    receipts_loaded: int
    stage_events_loaded: int
    records_skipped: int


@dataclass(frozen=True)
class MaintenanceCoreTransformResult:
    production_lines_loaded: int
    equipment_loaded: int
    technicians_loaded: int
    parts_loaded: int
    maintenance_requests_loaded: int
    maintenance_stage_events_loaded: int
    maintenance_work_orders_loaded: int
    inspection_results_loaded: int
    sensor_alerts_loaded: int
    records_skipped: int


def transform_raw_to_core(session: Session, sample_dir: Path) -> CoreTransformResult:
    skipped = 0
    masters = _load_master_records(sample_dir)

    departments_loaded = _merge_departments(session, masters["departments"])
    requesters_loaded = _merge_requesters(session, masters["requesters"])
    items_loaded = _merge_items(session, masters["items"])
    vendors_loaded = _merge_vendors(session, masters["vendors"])
    session.flush()

    valid_department_ids = _id_set(session, Department.department_id)
    valid_requester_ids = _id_set(session, Requester.requester_id)
    valid_item_ids = _id_set(session, Item.item_id)
    valid_vendor_ids = _id_set(session, Vendor.vendor_id)

    purchase_requests_loaded = 0
    for raw_record in session.scalars(select(RawPurchaseRequest)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_purchase_requests", payload):
            skipped += 1
            continue
        if (
            payload["department_id"] not in valid_department_ids
            or payload["requester_id"] not in valid_requester_ids
            or payload["item_id"] not in valid_item_ids
        ):
            skipped += 1
            continue
        session.merge(_purchase_request_from_payload(payload))
        purchase_requests_loaded += 1
    session.flush()

    valid_request_ids = _id_set(session, PurchaseRequest.request_id)

    purchase_orders_loaded = 0
    for raw_record in session.scalars(select(RawPurchaseOrder)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_purchase_orders", payload):
            skipped += 1
            continue
        if payload["request_id"] not in valid_request_ids or payload["vendor_id"] not in valid_vendor_ids:
            skipped += 1
            continue
        session.merge(_purchase_order_from_payload(payload))
        purchase_orders_loaded += 1
    session.flush()

    valid_po_ids = _id_set(session, PurchaseOrder.po_id)

    receipts_loaded = 0
    for raw_record in session.scalars(select(RawReceipt)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_receipts", payload):
            skipped += 1
            continue
        if payload["po_id"] not in valid_po_ids:
            skipped += 1
            continue
        session.merge(_receipt_from_payload(payload))
        receipts_loaded += 1

    stage_events_loaded = 0
    for raw_record in session.scalars(select(RawStageEvent)):
        payload = raw_record.payload_json
        if not _has_required_fields("raw_stage_events", payload):
            skipped += 1
            continue
        if payload["request_id"] not in valid_request_ids:
            skipped += 1
            continue
        session.merge(_stage_event_from_payload(payload))
        stage_events_loaded += 1

    session.flush()
    return CoreTransformResult(
        departments_loaded=departments_loaded,
        requesters_loaded=requesters_loaded,
        items_loaded=items_loaded,
        vendors_loaded=vendors_loaded,
        purchase_requests_loaded=purchase_requests_loaded,
        purchase_orders_loaded=purchase_orders_loaded,
        receipts_loaded=receipts_loaded,
        stage_events_loaded=stage_events_loaded,
        records_skipped=skipped,
    )


def transform_maintenance_raw_to_core(session: Session, sample_dir: Path) -> MaintenanceCoreTransformResult:
    skipped = 0
    masters = _load_maintenance_master_records(sample_dir)

    production_lines_loaded = _merge_production_lines(session, masters["production_lines"])
    equipment_loaded = _merge_equipment(session, masters["equipment"])
    technicians_loaded = _merge_technicians(session, masters["technicians"])
    parts_loaded = _merge_parts(session, masters["parts"])
    session.flush()

    valid_line_ids = _id_set(session, ProductionLine.line_id)
    valid_equipment_ids = _id_set(session, Equipment.equipment_id)
    valid_technician_ids = _id_set(session, Technician.technician_id)
    valid_part_ids = _id_set(session, Part.part_id)

    maintenance_requests_loaded = 0
    for raw_record in session.scalars(select(RawMaintenanceRequest)):
        payload = raw_record.payload_json
        if not _has_maintenance_required_fields("raw_maintenance_requests", payload):
            skipped += 1
            continue
        if payload["equipment_id"] not in valid_equipment_ids or payload["line_id"] not in valid_line_ids:
            skipped += 1
            continue
        session.merge(_maintenance_request_from_payload(payload))
        maintenance_requests_loaded += 1
    session.flush()

    valid_maintenance_request_ids = _id_set(session, MaintenanceRequest.maintenance_request_id)

    maintenance_stage_events_loaded = 0
    for raw_record in session.scalars(select(RawMaintenanceStageEvent)):
        payload = raw_record.payload_json
        if not _has_maintenance_required_fields("raw_maintenance_stage_events", payload):
            skipped += 1
            continue
        if payload["maintenance_request_id"] not in valid_maintenance_request_ids:
            skipped += 1
            continue
        session.merge(_maintenance_stage_event_from_payload(payload))
        maintenance_stage_events_loaded += 1

    maintenance_work_orders_loaded = 0
    for raw_record in session.scalars(select(RawMaintenanceWorkOrder)):
        payload = raw_record.payload_json
        if not _has_maintenance_required_fields("raw_maintenance_work_orders", payload):
            skipped += 1
            continue
        if payload["maintenance_request_id"] not in valid_maintenance_request_ids:
            skipped += 1
            continue
        if payload.get("assigned_technician_id") and payload["assigned_technician_id"] not in valid_technician_ids:
            skipped += 1
            continue
        if payload.get("required_part_id") and payload["required_part_id"] not in valid_part_ids:
            skipped += 1
            continue
        session.merge(_maintenance_work_order_from_payload(payload))
        maintenance_work_orders_loaded += 1

    inspection_results_loaded = 0
    for raw_record in session.scalars(select(RawInspectionResult)):
        payload = raw_record.payload_json
        if not _has_maintenance_required_fields("raw_inspection_results", payload):
            skipped += 1
            continue
        if payload["maintenance_request_id"] not in valid_maintenance_request_ids:
            skipped += 1
            continue
        if payload.get("inspector_id") and payload["inspector_id"] not in valid_technician_ids:
            skipped += 1
            continue
        session.merge(_inspection_result_from_payload(payload))
        inspection_results_loaded += 1

    sensor_alerts_loaded = 0
    for raw_record in session.scalars(select(RawSensorAlert)):
        payload = raw_record.payload_json
        if not _has_maintenance_required_fields("raw_sensor_alerts", payload):
            skipped += 1
            continue
        if payload["equipment_id"] not in valid_equipment_ids:
            skipped += 1
            continue
        if (
            payload.get("linked_maintenance_request_id")
            and payload["linked_maintenance_request_id"] not in valid_maintenance_request_ids
        ):
            skipped += 1
            continue
        session.merge(_sensor_alert_from_payload(payload))
        sensor_alerts_loaded += 1

    session.flush()
    return MaintenanceCoreTransformResult(
        production_lines_loaded=production_lines_loaded,
        equipment_loaded=equipment_loaded,
        technicians_loaded=technicians_loaded,
        parts_loaded=parts_loaded,
        maintenance_requests_loaded=maintenance_requests_loaded,
        maintenance_stage_events_loaded=maintenance_stage_events_loaded,
        maintenance_work_orders_loaded=maintenance_work_orders_loaded,
        inspection_results_loaded=inspection_results_loaded,
        sensor_alerts_loaded=sensor_alerts_loaded,
        records_skipped=skipped,
    )


def _load_master_records(sample_dir: Path) -> dict[str, list[dict[str, Any]]]:
    master_names = ["departments", "requesters", "items", "vendors"]
    records = {}
    for name in master_names:
        path = sample_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing master data file: {path}")
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise ValueError(f"Expected list records in {path}")
        records[name] = loaded
    return records


def _load_maintenance_master_records(sample_dir: Path) -> dict[str, list[dict[str, Any]]]:
    master_names = ["production_lines", "equipment", "technicians", "parts"]
    records = {}
    for name in master_names:
        path = sample_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing maintenance master data file: {path}")
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise ValueError(f"Expected list records in {path}")
        records[name] = loaded
    return records


def _merge_departments(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Department(
                department_id=record["department_id"],
                department_name=record["department_name"],
                department_type=record["department_type"],
                cost_center=record["cost_center"],
            )
        )
    return len(records)


def _merge_requesters(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Requester(
                requester_id=record["requester_id"],
                requester_name=record["requester_name"],
                department_id=record["department_id"],
                role=record["role"],
            )
        )
    return len(records)


def _merge_items(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Item(
                item_id=record["item_id"],
                item_name=record["item_name"],
                item_category=record["item_category"],
                is_critical_item=record["is_critical_item"],
                standard_lead_time_days=record["standard_lead_time_days"],
            )
        )
    return len(records)


def _merge_vendors(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Vendor(
                vendor_id=record["vendor_id"],
                vendor_name=record["vendor_name"],
                vendor_type=record["vendor_type"],
                reliability_tier=record["reliability_tier"],
                default_lead_time_days=record["default_lead_time_days"],
            )
        )
    return len(records)


def _merge_production_lines(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            ProductionLine(
                line_id=record["line_id"],
                line_code=record["line_code"],
                line_name=record["line_name"],
                plant_area=record["plant_area"],
                line_priority=record["line_priority"],
                current_status=record["current_status"],
            )
        )
    return len(records)


def _merge_equipment(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Equipment(
                equipment_id=record["equipment_id"],
                equipment_code=record["equipment_code"],
                equipment_name=record["equipment_name"],
                equipment_type=record["equipment_type"],
                line_id=record["line_id"],
                criticality_level=record["criticality_level"],
                installed_at=_parse_datetime(record["installed_at"]),
                manufacturer=record["manufacturer"],
                model_number=record["model_number"],
                current_status=record["current_status"],
            )
        )
    return len(records)


def _merge_technicians(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Technician(
                technician_id=record["technician_id"],
                technician_name=record["technician_name"],
                team_name=record["team_name"],
                skill_group=record["skill_group"],
                shift=record["shift"],
                active_status=record["active_status"],
            )
        )
    return len(records)


def _merge_parts(session: Session, records: list[dict[str, Any]]) -> int:
    for record in records:
        session.merge(
            Part(
                part_id=record["part_id"],
                part_number=record["part_number"],
                part_name=record["part_name"],
                part_category=record["part_category"],
                stock_status=record["stock_status"],
                lead_time_days=float(record["lead_time_days"]),
                critical_spare=record["critical_spare"],
            )
        )
    return len(records)


def _purchase_request_from_payload(payload: dict[str, Any]) -> PurchaseRequest:
    return PurchaseRequest(
        request_id=payload["request_id"],
        request_number=payload["request_number"],
        request_title=payload["request_title"],
        request_type=payload["request_type"],
        department_id=payload["department_id"],
        requester_id=payload["requester_id"],
        item_id=payload["item_id"],
        quantity=int(payload["quantity"]),
        estimated_amount=float(payload["estimated_amount"]),
        currency=payload["currency"],
        criticality_level=payload["criticality_level"],
        business_impact=payload["business_impact"],
        needed_by_date=_parse_date(payload["needed_by_date"]),
        submitted_at=_parse_datetime(payload["submitted_at"]),
        current_stage=payload["current_stage"],
        current_status=payload["current_status"],
    )


def _purchase_order_from_payload(payload: dict[str, Any]) -> PurchaseOrder:
    return PurchaseOrder(
        po_id=payload["po_id"],
        po_number=payload["po_number"],
        request_id=payload["request_id"],
        vendor_id=payload["vendor_id"],
        po_created_at=_parse_optional_datetime(payload.get("po_created_at")),
        vendor_confirmed_at=_parse_optional_datetime(payload.get("vendor_confirmed_at")),
        expected_delivery_date=_parse_optional_date(payload.get("expected_delivery_date")),
        actual_delivery_date=_parse_optional_date(payload.get("actual_delivery_date")),
        po_status=payload["po_status"],
    )


def _receipt_from_payload(payload: dict[str, Any]) -> Receipt:
    return Receipt(
        receipt_id=payload["receipt_id"],
        po_id=payload["po_id"],
        received_at=_parse_optional_datetime(payload.get("received_at")),
        received_quantity=int(payload["received_quantity"]),
        inspection_status=payload["inspection_status"],
        inspection_completed_at=_parse_optional_datetime(payload.get("inspection_completed_at")),
        rejection_reason=payload.get("rejection_reason"),
    )


def _stage_event_from_payload(payload: dict[str, Any]) -> ProcurementStageEvent:
    return ProcurementStageEvent(
        event_id=payload["event_id"],
        request_id=payload["request_id"],
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


def _maintenance_request_from_payload(payload: dict[str, Any]) -> MaintenanceRequest:
    return MaintenanceRequest(
        maintenance_request_id=payload["maintenance_request_id"],
        request_number=payload["request_number"],
        equipment_id=payload["equipment_id"],
        line_id=payload["line_id"],
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


def _maintenance_stage_event_from_payload(payload: dict[str, Any]) -> MaintenanceStageEvent:
    return MaintenanceStageEvent(
        event_id=payload["event_id"],
        maintenance_request_id=payload["maintenance_request_id"],
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


def _maintenance_work_order_from_payload(payload: dict[str, Any]) -> MaintenanceWorkOrder:
    return MaintenanceWorkOrder(
        work_order_id=payload["work_order_id"],
        maintenance_request_id=payload["maintenance_request_id"],
        assigned_team=payload["assigned_team"],
        assigned_technician_id=payload.get("assigned_technician_id"),
        work_order_status=payload["work_order_status"],
        planned_start_at=_parse_optional_datetime(payload.get("planned_start_at")),
        actual_start_at=_parse_optional_datetime(payload.get("actual_start_at")),
        actual_completed_at=_parse_optional_datetime(payload.get("actual_completed_at")),
        required_part_id=payload.get("required_part_id"),
    )


def _inspection_result_from_payload(payload: dict[str, Any]) -> InspectionResult:
    return InspectionResult(
        inspection_id=payload["inspection_id"],
        maintenance_request_id=payload["maintenance_request_id"],
        inspection_status=payload["inspection_status"],
        inspector_id=payload.get("inspector_id"),
        inspection_started_at=_parse_optional_datetime(payload.get("inspection_started_at")),
        inspection_completed_at=_parse_optional_datetime(payload.get("inspection_completed_at")),
        failure_reason=payload.get("failure_reason"),
    )


def _sensor_alert_from_payload(payload: dict[str, Any]) -> SensorAlert:
    return SensorAlert(
        sensor_alert_id=payload["sensor_alert_id"],
        equipment_id=payload["equipment_id"],
        alert_type=payload["alert_type"],
        severity=payload["severity"],
        triggered_at=_parse_datetime(payload["triggered_at"]),
        resolved_at=_parse_optional_datetime(payload.get("resolved_at")),
        linked_maintenance_request_id=payload.get("linked_maintenance_request_id"),
        metadata_json=payload.get("metadata_json"),
    )


def _has_required_fields(target_table: str, payload: dict[str, Any]) -> bool:
    return all(payload.get(field) not in (None, "") for field in REQUIRED_PAYLOAD_FIELDS[target_table])


def _has_maintenance_required_fields(target_table: str, payload: dict[str, Any]) -> bool:
    return all(payload.get(field) not in (None, "") for field in MAINTENANCE_REQUIRED_PAYLOAD_FIELDS[target_table])


def _id_set(session: Session, column) -> set[Any]:
    return {row[0] for row in session.execute(select(column))}


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_optional_datetime(value: str | None) -> datetime | None:
    return _parse_datetime(value) if value else None


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_optional_date(value: str | None) -> date | None:
    return _parse_date(value) if value else None


def _parse_optional_float(value: Any | None) -> float | None:
    return float(value) if value is not None else None
