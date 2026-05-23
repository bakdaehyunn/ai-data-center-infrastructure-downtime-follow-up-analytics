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
from app.pipeline.runner import run_raw_ingestion_pipeline
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
        run_raw_ingestion_pipeline(session=session, sample_dir=sample_dir)

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_overview_endpoint_returns_operational_summary(api_client: TestClient) -> None:
    response = api_client.get("/api/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 10
    assert data["open_requests"] == 7
    assert data["delayed_requests"] == 8
    assert data["critical_open_requests"] == 3
    assert data["top_bottleneck_stage"] == "VENDOR_CONFIRMATION"
    assert data["latest_pipeline_run_status"] == "PARTIAL_SUCCESS"
    assert data["data_quality_status"] == "FAILED"


def test_critical_requests_endpoint_returns_ranked_queue(api_client: TestClient) -> None:
    response = api_client.get("/api/requests/critical?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert [row["request_id"] for row in data] == ["REQ-0005", "REQ-0009", "REQ-0002"]
    assert data[0]["priority_rank"] == 1
    assert data[0]["total_priority_score"] == 120.0
    assert data[0]["recommended_action"] == "Escalate vendor confirmation"


def test_bottleneck_endpoints_return_stage_and_vendor_summaries(api_client: TestClient) -> None:
    stages_response = api_client.get("/api/bottlenecks/stages")
    vendors_response = api_client.get("/api/bottlenecks/vendors")

    assert stages_response.status_code == 200
    assert vendors_response.status_code == 200
    stages = stages_response.json()
    vendors = vendors_response.json()
    assert stages[0]["stage"] == "VENDOR_CONFIRMATION"
    assert stages[0]["total_delay_hours"] == 317.0
    assert vendors[0]["vendor_id"] == "VEN-SIGNAL"
    assert vendors[0]["delay_rate"] == 1.0
    assert vendors[0]["delayed_po_count"] == 2


def test_operations_endpoints_return_pipeline_and_quality_results(api_client: TestClient) -> None:
    runs_response = api_client.get("/api/pipeline-runs")
    failed_checks_response = api_client.get("/api/data-quality/checks?status=FAILED")

    assert runs_response.status_code == 200
    assert failed_checks_response.status_code == 200
    runs = runs_response.json()
    failed_checks = failed_checks_response.json()
    assert len(runs) == 1
    assert runs[0]["status"] == "PARTIAL_SUCCESS"
    assert len(failed_checks) == 4
    assert {
        (check["target_table"], check["check_name"])
        for check in failed_checks
    } == {
        ("raw_purchase_requests", "duplicate_source_record"),
        ("raw_purchase_requests", "missing_required_fields"),
        ("purchase_requests", "request_without_stage_event"),
        ("procurement_stage_events", "event_timestamp_out_of_order"),
    }


def test_metadata_endpoint_returns_dashboard_filters(api_client: TestClient) -> None:
    response = api_client.get("/api/metadata/filters")

    assert response.status_code == 200
    data = response.json()
    assert len(data["departments"]) == 6
    assert len(data["vendors"]) == 5
    assert "IT_EQUIPMENT" in data["item_categories"]
    assert data["criticality_levels"] == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "VENDOR_CONFIRMATION" in data["stages"]
