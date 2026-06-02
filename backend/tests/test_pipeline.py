from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.analytics import (
    DowntimeFollowUpQueue,
    EquipmentDelaySummary,
    MaintenanceBottleneckSummary,
    MaintenanceCurrentStatus,
    MaintenanceStageLeadTime,
    PartsWaitingSummary,
    ProductionLineDelaySummary,
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
from app.models.ops import DataQualityCheckResult, PipelineRun
from app.models.raw import (
    RawInspectionResult,
    RawMaintenanceRequest,
    RawMaintenanceStageEvent,
    RawMaintenanceWorkOrder,
    RawSensorAlert,
)
from app.pipeline.quality import run_raw_quality_checks
from app.pipeline.raw_loader import read_raw_source_records
from app.pipeline.runner import PIPELINE_NAME, run_ingestion_pipeline
from app.sample_data.generator import generate_sample_dataset, write_sample_dataset


def test_raw_quality_checks_detect_seeded_source_issues(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    records_by_table = read_raw_source_records(sample_dir)

    results = run_raw_quality_checks(records_by_table, pipeline_run_id="RUN-TEST")
    failures = {
        (result.target_table, result.check_name): result.failed_row_count
        for result in results
        if result.status != "PASS"
    }

    assert failures[("raw_maintenance_requests", "duplicate_source_record")] == 1
    assert failures[("raw_maintenance_requests", "missing_required_fields")] == 1


def test_ingestion_pipeline_loads_raw_core_analytics_and_quality_results(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        result = run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        assert result.status == "PARTIAL_SUCCESS"
        assert result.rows_extracted == 125
        assert result.rows_loaded == 124
        assert result.rows_rejected == 1
        assert result.quality_failed_checks == 6
        assert result.core_records_loaded == 153
        assert result.core_records_skipped == 1
        assert result.analytics_records_loaded == 358

        pipeline_run = session.scalar(select(PipelineRun).where(PipelineRun.pipeline_run_id == result.pipeline_run_id))
        assert pipeline_run is not None
        assert pipeline_run.pipeline_name == PIPELINE_NAME
        assert _count(session, RawMaintenanceRequest) == 12
        assert _count(session, RawMaintenanceStageEvent) == 91
        assert _count(session, RawMaintenanceWorkOrder) == 10
        assert _count(session, RawInspectionResult) == 5
        assert _count(session, RawSensorAlert) == 6
        assert _count(session, ProductionLine) == 5
        assert _count(session, Equipment) == 9
        assert _count(session, Technician) == 6
        assert _count(session, Part) == 10
        assert _count(session, MaintenanceRequest) == 11
        assert _count(session, MaintenanceStageEvent) == 91
        assert _count(session, MaintenanceWorkOrder) == 10
        assert _count(session, InspectionResult) == 5
        assert _count(session, SensorAlert) == 6
        assert _count(session, MaintenanceCurrentStatus) == 10
        assert _count(session, MaintenanceStageLeadTime) == 48
        assert _count(session, DowntimeFollowUpQueue) == 7
        assert _count(session, MaintenanceBottleneckSummary) == 277
        assert _count(session, EquipmentDelaySummary) == 9
        assert _count(session, ProductionLineDelaySummary) == 5
        assert _count(session, PartsWaitingSummary) == 2
        assert _count(session, DataQualityCheckResult) == 30

        failures = {
            (result.target_table, result.check_name): result.failed_row_count
            for result in session.scalars(select(DataQualityCheckResult))
            if result.status != "PASS"
        }
        assert failures[("raw_maintenance_requests", "duplicate_source_record")] == 1
        assert failures[("raw_maintenance_requests", "missing_required_fields")] == 1
        assert failures[("maintenance_requests", "maintenance_request_without_stage_event")] == 1
        assert failures[("maintenance_stage_events", "stage_event_timestamp_out_of_order")] == 1
        assert failures[("maintenance_work_orders", "parts_waiting_without_required_part")] == 1
        assert failures[("inspection_results", "inspection_without_completed_work")] == 1
        completed_stage_summary = session.scalar(
            select(MaintenanceBottleneckSummary).where(MaintenanceBottleneckSummary.stage == "COMPLETED")
        )
        assert completed_stage_summary is None


def test_analytics_identifies_seeded_downtime_bottlenecks(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        parts_waiting = session.scalar(
            select(MaintenanceBottleneckSummary).where(
                MaintenanceBottleneckSummary.dimension_type == "STAGE",
                MaintenanceBottleneckSummary.dimension_id == "PARTS_WAITING",
                MaintenanceBottleneckSummary.stage == "PARTS_WAITING",
            )
        )
        servo_part = session.scalar(
            select(PartsWaitingSummary).where(PartsWaitingSummary.part_id == "PART-SERVO-7KW")
        )
        repeat_equipment = session.scalar(
            select(EquipmentDelaySummary).where(EquipmentDelaySummary.equipment_id == "EQ-CNV-001")
        )

        assert parts_waiting is not None
        assert parts_waiting.delayed_count == 2
        assert float(parts_waiting.total_delay_hours) == 100.0
        assert servo_part is not None
        assert servo_part.waiting_request_count == 1
        assert float(servo_part.total_wait_hours) == 85.0
        assert repeat_equipment is not None
        assert repeat_equipment.request_count == 2
        assert repeat_equipment.repeat_failure_count == 2


def test_analytics_ranks_downtime_follow_up_queue(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        top_requests = session.scalars(
            select(DowntimeFollowUpQueue).order_by(DowntimeFollowUpQueue.priority_rank).limit(3)
        ).all()
        top_request_ids = [request.maintenance_request_id for request in top_requests]

        assert top_request_ids == ["MREQ-0004", "MREQ-0007", "MREQ-0006"]
        assert top_requests[0].current_stage == "PARTS_WAITING"
        assert top_requests[0].recommended_action == "Expedite required part or approve substitute"
        assert float(top_requests[0].total_priority_score) == 151.73


def test_pipeline_idempotently_rejects_duplicate_raw_records(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        first = run_ingestion_pipeline(session=session, sample_dir=sample_dir)
        second = run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        assert first.rows_loaded == 124
        assert second.rows_loaded == 0
        assert second.rows_rejected == 125
        assert _count(session, RawMaintenanceRequest) == 12
        assert _count(session, MaintenanceRequest) == 11
        assert _count(session, MaintenanceStageEvent) == 91
        assert _count(session, DowntimeFollowUpQueue) == 7


def _write_sample_data(tmp_path: Path) -> Path:
    sample_dir = tmp_path / "sample_data"
    write_sample_dataset(generate_sample_dataset(), sample_dir)
    return sample_dir


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
