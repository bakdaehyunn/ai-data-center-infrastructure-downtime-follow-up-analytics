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
    assert data[0]["criticality_score"] == 30.0
    assert data[0]["delay_score"] == 30.0
    assert data[0]["business_impact_score"] == 20.0
    assert data[0]["needed_by_urgency_score"] == 20.0
    assert data[0]["vendor_risk_score"] == 20.0
    assert data[0]["recommended_action"] == "Escalate vendor confirmation"


def test_critical_requests_endpoint_filters_operational_queue(api_client: TestClient) -> None:
    stage_response = api_client.get("/api/requests/critical?stage=BUDGET_REVIEW")
    vendor_response = api_client.get("/api/requests/critical?vendor_id=VEN-SIGNAL")
    criticality_response = api_client.get("/api/requests/critical?criticality_level=HIGH")

    assert stage_response.status_code == 200
    assert vendor_response.status_code == 200
    assert criticality_response.status_code == 200

    stage_data = stage_response.json()
    vendor_data = vendor_response.json()
    criticality_data = criticality_response.json()

    assert [row["request_id"] for row in stage_data] == ["REQ-0002"]
    assert [row["request_id"] for row in vendor_data] == ["REQ-0005", "REQ-0009"]
    assert criticality_data
    assert {row["criticality_level"] for row in criticality_data} == {"HIGH"}


def test_request_detail_endpoint_returns_state_timeline_and_related_records(api_client: TestClient) -> None:
    response = api_client.get("/api/requests/REQ-0005")

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["request_id"] == "REQ-0005"
    assert data["request"]["priority_rank"] == 1
    assert data["request"]["current_stage"] == "VENDOR_CONFIRMATION"
    assert data["request"]["recommended_action"] == "Escalate vendor confirmation"
    component_total = sum(
        data["request"][field]
        for field in [
            "criticality_score",
            "delay_score",
            "business_impact_score",
            "needed_by_urgency_score",
            "vendor_risk_score",
        ]
    )
    assert component_total == data["request"]["total_priority_score"]
    assert [stage["stage"] for stage in data["stage_lead_times"]] == [
        "REQUEST_SUBMITTED",
        "BUDGET_REVIEW",
        "PROCUREMENT_REVIEW",
        "PO_CREATION",
        "VENDOR_CONFIRMATION",
    ]
    assert data["stage_lead_times"][-1]["is_bottleneck"] is True
    assert data["related_po"]["po_id"] == "PO-0005"
    assert data["related_po"]["vendor_id"] == "VEN-SIGNAL"
    assert data["receipt"] is None
    assert data["quality_flags"] == []


def test_request_detail_endpoint_handles_closed_non_queued_request(api_client: TestClient) -> None:
    response = api_client.get("/api/requests/REQ-0001")

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["priority_rank"] == 0
    assert data["request"]["current_status"] == "CLOSED"
    assert data["request"]["recommended_action"] == "No action required"
    assert data["related_po"]["po_id"] == "PO-0001"
    assert data["receipt"]["receipt_id"] == "RCPT-0001"
    assert len(data["timeline"]) == 19
    assert set(data["quality_flags"]) == {
        "procurement_stage_events.event_timestamp_out_of_order: Stage event timestamps should not occur before request submission.",
        "raw_purchase_requests.duplicate_source_record: Duplicate source records are rejected before raw insertion.",
    }


def test_request_timeline_endpoint_returns_sorted_stage_events(api_client: TestClient) -> None:
    response = api_client.get("/api/requests/REQ-0005/timeline")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 9
    assert data[0]["stage"] == "REQUEST_SUBMITTED"
    assert data[0]["event_type"] == "ENTERED_STAGE"
    assert data[-1]["stage"] == "VENDOR_CONFIRMATION"
    assert data[-1]["event_type"] == "ENTERED_STAGE"


def test_request_detail_and_timeline_return_404_for_unknown_request(api_client: TestClient) -> None:
    detail_response = api_client.get("/api/requests/REQ-NOT-FOUND")
    timeline_response = api_client.get("/api/requests/REQ-NOT-FOUND/timeline")

    assert detail_response.status_code == 404
    assert timeline_response.status_code == 404


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


def test_bottleneck_endpoints_support_dashboard_filters(api_client: TestClient) -> None:
    stages_response = api_client.get(
        "/api/bottlenecks/stages?department_id=DEPT-SAFETY&criticality_level=HIGH&stage=BUDGET_REVIEW"
    )
    vendors_response = api_client.get(
        "/api/bottlenecks/vendors?vendor_id=VEN-SIGNAL&criticality_level=CRITICAL"
    )

    assert stages_response.status_code == 200
    assert vendors_response.status_code == 200

    stages = stages_response.json()
    vendors = vendors_response.json()
    assert len(stages) == 1
    assert stages[0]["stage"] == "BUDGET_REVIEW"
    assert stages[0]["request_count"] == 2
    assert stages[0]["delayed_count"] == 1
    assert [vendor["vendor_id"] for vendor in vendors] == ["VEN-SIGNAL"]
    assert vendors[0]["total_po_count"] == 2
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


def test_data_quality_checks_support_drilldown_filters_and_detail(api_client: TestClient) -> None:
    filtered_response = api_client.get(
        "/api/data-quality/checks?target_table=raw_purchase_requests&status=FAILED"
    )
    limited_response = api_client.get("/api/data-quality/checks?severity=ERROR&limit=2")

    assert filtered_response.status_code == 200
    assert limited_response.status_code == 200

    filtered_checks = filtered_response.json()
    limited_checks = limited_response.json()
    assert [check["check_name"] for check in filtered_checks] == [
        "duplicate_source_record",
        "missing_required_fields",
    ]
    assert len(limited_checks) <= 2
    assert {check["severity"] for check in limited_checks} == {"ERROR"}

    check_result_id = filtered_checks[0]["check_result_id"]
    detail_response = api_client.get(f"/api/data-quality/checks/{check_result_id}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["check_result_id"] == check_result_id
    assert detail["target_table"] == "raw_purchase_requests"
    assert detail["status"] == "FAILED"
    assert detail["failed_row_count"] == 1
    assert detail["sample_failed_keys"]
    assert detail["pipeline_run_id"] == filtered_checks[0]["pipeline_run_id"]
    assert "Duplicate source records" in detail["message"]


def test_data_quality_check_detail_returns_404_for_unknown_check(api_client: TestClient) -> None:
    response = api_client.get("/api/data-quality/checks/DQ-NOT-FOUND")

    assert response.status_code == 404


def test_metadata_endpoint_returns_dashboard_filters(api_client: TestClient) -> None:
    response = api_client.get("/api/metadata/filters")

    assert response.status_code == 200
    data = response.json()
    assert len(data["departments"]) == 6
    assert len(data["vendors"]) == 5
    assert "IT_EQUIPMENT" in data["item_categories"]
    assert data["criticality_levels"] == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "VENDOR_CONFIRMATION" in data["stages"]
