from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.ops import PipelineRun
from app.pipeline.analytics_builder import build_analytics
from app.pipeline.core_transformer import transform_raw_to_core
from app.pipeline.quality import run_core_quality_checks, run_raw_quality_checks
from app.pipeline.raw_loader import load_raw_records, read_raw_source_records
from app.pipeline.reconciler import run_reconciliation_checks
from app.sample_data.generator import generate_sample_dataset, write_sample_dataset


PIPELINE_NAME = "ai_data_center_infrastructure_followup"


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
    reconciliation_issues_created: int


def run_ingestion_pipeline(
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
        reconciliation_result = run_reconciliation_checks(
            session=session,
            pipeline_run_id=pipeline_run_id,
        )

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
            reconciliation_issues_created=reconciliation_result.issues_created,
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


def _new_pipeline_run_id() -> str:
    timestamp = _utc_now().strftime("%Y%m%d%H%M%S")
    return f"RUN-{timestamp}-{uuid.uuid4().hex[:8]}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _core_records_loaded(core_result) -> int:
    return (
        core_result.infrastructure_zones_loaded
        + core_result.infrastructure_assets_loaded
        + core_result.facilities_engineers_loaded
        + core_result.critical_spares_loaded
        + core_result.infrastructure_incidents_loaded
        + core_result.incident_stage_events_loaded
        + core_result.facility_work_orders_loaded
        + core_result.validation_results_loaded
        + core_result.telemetry_alerts_loaded
    )


def _analytics_records_loaded(analytics_result) -> int:
    return (
        analytics_result.incident_current_status_count
        + analytics_result.incident_stage_lead_times_count
        + analytics_result.downtime_follow_up_queue_count
        + analytics_result.infrastructure_bottleneck_summary_count
        + analytics_result.asset_delay_summary_count
        + analytics_result.zone_delay_summary_count
        + analytics_result.spare_waiting_summary_count
    )
