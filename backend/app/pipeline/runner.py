from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.ops import PipelineRun
from app.pipeline.analytics_builder import build_analytics, build_maintenance_analytics
from app.pipeline.core_transformer import transform_maintenance_raw_to_core, transform_raw_to_core
from app.pipeline.quality import (
    run_core_quality_checks,
    run_maintenance_core_quality_checks,
    run_maintenance_raw_quality_checks,
    run_raw_quality_checks,
)
from app.pipeline.raw_loader import (
    load_maintenance_raw_records,
    load_raw_records,
    read_maintenance_raw_source_records,
    read_raw_source_records,
)
from app.sample_data.generator import (
    generate_maintenance_sample_dataset,
    generate_sample_dataset,
    write_sample_dataset,
)


PIPELINE_NAME = "procurement_ingestion"
MAINTENANCE_PIPELINE_NAME = "maintenance_ingestion"


@dataclass(frozen=True)
class PipelineResult:
    pipeline_run_id: str
    status: str
    rows_extracted: int
    rows_loaded: int
    rows_rejected: int
    quality_failed_checks: int
    core_records_loaded: int
    core_records_skipped: int
    analytics_records_loaded: int


def run_raw_ingestion_pipeline(
    session: Session,
    sample_dir: Path,
    generate_sample: bool = False,
    seed: int = 20260523,
) -> PipelineResult:
    if generate_sample:
        write_sample_dataset(generate_sample_dataset(seed=seed), sample_dir)

    pipeline_run_id = _new_pipeline_run_id()
    started_at = _utc_now()
    pipeline_run = PipelineRun(
        pipeline_run_id=pipeline_run_id,
        pipeline_name=PIPELINE_NAME,
        started_at=started_at,
        status="RUNNING",
        rows_extracted=0,
        rows_loaded=0,
        rows_rejected=0,
    )
    session.add(pipeline_run)
    session.flush()

    try:
        records_by_table = read_raw_source_records(sample_dir)
        quality_results = run_raw_quality_checks(records_by_table, pipeline_run_id)
        session.add_all(quality_results)

        load_result = load_raw_records(
            session=session,
            sample_dir=sample_dir,
            pipeline_run_id=pipeline_run_id,
        )

        core_result = transform_raw_to_core(session=session, sample_dir=sample_dir)
        core_quality_results = run_core_quality_checks(
            session=session,
            pipeline_run_id=pipeline_run_id,
            start_index=len(quality_results) + 1,
        )
        session.add_all(core_quality_results)
        analytics_result = build_analytics(session=session)

        all_quality_results = quality_results + core_quality_results
        failed_checks = sum(1 for result in all_quality_results if result.status != "PASS")
        status = "SUCCESS" if failed_checks == 0 and load_result.rows_rejected == 0 else "PARTIAL_SUCCESS"

        pipeline_run.status = status
        pipeline_run.rows_extracted = load_result.rows_extracted
        pipeline_run.rows_loaded = load_result.rows_loaded
        pipeline_run.rows_rejected = load_result.rows_rejected
        pipeline_run.finished_at = _utc_now()
        session.commit()

        return PipelineResult(
            pipeline_run_id=pipeline_run_id,
            status=status,
            rows_extracted=load_result.rows_extracted,
            rows_loaded=load_result.rows_loaded,
            rows_rejected=load_result.rows_rejected,
            quality_failed_checks=failed_checks,
            core_records_loaded=_core_records_loaded(core_result),
            core_records_skipped=core_result.records_skipped,
            analytics_records_loaded=_analytics_records_loaded(analytics_result),
        )
    except Exception as exc:
        session.rollback()
        failure_run = session.get(PipelineRun, pipeline_run_id)
        if failure_run is None:
            failure_run = PipelineRun(
                pipeline_run_id=pipeline_run_id,
                pipeline_name=PIPELINE_NAME,
                started_at=started_at,
                status="FAILED",
                rows_extracted=0,
                rows_loaded=0,
                rows_rejected=0,
            )
            session.add(failure_run)
        failure_run.status = "FAILED"
        failure_run.error_message = str(exc)
        failure_run.finished_at = _utc_now()
        session.commit()
        raise


