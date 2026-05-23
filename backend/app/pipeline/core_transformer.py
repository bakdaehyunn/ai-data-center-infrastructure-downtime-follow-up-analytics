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
from app.models.raw import RawPurchaseOrder, RawPurchaseRequest, RawReceipt, RawStageEvent
from app.pipeline.quality import REQUIRED_PAYLOAD_FIELDS


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


def _has_required_fields(target_table: str, payload: dict[str, Any]) -> bool:
    return all(payload.get(field) not in (None, "") for field in REQUIRED_PAYLOAD_FIELDS[target_table])


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
