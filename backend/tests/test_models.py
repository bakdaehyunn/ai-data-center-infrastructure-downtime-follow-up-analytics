from app.models import Base


def test_v1_schema_tables_are_registered() -> None:
    expected_tables = {
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

    assert set(Base.metadata.tables) == expected_tables


def test_stage_events_support_timeline_queries() -> None:
    stage_events = Base.metadata.tables["procurement_stage_events"]

    assert "request_id" in stage_events.c
    assert "occurred_at" in stage_events.c
    assert any(
        index.name == "ix_procurement_stage_events_request_time"
        for index in stage_events.indexes
    )
