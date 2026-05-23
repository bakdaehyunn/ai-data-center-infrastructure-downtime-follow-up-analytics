from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
        for index, check in enumerate(checks, start=1)
    ]


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
