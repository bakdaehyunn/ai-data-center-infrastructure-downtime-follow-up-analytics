from app.models import Base


def test_infrastructure_downtime_schema_tables_are_registered() -> None:
    expected_tables = {
        "raw_infrastructure_incidents",
        "raw_incident_stage_events",
        "raw_facility_work_orders",
        "raw_validation_results",
        "raw_telemetry_alerts",
        "incident_current_status",
        "incident_stage_lead_times",
        "downtime_follow_up_queue",
        "infrastructure_bottleneck_summary",
        "asset_delay_summary",
        "zone_delay_summary",
        "spare_waiting_summary",
        "infrastructure_zones",
        "infrastructure_assets",
        "facilities_engineers",
        "critical_spares",
        "infrastructure_incidents",
        "incident_stage_events",
        "facility_work_orders",
        "validation_results",
        "telemetry_alerts",
        "pipeline_runs",
        "data_quality_check_results",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_stage_events_support_timeline_queries() -> None:
    stage_events = Base.metadata.tables["incident_stage_events"]

    assert "incident_id" in stage_events.c
    assert "occurred_at" in stage_events.c
    assert any(
        index.name == "ix_incident_stage_events_request_time"
        for index in stage_events.indexes
    )


def test_follow_up_queue_supports_priority_queries() -> None:
    queue = Base.metadata.tables["downtime_follow_up_queue"]

    assert "priority_rank" in queue.c
    assert "current_stage" in queue.c
    assert any(index.name == "ix_downtime_follow_up_queue_rank" for index in queue.indexes)
