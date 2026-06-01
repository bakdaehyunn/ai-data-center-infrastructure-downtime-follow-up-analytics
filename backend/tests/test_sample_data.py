import json

from app.sample_data.generator import (
    generate_maintenance_sample_dataset,
    generate_sample_dataset,
    write_sample_dataset,
)


def test_sample_dataset_is_deterministic() -> None:
    first = generate_sample_dataset(seed=123)
    second = generate_sample_dataset(seed=123)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_maintenance_sample_dataset_is_deterministic() -> None:
    first = generate_maintenance_sample_dataset(seed=123)
    second = generate_maintenance_sample_dataset(seed=123)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_sample_dataset_contains_required_scenarios() -> None:
    dataset = generate_sample_dataset()
    scenario_keys = {
        scenario["scenario_key"]
        for scenario in dataset["manifest"]["scenarios"]
    }

    assert {
        "normal_completed",
        "budget_review_delay",
        "procurement_review_correction",
        "po_creation_delay",
        "vendor_confirmation_delay",
        "delivery_delay",
        "receiving_delay",
        "inspection_delay",
        "critical_request_delayed",
    }.issubset(scenario_keys)


def test_maintenance_sample_dataset_contains_required_scenarios() -> None:
    dataset = generate_maintenance_sample_dataset()
    scenario_keys = {
        scenario["scenario_key"]
        for scenario in dataset["manifest"]["scenarios"]
    }

    assert {
        "normal_completed_maintenance",
        "maintenance_review_delay",
        "technician_assignment_delay",
        "parts_waiting_delay",
        "maintenance_in_progress_delay",
        "inspection_delay",
        "critical_equipment_delayed",
        "repeat_failure_equipment",
        "line_delay_concentration",
        "sensor_triggered_maintenance",
    }.issubset(scenario_keys)


def test_sample_dataset_contains_quality_issue_records() -> None:
    dataset = generate_sample_dataset()
    expected_checks = {
        issue["check_name"]
        for issue in dataset["manifest"]["expected_quality_issues"]
    }
    purchase_request_source_ids = [
        record["source_record_id"]
        for record in dataset["purchase_requests"]
    ]

    assert {
        "duplicate_source_record",
        "missing_required_fields",
        "request_without_stage_event",
        "event_timestamp_out_of_order",
    } == expected_checks
    assert len(purchase_request_source_ids) != len(set(purchase_request_source_ids))


def test_maintenance_sample_dataset_contains_quality_issue_records() -> None:
    dataset = generate_maintenance_sample_dataset()
    expected_checks = {
        issue["check_name"]
        for issue in dataset["manifest"]["expected_quality_issues"]
    }
    maintenance_request_source_ids = [
        record["source_record_id"]
        for record in dataset["maintenance_requests"]
    ]

    assert {
        "duplicate_source_record",
        "missing_required_fields",
        "maintenance_request_without_stage_event",
        "stage_event_timestamp_out_of_order",
        "parts_waiting_without_required_part",
        "inspection_without_completed_work",
    } == expected_checks
    assert len(maintenance_request_source_ids) != len(set(maintenance_request_source_ids))


def test_critical_delayed_requests_are_open() -> None:
    dataset = generate_sample_dataset()
    requests_by_scenario = {
        record["payload"]["scenario_key"]: record["payload"]
        for record in dataset["purchase_requests"]
        if "scenario_key" in record["payload"]
    }

    critical = requests_by_scenario["critical_request_delayed"]
    vendor_delay = requests_by_scenario["vendor_confirmation_delay"]
    delivery_delay = requests_by_scenario["delivery_delay"]

    assert critical["criticality_level"] == "CRITICAL"
    assert critical["current_stage"] == "VENDOR_CONFIRMATION"
    assert critical["current_status"] == "IN_PROGRESS"
    assert vendor_delay["current_stage"] == "VENDOR_CONFIRMATION"
    assert delivery_delay["current_stage"] == "DELIVERY"


def test_critical_delayed_maintenance_requests_are_open() -> None:
    dataset = generate_maintenance_sample_dataset()
    requests_by_scenario = {
        record["payload"]["scenario_key"]: record["payload"]
        for record in dataset["maintenance_requests"]
        if "scenario_key" in record["payload"]
    }

    parts_waiting = requests_by_scenario["parts_waiting_delay"]
    critical = requests_by_scenario["critical_equipment_delayed"]
    technician_delay = requests_by_scenario["technician_assignment_delay"]

    assert parts_waiting["priority_level"] == "CRITICAL"
    assert parts_waiting["current_stage"] == "PARTS_WAITING"
    assert parts_waiting["current_status"] == "IN_PROGRESS"
    assert critical["current_stage"] == "PARTS_WAITING"
    assert technician_delay["current_stage"] == "TECHNICIAN_ASSIGNED"


def test_write_sample_dataset_creates_expected_files(tmp_path) -> None:
    dataset = generate_sample_dataset()
    written = write_sample_dataset(dataset, tmp_path)

    assert {path.name for path in written} == {
        "manifest.json",
        "departments.json",
        "requesters.json",
        "items.json",
        "vendors.json",
        "purchase_requests.json",
        "purchase_orders.json",
        "vendor_updates.json",
        "receipts.json",
        "stage_events.json",
    }
    assert json.loads((tmp_path / "manifest.json").read_text())["seed"] == 20260523


def test_write_maintenance_sample_dataset_creates_expected_files(tmp_path) -> None:
    dataset = generate_maintenance_sample_dataset()
    written = write_sample_dataset(dataset, tmp_path)

    assert {path.name for path in written} == {
        "manifest.json",
        "production_lines.json",
        "equipment.json",
        "technicians.json",
        "parts.json",
        "maintenance_requests.json",
        "maintenance_stage_events.json",
        "maintenance_work_orders.json",
        "inspection_results.json",
        "sensor_alerts.json",
    }
    assert json.loads((tmp_path / "manifest.json").read_text())["source_system"] == "sample_industrial_maintenance_system"
