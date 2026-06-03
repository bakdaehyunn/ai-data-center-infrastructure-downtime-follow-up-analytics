from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base
from app.models.ops import DataQualityCheckResult, MaintenanceReconciliationIssue, PipelineRun
from app.pipeline.runner import run_ingestion_pipeline
from app.sample_data.generator import generate_sample_dataset, write_sample_dataset


@pytest.fixture()
def api_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    sample_dir = tmp_path / "sample_data"
    write_sample_dataset(generate_sample_dataset(), sample_dir)
    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_overview_endpoint_returns_downtime_follow_up_summary(api_client: TestClient) -> None:
    response = api_client.get("/api/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 11
    assert data["open_requests"] == 8
    assert data["delayed_requests"] == 8
    assert data["critical_equipment_delayed"] == 3
    assert data["top_bottleneck_stage"] == "TECHNICIAN_ASSIGNED"
    assert data["latest_pipeline_run_status"] == "PARTIAL_SUCCESS"
    assert data["data_quality_status"] == "FAILED"


def test_follow_ups_endpoint_returns_ranked_queue(api_client: TestClient) -> None:
    response = api_client.get("/api/follow-ups?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert [row["maintenance_request_id"] for row in data] == ["MREQ-0004", "MREQ-0007", "MREQ-0006"]
    assert data[0]["priority_rank"] == 1
    assert data[0]["current_stage"] == "PARTS_WAITING"
    assert data[0]["recommended_action"] == "Expedite required part or approve substitute"
    assert data[0]["total_priority_score"] == 151.73


def test_follow_ups_endpoint_filters_queue(api_client: TestClient) -> None:
    stage_response = api_client.get("/api/follow-ups?stage=TECHNICIAN_ASSIGNED")
    line_response = api_client.get("/api/follow-ups?line_id=LINE-PKG-01")
    priority_response = api_client.get("/api/follow-ups?priority_level=CRITICAL")

    assert stage_response.status_code == 200
    assert line_response.status_code == 200
    assert priority_response.status_code == 200

    assert [row["maintenance_request_id"] for row in stage_response.json()] == ["MREQ-0003", "MREQ-0009"]
    assert {row["line_id"] for row in line_response.json()} == {"LINE-PKG-01"}
    assert {row["priority_level"] for row in priority_response.json()} == {"CRITICAL"}


def test_follow_up_detail_returns_state_timeline_and_related_records(api_client: TestClient) -> None:
    response = api_client.get("/api/follow-ups/MREQ-0004")

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["maintenance_request_id"] == "MREQ-0004"
    assert data["request"]["priority_rank"] == 1
    assert data["request"]["current_stage"] == "PARTS_WAITING"
    assert data["request"]["recommended_action"] == "Expedite required part or approve substitute"
    assert [stage["stage"] for stage in data["stage_lead_times"]] == [
        "MAINTENANCE_REQUEST_SUBMITTED",
        "MAINTENANCE_REVIEW",
        "TECHNICIAN_ASSIGNED",
        "PARTS_WAITING",
    ]
    assert data["stage_lead_times"][-1]["is_bottleneck"] is True
    assert data["work_orders"][0]["required_part_id"] == "PART-SERVO-7KW"
    assert data["work_orders"][0]["stock_status"] == "OUT_OF_STOCK"
    assert data["sensor_alerts"][0]["alert_type"] == "DRIVE_FAULT"
    assert any(
        flag == "Parts data mismatch: A work order is waiting for parts, but no required part is linked."
        for flag in data["quality_flags"]
    )


def test_follow_up_detail_handles_completed_non_queued_request(api_client: TestClient) -> None:
    response = api_client.get("/api/follow-ups/MREQ-0010")

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["priority_rank"] == 0
    assert data["request"]["current_status"] == "COMPLETED"
    assert data["request"]["recommended_action"] == "No follow-up required"
    assert len(data["timeline"]) == 14
    assert data["quality_flags"] == []


def test_follow_up_detail_and_timeline_return_404_for_unknown_request(api_client: TestClient) -> None:
    detail_response = api_client.get("/api/follow-ups/MREQ-NOT-FOUND")
    timeline_response = api_client.get("/api/follow-ups/MREQ-NOT-FOUND/timeline")

    assert detail_response.status_code == 404
    assert timeline_response.status_code == 404


def test_downtime_and_impact_endpoints_return_analytics(api_client: TestClient) -> None:
    stages_response = api_client.get("/api/downtime/stages")
    equipment_response = api_client.get("/api/equipment/delays")
    lines_response = api_client.get("/api/lines/delays")
    parts_response = api_client.get("/api/parts/waiting")

    assert stages_response.status_code == 200
    assert equipment_response.status_code == 200
    assert lines_response.status_code == 200
    assert parts_response.status_code == 200

    stages = stages_response.json()
    assert stages[0]["stage"] == "TECHNICIAN_ASSIGNED"
    assert stages[0]["total_delay_hours"] == 128.0
    assert equipment_response.json()[0]["equipment_id"] == "EQ-PRS-001"
    assert lines_response.json()[0]["line_id"] == "LINE-PKG-01"
    assert parts_response.json()[0]["part_id"] == "PART-SERVO-7KW"


def test_data_quality_endpoints_expose_failed_checks(api_client: TestClient) -> None:
    response = api_client.get("/api/data-quality/checks?status=FAILED")

    assert response.status_code == 200
    data = response.json()
    failed_keys = {(row["target_table"], row["check_name"]) for row in data}
    assert {
        ("raw_maintenance_requests", "duplicate_source_record"),
        ("raw_maintenance_requests", "missing_required_fields"),
        ("maintenance_requests", "maintenance_request_without_stage_event"),
        ("maintenance_stage_events", "stage_event_timestamp_out_of_order"),
        ("maintenance_work_orders", "parts_waiting_without_required_part"),
        ("inspection_results", "inspection_without_completed_work"),
    }.issubset(failed_keys)

    detail_response = api_client.get(f"/api/data-quality/checks/{data[0]['check_result_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["check_result_id"] == data[0]["check_result_id"]


def test_overview_and_quality_checks_use_latest_pipeline_run(api_client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as session:
        latest_run = session.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
        assert latest_run is not None
        session.add(
            PipelineRun(
                pipeline_run_id="RUN-OLDER-FAILED",
                pipeline_name="maintenance_downtime_followup",
                started_at=latest_run.started_at.replace(year=latest_run.started_at.year - 1),
                status="PARTIAL_SUCCESS",
                rows_extracted=1,
                rows_loaded=1,
                rows_rejected=0,
            )
        )
        session.add(
            DataQualityCheckResult(
                check_result_id="DQ-RUN-OLDER-FAILED-001",
                pipeline_run_id="RUN-OLDER-FAILED",
                check_name="stale_failure",
                target_table="stale_table",
                severity="ERROR",
                status="FAILED",
                failed_row_count=1,
                sample_failed_keys=["MREQ-0010"],
                message="Old failed check should not affect latest-run quality.",
            )
        )
        session.add(
            MaintenanceReconciliationIssue(
                issue_id="REC-RUN-OLDER-FAILED-001",
                pipeline_run_id="RUN-OLDER-FAILED",
                maintenance_request_id="MREQ-0010",
                equipment_id="EQ-MIX-001",
                issue_type="stale_reconciliation_issue",
                severity="ERROR",
                status="OPEN",
                message="Old reconciliation issue should not affect latest-run drilldown.",
                evidence_json={"source": "test"},
            )
        )
        session.commit()

    overview_response = api_client.get("/api/overview")
    failed_response = api_client.get("/api/data-quality/checks?status=FAILED")
    all_failed_response = api_client.get("/api/data-quality/checks?status=FAILED&all_runs=true")
    detail_response = api_client.get("/api/follow-ups/MREQ-0010")

    assert overview_response.status_code == 200
    assert failed_response.status_code == 200
    assert all_failed_response.status_code == 200
    assert detail_response.status_code == 200
    assert overview_response.json()["latest_pipeline_run_status"] == "PARTIAL_SUCCESS"
    assert {row["target_table"] for row in failed_response.json()} != {"stale_table"}
    assert "stale_table" not in {row["target_table"] for row in failed_response.json()}
    assert "stale_table" in {row["target_table"] for row in all_failed_response.json()}
    assert detail_response.json()["quality_flags"] == []


def test_filter_metadata_endpoint_returns_maintenance_options(api_client: TestClient) -> None:
    response = api_client.get("/api/metadata/filters")

    assert response.status_code == 200
    data = response.json()
    assert len(data["production_lines"]) == 5
    assert len(data["equipment"]) == 9
    assert "PARTS_WAITING" in data["stages"]
    assert "COMPLETED" not in data["stages"]
    assert "CRITICAL" in data["priority_levels"]
