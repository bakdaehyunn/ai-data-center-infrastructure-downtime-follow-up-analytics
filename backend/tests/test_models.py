from app.models import Base


def test_maintenance_downtime_schema_tables_are_registered() -> None:
    expected_tables = {
        "raw_maintenance_requests",
        "raw_maintenance_stage_events",
        "raw_maintenance_work_orders",
        "raw_inspection_results",
        "raw_sensor_alerts",
        "maintenance_current_status",
        "maintenance_stage_lead_times",
        "downtime_follow_up_queue",
        "maintenance_bottleneck_summary",
        "equipment_delay_summary",
        "production_line_delay_summary",
        "parts_waiting_summary",
        "production_lines",
        "equipment",
        "technicians",
        "parts",
        "maintenance_requests",
        "maintenance_stage_events",
        "maintenance_work_orders",
        "inspection_results",
        "sensor_alerts",
        "pipeline_runs",
        "data_quality_check_results",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_stage_events_support_timeline_queries() -> None:
    stage_events = Base.metadata.tables["maintenance_stage_events"]

    assert "maintenance_request_id" in stage_events.c
    assert "occurred_at" in stage_events.c
    assert any(
        index.name == "ix_maintenance_stage_events_request_time"
        for index in stage_events.indexes
    )


def test_follow_up_queue_supports_priority_queries() -> None:
    queue = Base.metadata.tables["downtime_follow_up_queue"]

    assert "priority_rank" in queue.c
    assert "current_stage" in queue.c
    assert any(index.name == "ix_downtime_follow_up_queue_rank" for index in queue.indexes)