def run_maintenance_ingestion_pipeline(
    session: Session,
    sample_dir: Path,
    generate_sample: bool = False,
    seed: int = 20260523,
) -> PipelineResult:
    if generate_sample:
        write_sample_dataset(generate_maintenance_sample_dataset(seed=seed), sample_dir)

    pipeline_run_id = _new_pipeline_run_id()
    started_at = _utc_now()
    pipeline_run = PipelineRun(
        pipeline_run_id=pipeline_run_id,
        pipeline_name=MAINTENANCE_PIPELINE_NAME,
        started_at=started_at,
        status="RUNNING",
        rows_extracted=0,
        rows_loaded=0,
        rows_rejected=0,
    )
    session.add(pipeline_run)
    session.flush()

    try:
        records_by_table = read_maintenance_raw_source_records(sample_dir)
        quality_results = run_maintenance_raw_quality_checks(records_by_table, pipeline_run_id)
        session.add_all(quality_results)

        load_result = load_maintenance_raw_records(
            session=session,
            sample_dir=sample_dir,
            pipeline_run_id=pipeline_run_id,
        )

        core_result = transform_maintenance_raw_to_core(session=session, sample_dir=sample_dir)
        core_quality_results = run_maintenance_core_quality_checks(
            session=session,
            pipeline_run_id=pipeline_run_id,
            start_index=len(quality_results) + 1,
        )
        session.add_all(core_quality_results)
        analytics_result = build_maintenance_analytics(session=session)

        all_quality_results = quality_results + core_quality_results
        failed_checks = sum(1 for result in all_quality_results if result.status != "PASS")
        status = "SUCCESS" if failed_checks == 0 and load_result.rows_rejected == 0 else "PARTIAL_SUCCESS"

        pipeline_run.status = status
        pipeline_run.rows_extracted = load_result.rows_extracted
        pipeline_run.rows_loaded = load_result.rows_loaded
        pipeline_run.rows_rejected = load_result.rows_rejected
        pipeline_run.finished_at = _utc_now()
        session.commit()

        return PipelineResult(
            pipeline_run_id=pipeline_run_id,
            status=status,
            rows_extracted=load_result.rows_extracted,
            rows_loaded=load_result.rows_loaded,
            rows_rejected=load_result.rows_rejected,
            quality_failed_checks=failed_checks,
            core_records_loaded=_maintenance_core_records_loaded(core_result),
            core_records_skipped=core_result.records_skipped,
            analytics_records_loaded=_maintenance_analytics_records_loaded(analytics_result),
        )
    except Exception as exc:
        session.rollback()
        failure_run = session.get(PipelineRun, pipeline_run_id)
        if failure_run is None:
            failure_run = PipelineRun(
                pipeline_run_id=pipeline_run_id,
                pipeline_name=MAINTENANCE_PIPELINE_NAME,
                started_at=started_at,
                status="FAILED",
                rows_extracted=0,
                rows_loaded=0,
                rows_rejected=0,
            )
            session.add(failure_run)
        failure_run.status = "FAILED"
        failure_run.error_message = str(exc)
        failure_run.finished_at = _utc_now()
        session.commit()
        raise


def _new_pipeline_run_id() -> str:
    timestamp = _utc_now().strftime("%Y%m%d%H%M%S")
    return f"RUN-{timestamp}-{uuid.uuid4().hex[:8]}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _core_records_loaded(core_result) -> int:
    return (
        core_result.departments_loaded
        + core_result.requesters_loaded
        + core_result.items_loaded
        + core_result.vendors_loaded
        + core_result.purchase_requests_loaded
        + core_result.purchase_orders_loaded
        + core_result.receipts_loaded
        + core_result.stage_events_loaded
    )


def _analytics_records_loaded(analytics_result) -> int:
    return (
        analytics_result.request_current_status_count
        + analytics_result.request_stage_lead_times_count
        + analytics_result.critical_request_queue_count
        + analytics_result.bottleneck_summary_count
        + analytics_result.vendor_delay_summary_count
    )


def _maintenance_core_records_loaded(core_result) -> int:
    return (
        core_result.production_lines_loaded
        + core_result.equipment_loaded
        + core_result.technicians_loaded
        + core_result.parts_loaded
        + core_result.maintenance_requests_loaded
        + core_result.maintenance_stage_events_loaded
        + core_result.maintenance_work_orders_loaded
        + core_result.inspection_results_loaded
        + core_result.sensor_alerts_loaded
    )


def _maintenance_analytics_records_loaded(analytics_result) -> int:
    return (
        analytics_result.maintenance_current_status_count
        + analytics_result.maintenance_stage_lead_times_count
        + analytics_result.critical_maintenance_queue_count
        + analytics_result.maintenance_bottleneck_summary_count
        + analytics_result.equipment_delay_summary_count
        + analytics_result.production_line_delay_summary_count
        + analytics_result.parts_waiting_summary_count
    )
