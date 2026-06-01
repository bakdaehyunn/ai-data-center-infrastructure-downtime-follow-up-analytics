from app.models import Base


def test_v1_schema_tables_are_registered() -> None:
    expected_v1_tables = {
        "raw_purchase_requests",
        "raw_purchase_orders",
        "raw_vendor_updates",
        "raw_receipts",
        "raw_stage_events",
        "departments",
        "requesters",
        "items",
        "vendors",
        "purchase_requests",
        "purchase_orders",
        "receipts",
        "procurement_stage_events",
        "request_current_status",
        "request_stage_lead_times",
        "critical_request_queue",
        "bottleneck_summary",
        "vendor_delay_summary",
        "pipeline_runs",
        "data_quality_check_results",
    }

    assert expected_v1_tables.issubset(set(Base.metadata.tables))


def test_v2_maintenance_schema_tables_are_registered() -> None:
    expected_v2_tables = {
        "raw_maintenance_requests",
        "raw_maintenance_stage_events",
        "raw_maintenance_work_orders",
        "raw_inspection_results",
        "raw_sensor_alerts",
        "maintenance_current_status",
        "maintenance_stage_lead_times",
        "critical_maintenance_queue",
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
    }

    assert expected_v2_tables.issubset(set(Base.metadata.tables))


def test_stage_events_support_timeline_queries() -> None:
    stage_events = Base.metadata.tables["procurement_stage_events"]

    assert "request_id" in stage_events.c
    assert "occurred_at" in stage_events.c
    assert any(
        index.name == "ix_procurement_stage_events_request_time"
        for index in stage_events.indexes
    )


def test_maintenance_stage_events_support_timeline_queries() -> None:
    stage_events = Base.metadata.tables["maintenance_stage_events"]

    assert "maintenance_request_id" in stage_events.c
    assert "occurred_at" in stage_events.c
    assert any(
        index.name == "ix_maintenance_stage_events_request_time"
        for index in stage_events.indexes
    )
