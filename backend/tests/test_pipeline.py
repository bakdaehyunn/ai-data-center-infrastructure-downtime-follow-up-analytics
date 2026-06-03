from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.analytics import (
    DowntimeFollowUpQueue,
    AssetDelaySummary,
    InfrastructureBottleneckSummary,
    IncidentCurrentStatus,
    IncidentStageLeadTime,
    SpareWaitingSummary,
    ZoneDelaySummary,
)
from app.models.infrastructure import (
    InfrastructureAsset,
    InfrastructureImpactSnapshot,
    ValidationResult,
    InfrastructureIncident,
    IncidentStageEvent,
    FacilityWorkOrder,
    CriticalSpare,
    InfrastructureZone,
    TelemetryAlert,
    FacilitiesEngineer,
)
from app.models.ops import DataQualityCheckResult, InfrastructureReconciliationIssue, PipelineRun
from app.models.raw import (
    RawValidationResult,
    RawInfrastructureIncident,
    RawIncidentStageEvent,
    RawFacilityWorkOrder,
    RawTelemetryAlert,
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

    assert failures[("raw_infrastructure_incidents", "duplicate_source_record")] == 1
    assert failures[("raw_infrastructure_incidents", "missing_required_fields")] == 1


def test_ingestion_pipeline_loads_raw_core_analytics_and_quality_results(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        result = run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        assert result.status == "PARTIAL_SUCCESS"
        assert result.rows_extracted == 142
        assert result.rows_loaded == 141
        assert result.rows_rejected == 1
        assert result.quality_failed_checks == 6
        assert result.core_records_loaded == 180
        assert result.core_records_skipped == 1
        assert result.analytics_records_loaded == 348
        assert result.reconciliation_issues_created == 8

        pipeline_run = session.scalar(select(PipelineRun).where(PipelineRun.pipeline_run_id == result.pipeline_run_id))
        assert pipeline_run is not None
        assert pipeline_run.pipeline_name == PIPELINE_NAME
        assert _count(session, RawInfrastructureIncident) == 12
        assert _count(session, RawIncidentStageEvent) == 108
        assert _count(session, RawFacilityWorkOrder) == 10
        assert _count(session, RawValidationResult) == 5
        assert _count(session, RawTelemetryAlert) == 6
        assert _count(session, InfrastructureZone) == 5
        assert _count(session, InfrastructureAsset) == 9
        assert _count(session, FacilitiesEngineer) == 7
        assert _count(session, CriticalSpare) == 9
        assert _count(session, InfrastructureIncident) == 11
        assert _count(session, IncidentStageEvent) == 108
        assert _count(session, FacilityWorkOrder) == 10
        assert _count(session, ValidationResult) == 5
        assert _count(session, TelemetryAlert) == 6
        assert _count(session, InfrastructureImpactSnapshot) == 10
        assert _count(session, IncidentCurrentStatus) == 10
        assert _count(session, IncidentStageLeadTime) == 48
        assert _count(session, DowntimeFollowUpQueue) == 7
        assert _count(session, InfrastructureBottleneckSummary) == 267
        assert _count(session, AssetDelaySummary) == 9
        assert _count(session, ZoneDelaySummary) == 5
        assert _count(session, SpareWaitingSummary) == 2
        assert _count(session, DataQualityCheckResult) == 30
        assert _count(session, InfrastructureReconciliationIssue) == 8

        failures = {
            (result.target_table, result.check_name): result.failed_row_count
            for result in session.scalars(select(DataQualityCheckResult))
            if result.status != "PASS"
        }
        assert failures[("raw_infrastructure_incidents", "duplicate_source_record")] == 1
        assert failures[("raw_infrastructure_incidents", "missing_required_fields")] == 1
        assert failures[("infrastructure_incidents", "infrastructure_incident_without_stage_event")] == 1
        assert failures[("incident_stage_events", "stage_event_timestamp_out_of_order")] == 1
        assert failures[("facility_work_orders", "spare_waiting_without_required_spare")] == 1
        assert failures[("validation_results", "validation_without_completed_work")] == 1
        reconciliation_issue_types = {
            issue.issue_type
            for issue in session.scalars(select(InfrastructureReconciliationIssue))
        }
        assert {
            "analytics_output_missing_current_status",
            "event_sequence_before_request",
            "impact_mitigation_without_event_evidence",
            "impact_vendor_eta_past_not_missed",
            "validation_without_completed_work",
            "spare_waiting_missing_required_spare",
            "state_reconstruction_missing_stage_event",
        } == reconciliation_issue_types
        impact_reconciliation_issues = {
            (issue.incident_id, issue.issue_type)
            for issue in session.scalars(
                select(InfrastructureReconciliationIssue).where(
                    InfrastructureReconciliationIssue.issue_type.like("impact_%")
                )
            )
        }
        assert {
            ("INC-0003", "impact_mitigation_without_event_evidence"),
            ("INC-0004", "impact_vendor_eta_past_not_missed"),
            ("INC-0007", "impact_mitigation_without_event_evidence"),
        } == impact_reconciliation_issues
        spare_reconciliation_issue = session.scalar(
            select(InfrastructureReconciliationIssue).where(
                InfrastructureReconciliationIssue.incident_id == "INC-0004",
                InfrastructureReconciliationIssue.issue_type == "spare_waiting_missing_required_spare",
            )
        )
        assert spare_reconciliation_issue is not None
        assert spare_reconciliation_issue.evidence_json == {
            "work_order_ids": ["MWO-QA-NO-PART"],
            "work_order_status": "WAITING_SPARE_VENDOR",
        }
        completed_stage_summary = session.scalar(
            select(InfrastructureBottleneckSummary).where(InfrastructureBottleneckSummary.stage == "RESTORED")
        )
        assert completed_stage_summary is None


def test_analytics_identifies_seeded_downtime_bottlenecks(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        spare_waiting = session.scalar(
            select(InfrastructureBottleneckSummary).where(
                InfrastructureBottleneckSummary.dimension_type == "STAGE",
                InfrastructureBottleneckSummary.dimension_id == "SPARE_VENDOR_WAITING",
                InfrastructureBottleneckSummary.stage == "SPARE_VENDOR_WAITING",
            )
        )
        chiller_spare = session.scalar(
            select(SpareWaitingSummary).where(SpareWaitingSummary.spare_id == "SPARE-CHILLER-COMPRESSOR")
        )
        repeat_asset = session.scalar(
            select(AssetDelaySummary).where(AssetDelaySummary.asset_id == "ASSET-CRAH-01")
        )

        assert spare_waiting is not None
        assert spare_waiting.delayed_count == 2
        assert float(spare_waiting.total_delay_hours) == 112.0
        assert chiller_spare is not None
        assert chiller_spare.waiting_request_count == 1
        assert float(chiller_spare.total_wait_hours) == 85.0
        assert repeat_asset is not None
        assert repeat_asset.request_count == 2
        assert repeat_asset.repeat_failure_count == 2


def test_analytics_ranks_downtime_follow_up_queue(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        top_requests = session.scalars(
            select(DowntimeFollowUpQueue).order_by(DowntimeFollowUpQueue.priority_rank).limit(3)
        ).all()
        top_request_ids = [request.incident_id for request in top_requests]

        assert top_request_ids == ["INC-0007", "INC-0004", "INC-0006"]
        assert top_requests[0].current_stage == "SPARE_VENDOR_WAITING"
        assert top_requests[0].recommended_action == "Escalate missed vendor ETA and confirm recovery path"
        assert float(top_requests[0].total_priority_score) == 222.0
        assert float(top_requests[0].capacity_risk_score) == 30.0
        assert float(top_requests[0].redundancy_risk_score) == 24.0
        assert float(top_requests[0].vendor_eta_risk_score) == 22.0


def test_pipeline_idempotently_rejects_duplicate_raw_records(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        first = run_ingestion_pipeline(session=session, sample_dir=sample_dir)
        second = run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        assert first.rows_loaded == 141
        assert second.rows_loaded == 0
        assert second.rows_rejected == 142
        assert _count(session, RawInfrastructureIncident) == 12
        assert _count(session, InfrastructureIncident) == 11
        assert _count(session, IncidentStageEvent) == 108
        assert _count(session, InfrastructureImpactSnapshot) == 10
        assert _count(session, DowntimeFollowUpQueue) == 7


def test_reconciliation_detects_impact_context_evidence_issues(tmp_path: Path) -> None:
    sample_dir = _write_sample_data(tmp_path)
    session_factory = _session_factory()

    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)

        vendor_issue = session.scalar(
            select(InfrastructureReconciliationIssue).where(
                InfrastructureReconciliationIssue.incident_id == "INC-0004",
                InfrastructureReconciliationIssue.issue_type == "impact_vendor_eta_past_not_missed",
            )
        )
        mitigation_issue = session.scalar(
            select(InfrastructureReconciliationIssue).where(
                InfrastructureReconciliationIssue.incident_id == "INC-0007",
                InfrastructureReconciliationIssue.issue_type == "impact_mitigation_without_event_evidence",
            )
        )

        assert vendor_issue is not None
        assert vendor_issue.severity == "WARNING"
        assert vendor_issue.evidence_json["vendor_status"] == "WAITING_VENDOR_DISPATCH"
        assert vendor_issue.evidence_json["vendor_eta_at"] == "2026-01-07T16:00:00"
        assert mitigation_issue is not None
        assert mitigation_issue.evidence_json == {
            "mitigation_status": "RUNNING_DEGRADED",
            "expected_event_type": "MITIGATION_APPLIED",
            "latest_snapshot_id": "IMPACT-0007",
            "latest_snapshot_at": "2026-01-09T22:00:00",
        }


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
