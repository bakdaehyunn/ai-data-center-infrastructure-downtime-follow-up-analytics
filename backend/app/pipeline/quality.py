from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ProcurementStageEvent, PurchaseOrder, PurchaseRequest, Receipt
from app.models.ops import DataQualityCheckResult
from app.pipeline.raw_loader import RAW_SOURCE_SPECS
from app.sample_data.scenarios import SOURCE_SYSTEM


REQUIRED_PAYLOAD_FIELDS = {
    "raw_purchase_requests": {
        "request_id",
        "request_number",
        "request_title",
        "request_type",
        "department_id",
        "requester_id",
        "item_id",
        "quantity",
        "estimated_amount",
        "currency",
        "criticality_level",
        "business_impact",
        "needed_by_date",
        "submitted_at",
        "current_stage",
        "current_status",
    },
    "raw_purchase_orders": {
        "po_id",
        "po_number",
        "request_id",
        "vendor_id",
        "po_status",
    },
    "raw_vendor_updates": {
        "vendor_update_id",
        "po_id",
        "vendor_id",
        "update_type",
    },
    "raw_receipts": {
        "receipt_id",
        "po_id",
        "received_quantity",
        "inspection_status",
    },
    "raw_stage_events": {
        "event_id",
        "request_id",
        "stage",
        "event_type",
        "event_status",
        "occurred_at",
        "actor_type",
        "source_system",
    },
}

DATE_FIELDS = {
    "raw_purchase_requests": ["needed_by_date", "submitted_at"],
    "raw_purchase_orders": ["po_created_at", "vendor_confirmed_at", "expected_delivery_date", "actual_delivery_date"],
    "raw_vendor_updates": ["updated_at"],
    "raw_receipts": ["received_at", "inspection_completed_at"],
    "raw_stage_events": ["occurred_at"],
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
        _check_po_without_request(session),
        _check_receipt_without_po(session),
        _check_closed_request_without_receipt(session),
        _check_needed_by_date_before_submitted_at(session),
    ]

    return _quality_results_to_models(checks, pipeline_run_id, start_index)


def _check_unknown_source_system(target_table: str, records: list[dict[str, Any]]) -> QualityCheck:
    failed = [
        _record_key(record)
        for record in records
        if record.get("source_system") != SOURCE_SYSTEM
    ]
    return QualityCheck(
        check_name="unknown_source_system",
        target_table=target_table,
        severity="ERROR",
        failed_keys=failed,
        message="Source system must match the expected sample procurement source.",
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
    purchase_request_ids = _payload_id_set(records_by_table["raw_purchase_requests"], "request_id")
    purchase_order_ids = _payload_id_set(records_by_table["raw_purchase_orders"], "po_id")

    po_missing_request = [
        _record_key(record)
        for record in records_by_table["raw_purchase_orders"]
        if _payload_value(record, "request_id") not in purchase_request_ids
    ]
    event_missing_request = [
        _record_key(record)
        for record in records_by_table["raw_stage_events"]
        if _payload_value(record, "request_id") not in purchase_request_ids
    ]
    receipt_missing_po = [
        _record_key(record)
        for record in records_by_table["raw_receipts"]
        if _payload_value(record, "po_id") not in purchase_order_ids
    ]
    vendor_update_missing_po = [
        _record_key(record)
        for record in records_by_table["raw_vendor_updates"]
        if _payload_value(record, "po_id") not in purchase_order_ids
    ]

    return [
        QualityCheck(
            check_name="missing_request_reference",
            target_table="raw_purchase_orders",
            severity="ERROR",
            failed_keys=po_missing_request,
            message="Purchase order source records must reference an existing source request.",
        ),
        QualityCheck(
            check_name="missing_request_reference",
            target_table="raw_stage_events",
            severity="ERROR",
            failed_keys=event_missing_request,
            message="Stage event source records must reference an existing source request.",
        ),
        QualityCheck(
            check_name="missing_po_reference",
            target_table="raw_receipts",
            severity="ERROR",
            failed_keys=receipt_missing_po,
            message="Receipt source records must reference an existing source purchase order.",
        ),
        QualityCheck(
            check_name="missing_po_reference",
            target_table="raw_vendor_updates",
            severity="ERROR",
            failed_keys=vendor_update_missing_po,
            message="Vendor update source records must reference an existing source purchase order.",
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
        for row in session.execute(select(ProcurementStageEvent.request_id).distinct())
    }
    failed = [
        request.request_id
        for request in session.scalars(select(PurchaseRequest))
        if request.request_id not in request_ids_with_events
    ]
    return QualityCheck(
        check_name="request_without_stage_event",
        target_table="purchase_requests",
        severity="ERROR",
        failed_keys=failed,
        message="Every core purchase request should have at least one stage event.",
    )


def _check_event_timestamp_out_of_order(session: Session) -> QualityCheck:
    requests = {
        request.request_id: request
        for request in session.scalars(select(PurchaseRequest))
    }
    failed = []
    for event in session.scalars(select(ProcurementStageEvent)):
        request = requests.get(event.request_id)
        if request and event.occurred_at < request.submitted_at:
            failed.append(event.event_id)

    return QualityCheck(
        check_name="event_timestamp_out_of_order",
        target_table="procurement_stage_events",
        severity="ERROR",
        failed_keys=failed,
        message="Stage event timestamps should not occur before request submission.",
    )


def _check_po_without_request(session: Session) -> QualityCheck:
    request_ids = {
        row[0]
        for row in session.execute(select(PurchaseRequest.request_id))
    }
    failed = [
        purchase_order.po_id
        for purchase_order in session.scalars(select(PurchaseOrder))
        if purchase_order.request_id not in request_ids
    ]
    return QualityCheck(
        check_name="po_without_request",
        target_table="purchase_orders",
        severity="CRITICAL",
        failed_keys=failed,
        message="Every purchase order should reference an existing core request.",
    )


def _check_receipt_without_po(session: Session) -> QualityCheck:
    po_ids = {
        row[0]
        for row in session.execute(select(PurchaseOrder.po_id))
    }
    failed = [
        receipt.receipt_id
        for receipt in session.scalars(select(Receipt))
        if receipt.po_id not in po_ids
    ]
    return QualityCheck(
        check_name="receipt_without_po",
        target_table="receipts",
        severity="CRITICAL",
        failed_keys=failed,
        message="Every receipt should reference an existing core purchase order.",
    )


def _check_closed_request_without_receipt(session: Session) -> QualityCheck:
    po_by_request = {
        purchase_order.request_id: purchase_order.po_id
        for purchase_order in session.scalars(select(PurchaseOrder))
    }
    po_ids_with_receipts = {
        row[0]
        for row in session.execute(select(Receipt.po_id).distinct())
    }
    failed = []
    for request in session.scalars(select(PurchaseRequest)):
        if request.current_status != "CLOSED":
            continue
        po_id = po_by_request.get(request.request_id)
        if po_id not in po_ids_with_receipts:
            failed.append(request.request_id)

    return QualityCheck(
        check_name="closed_request_without_receipt",
        target_table="purchase_requests",
        severity="ERROR",
        failed_keys=failed,
        message="Closed requests should have receipt evidence in V1.",
    )


def _check_needed_by_date_before_submitted_at(session: Session) -> QualityCheck:
    failed = [
        request.request_id
        for request in session.scalars(select(PurchaseRequest))
        if request.needed_by_date < request.submitted_at.date()
    ]
    return QualityCheck(
        check_name="needed_by_date_before_submitted_at",
        target_table="purchase_requests",
        severity="ERROR",
        failed_keys=failed,
        message="Needed-by date should not be earlier than submission date.",
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
