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
from app.models.ops import DataQualityCheckResult, InfrastructureReconciliationIssue, PipelineRun
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
    assert data["critical_asset_delayed"] == 3
    assert data["top_bottleneck_stage"] == "ENGINEER_ASSIGNED"
    assert data["repeat_failure_asset_count"] == 1
    assert data["capacity_risk_kw"] == 2820.0
    assert data["affected_gpu_count"] == 1024
    assert data["redundancy_lost_incidents"] == 5
    assert data["vendor_eta_missed_count"] == 1
    assert data["latest_pipeline_run_status"] == "PARTIAL_SUCCESS"
    assert data["data_quality_status"] == "FAILED"


def test_follow_ups_endpoint_returns_ranked_queue(api_client: TestClient) -> None:
    response = api_client.get("/api/follow-ups?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert [row["incident_id"] for row in data] == ["INC-0007", "INC-0004", "INC-0006"]
    assert data[0]["priority_rank"] == 1
    assert data[0]["current_stage"] == "SPARE_VENDOR_WAITING"
    assert data[0]["recommended_action"] == "Escalate missed vendor ETA and confirm recovery path"
    assert data[0]["total_priority_score"] == 222.0
    assert data[0]["redundancy_state"] == "N-1"
    assert data[0]["affected_gpu_count"] == 320
    assert data[0]["vendor_status"] == "ETA_MISSED"
    assert data[0]["impact_confidence_status"] == "WARNING"
    assert data[0]["impact_trust_issue_count"] == 1
    assert data[2]["impact_confidence_status"] == "TRUSTED"


def test_follow_ups_endpoint_filters_queue(api_client: TestClient) -> None:
    stage_response = api_client.get("/api/follow-ups?stage=ENGINEER_ASSIGNED")
    zone_response = api_client.get("/api/follow-ups?zone_id=ZONE-POWER-A")
    priority_response = api_client.get("/api/follow-ups?priority_level=CRITICAL")

    assert stage_response.status_code == 200
    assert zone_response.status_code == 200
    assert priority_response.status_code == 200

    assert [row["incident_id"] for row in stage_response.json()] == ["INC-0003", "INC-0009"]
    assert {row["zone_id"] for row in zone_response.json()} == {"ZONE-POWER-A"}
    assert {row["priority_level"] for row in priority_response.json()} == {"CRITICAL"}


def test_follow_up_detail_returns_state_timeline_and_related_records(api_client: TestClient) -> None:
    response = api_client.get("/api/follow-ups/INC-0004")

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["incident_id"] == "INC-0004"
    assert data["request"]["priority_rank"] == 2
    assert data["request"]["current_stage"] == "SPARE_VENDOR_WAITING"
    assert data["request"]["recommended_action"] == "Expedite critical spare or vendor dispatch"
    assert "Impact rationale:" in data["request"]["reason_summary"]
    assert "redundancy exposure" in data["request"]["reason_summary"]
    assert data["request"]["mitigation_status"] == "LOAD_SHIFTED"
    assert data["request"]["vendor_status"] == "WAITING_VENDOR_DISPATCH"
    assert [stage["stage"] for stage in data["stage_lead_times"]] == [
        "INCIDENT_REPORTED",
        "FACILITIES_TRIAGE",
        "ENGINEER_ASSIGNED",
        "SPARE_VENDOR_WAITING",
    ]
    assert data["stage_lead_times"][-1]["is_bottleneck"] is True
    assert data["work_orders"][0]["required_spare_id"] == "SPARE-CHILLER-COMPRESSOR"
    assert data["work_orders"][0]["stock_status"] == "OUT_OF_STOCK"
    assert data["telemetry_alerts"][0]["alert_type"] == "CHILLED_WATER_TEMP_HIGH"
    assert data["impact_snapshot"]["affected_gpu_count"] == 256
    assert data["impact_snapshot"]["estimated_capacity_risk_kw"] == 620.0
    assert data["impact_snapshot"]["cooling_redundancy_lost"] is True
    assert data["impact_snapshot"]["telemetry_readings"][0]["metric"] == "supply_water_temp_c"
    assert data["impact_confidence_status"] == "WARNING"
    assert data["impact_trust_flags"] == [
        {
            "issue_type": "impact_vendor_eta_past_not_missed",
            "severity": "WARNING",
            "message": "The vendor ETA is older than the analytics as-of time, but the impact snapshot has not marked the ETA as missed.",
            "evidence": {
                "vendor_status": "WAITING_VENDOR_DISPATCH",
                "vendor_eta_at": "2026-01-07T16:00:00",
                "analytics_as_of": "2026-01-10T03:00:00",
            },
        }
    ]
    assert any(
        flag == "Spare or vendor evidence mismatch: A work order is waiting on a spare or vendor, but no required spare is linked."
        for flag in data["quality_flags"]
    )


def test_follow_up_detail_handles_completed_non_queued_request(api_client: TestClient) -> None:
    response = api_client.get("/api/follow-ups/INC-0010")

    assert response.status_code == 200
    data = response.json()
    assert data["request"]["priority_rank"] == 0
    assert data["request"]["current_status"] == "RESTORED"
    assert data["request"]["recommended_action"] == "No follow-up required"
    assert len(data["timeline"]) == 15
    assert data["impact_snapshot"]["mitigation_status"] == "VERIFIED_NORMAL"
    assert data["impact_confidence_status"] == "TRUSTED"
    assert data["impact_trust_flags"] == []
    assert data["quality_flags"] == []


def test_follow_up_detail_and_timeline_return_404_for_unknown_request(api_client: TestClient) -> None:
    detail_response = api_client.get("/api/follow-ups/INC-NOT-FOUND")
    timeline_response = api_client.get("/api/follow-ups/INC-NOT-FOUND/timeline")

    assert detail_response.status_code == 404
    assert timeline_response.status_code == 404


def test_downtime_and_impact_endpoints_return_analytics(api_client: TestClient) -> None:
    stages_response = api_client.get("/api/downtime/stages")
    assets_response = api_client.get("/api/assets/delays")
    zones_response = api_client.get("/api/zones/delays")
    spares_response = api_client.get("/api/spares/waiting")
    impact_response = api_client.get("/api/impact/summary")

    assert stages_response.status_code == 200
    assert assets_response.status_code == 200
    assert zones_response.status_code == 200
    assert spares_response.status_code == 200
    assert impact_response.status_code == 200

    stages = stages_response.json()
    assert stages[0]["stage"] == "ENGINEER_ASSIGNED"
    assert stages[0]["total_delay_hours"] == 132.0
    assert assets_response.json()[0]["asset_id"] == "ASSET-UPS-01"
    assert zones_response.json()[0]["zone_id"] == "ZONE-POWER-A"
    assert spares_response.json()[0]["spare_id"] == "SPARE-CHILLER-COMPRESSOR"
    assert impact_response.json() == {
        "incident_count": 7,
        "capacity_risk_kw": 2820.0,
        "affected_rack_count": 128,
        "affected_gpu_count": 1024,
        "redundancy_lost_incidents": 5,
        "vendor_eta_missed_count": 1,
        "mitigated_incidents": 6,
        "thermal_breach_minutes": 219,
        "trusted_impact_count": 4,
        "warning_impact_count": 3,
        "unverified_impact_count": 0,
    }


def test_data_quality_endpoints_expose_failed_checks(api_client: TestClient) -> None:
    response = api_client.get("/api/data-quality/checks?status=FAILED")

    assert response.status_code == 200
    data = response.json()
    failed_keys = {(row["target_table"], row["check_name"]) for row in data}
    assert {
        ("raw_infrastructure_incidents", "duplicate_source_record"),
        ("raw_infrastructure_incidents", "missing_required_fields"),
        ("infrastructure_incidents", "infrastructure_incident_without_stage_event"),
        ("incident_stage_events", "stage_event_timestamp_out_of_order"),
        ("facility_work_orders", "spare_waiting_without_required_spare"),
        ("validation_results", "validation_without_completed_work"),
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
                pipeline_name="ai_data_center_infrastructure_followup",
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
                sample_failed_keys=["INC-0010"],
                message="Old failed check should not affect latest-run quality.",
            )
        )
        session.add(
            InfrastructureReconciliationIssue(
                issue_id="REC-RUN-OLDER-FAILED-001",
                pipeline_run_id="RUN-OLDER-FAILED",
                incident_id="INC-0010",
                asset_id="ASSET-SWGR-01",
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
    detail_response = api_client.get("/api/follow-ups/INC-0010")

    assert overview_response.status_code == 200
    assert failed_response.status_code == 200
    assert all_failed_response.status_code == 200
    assert detail_response.status_code == 200
    assert overview_response.json()["latest_pipeline_run_status"] == "PARTIAL_SUCCESS"
    assert {row["target_table"] for row in failed_response.json()} != {"stale_table"}
    assert "stale_table" not in {row["target_table"] for row in failed_response.json()}
    assert "stale_table" in {row["target_table"] for row in all_failed_response.json()}
    assert detail_response.json()["quality_flags"] == []
    assert detail_response.json()["impact_trust_flags"] == []


def test_filter_metadata_endpoint_returns_infrastructure_options(api_client: TestClient) -> None:
    response = api_client.get("/api/metadata/filters")

    assert response.status_code == 200
    data = response.json()
    assert len(data["infrastructure_zones"]) == 5
    assert len(data["assets"]) == 9
    assert "SPARE_VENDOR_WAITING" in data["stages"]
    assert "RESTORED" not in data["stages"]
    assert "CRITICAL" in data["priority_levels"]
