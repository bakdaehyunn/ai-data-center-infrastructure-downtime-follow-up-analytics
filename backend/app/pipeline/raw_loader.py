from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type

from sqlalchemy import select
from sqlalchemy.orm import Session

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
    RawVendorUpdate,
)


@dataclass(frozen=True)
class RawSourceSpec:
    file_name: str
    target_table: str
    model: Type[
        RawPurchaseRequest
        | RawPurchaseOrder
        | RawVendorUpdate
        | RawReceipt
        | RawStageEvent
        | RawMaintenanceRequest
        | RawMaintenanceStageEvent
        | RawMaintenanceWorkOrder
        | RawInspectionResult
        | RawSensorAlert
    ]


RAW_SOURCE_SPECS = [
    RawSourceSpec("purchase_requests.json", "raw_purchase_requests", RawPurchaseRequest),
    RawSourceSpec("purchase_orders.json", "raw_purchase_orders", RawPurchaseOrder),
    RawSourceSpec("vendor_updates.json", "raw_vendor_updates", RawVendorUpdate),
    RawSourceSpec("receipts.json", "raw_receipts", RawReceipt),
    RawSourceSpec("stage_events.json", "raw_stage_events", RawStageEvent),
]

MAINTENANCE_RAW_SOURCE_SPECS = [
    RawSourceSpec("maintenance_requests.json", "raw_maintenance_requests", RawMaintenanceRequest),
    RawSourceSpec("maintenance_stage_events.json", "raw_maintenance_stage_events", RawMaintenanceStageEvent),
    RawSourceSpec("maintenance_work_orders.json", "raw_maintenance_work_orders", RawMaintenanceWorkOrder),
    RawSourceSpec("inspection_results.json", "raw_inspection_results", RawInspectionResult),
    RawSourceSpec("sensor_alerts.json", "raw_sensor_alerts", RawSensorAlert),
]


@dataclass(frozen=True)
class RawLoadResult:
    rows_extracted: int
    rows_loaded: int
    rows_rejected: int
    rejected_keys: list[str]


def read_raw_source_records(sample_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return _read_raw_source_records(sample_dir, RAW_SOURCE_SPECS)


def read_maintenance_raw_source_records(sample_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return _read_raw_source_records(sample_dir, MAINTENANCE_RAW_SOURCE_SPECS)


def _read_raw_source_records(
    sample_dir: Path,
    source_specs: list[RawSourceSpec],
) -> dict[str, list[dict[str, Any]]]:
    records_by_table: dict[str, list[dict[str, Any]]] = {}

    for spec in source_specs:
        path = sample_dir / spec.file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing raw source file: {path}")

        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError(f"Expected list records in {path}")
        records_by_table[spec.target_table] = records

    return records_by_table


def load_raw_records(
    session: Session,
    sample_dir: Path,
    pipeline_run_id: str,
) -> RawLoadResult:
    return _load_raw_records(
        session=session,
        records_by_table=read_raw_source_records(sample_dir),
        pipeline_run_id=pipeline_run_id,
        source_specs=RAW_SOURCE_SPECS,
    )


def load_maintenance_raw_records(
    session: Session,
    sample_dir: Path,
    pipeline_run_id: str,
) -> RawLoadResult:
    return _load_raw_records(
        session=session,
        records_by_table=read_maintenance_raw_source_records(sample_dir),
        pipeline_run_id=pipeline_run_id,
        source_specs=MAINTENANCE_RAW_SOURCE_SPECS,
    )


def _load_raw_records(
    session: Session,
    records_by_table: dict[str, list[dict[str, Any]]],
    pipeline_run_id: str,
    source_specs: list[RawSourceSpec],
) -> RawLoadResult:
    rows_extracted = 0
    rows_loaded = 0
    rejected_keys: list[str] = []

    for spec in source_specs:
        records = records_by_table[spec.target_table]
        rows_extracted += len(records)
        seen_keys: set[tuple[str, str]] = set()
        existing_keys = {
            (source_system, source_record_id)
            for source_system, source_record_id in session.execute(
                select(spec.model.source_system, spec.model.source_record_id)
            )
        }

        for record in records:
            source_system = record.get("source_system")
            source_record_id = record.get("source_record_id")
            payload = record.get("payload")
            source_key = (source_system, source_record_id)

            if (
                not source_system
                or not source_record_id
                or not isinstance(payload, dict)
                or source_key in seen_keys
            ):
                rejected_keys.append(f"{spec.target_table}:{source_system}:{source_record_id}")
                continue
            if source_key in existing_keys:
                continue

            seen_keys.add(source_key)
            session.add(
                spec.model(
                    source_record_id=source_record_id,
                    source_system=source_system,
                    payload_json=payload,
                    pipeline_run_id=pipeline_run_id,
                )
            )
            rows_loaded += 1

    return RawLoadResult(
        rows_extracted=rows_extracted,
        rows_loaded=rows_loaded,
        rows_rejected=len(rejected_keys),
        rejected_keys=rejected_keys,
    )
