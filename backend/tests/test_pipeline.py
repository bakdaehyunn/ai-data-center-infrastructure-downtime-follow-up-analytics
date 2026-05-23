from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.ops import DataQualityCheckResult, PipelineRun
from app.models.raw import (
    RawPurchaseOrder,
    RawPurchaseRequest,
    RawReceipt,
    RawStageEvent,
    RawVendorUpdate,
)
from app.pipeline.quality import run_raw_quality_checks
from app.pipeline.raw_loader import read_raw_source_records
from app.pipeline.runner import run_raw_ingestion_pipeline
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

    assert failures[("raw_purchase_requests", "duplicate_source_record")] == 1
    assert failures[("raw_purchase_requests", "missing_required_fields")] == 1


def test_raw_ingestion_pipeline_loads_raw_records_and_quality_results(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        result = run_raw_ingestion_pipeline(session=session, sample_dir=sample_dir)

        assert result.status == "PARTIAL_SUCCESS"
        assert result.rows_extracted == 150
        assert result.rows_loaded == 149
        assert result.rows_rejected == 1
        assert result.quality_failed_checks == 2

        assert session.scalar(select(PipelineRun).where(PipelineRun.pipeline_run_id == result.pipeline_run_id)) is not None
        assert _count(session, RawPurchaseRequest) == 11
        assert _count(session, RawPurchaseOrder) == 8
        assert _count(session, RawVendorUpdate) == 8
        assert _count(session, RawReceipt) == 5
        assert _count(session, RawStageEvent) == 117
        assert _count(session, DataQualityCheckResult) == 24


def test_raw_ingestion_pipeline_is_idempotent_for_existing_source_records(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        first = run_raw_ingestion_pipeline(session=session, sample_dir=sample_dir)
        second = run_raw_ingestion_pipeline(session=session, sample_dir=sample_dir)

        assert first.rows_loaded == 149
        assert second.rows_loaded == 0
        assert second.rows_rejected == 0
        assert _count(session, RawPurchaseRequest) == 11
        assert _count(session, RawStageEvent) == 117


def _write_sample_data(tmp_path: Path) -> Path:
    sample_dir = tmp_path / "sample_data"
    write_sample_dataset(generate_sample_dataset(), sample_dir)
    return sample_dir


def _session_factory() -> sessionmaker:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _count(session, model) -> int:
    return len(session.scalars(select(model)).all())
