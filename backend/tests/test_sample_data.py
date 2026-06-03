import json

from app.sample_data.generator import generate_sample_dataset, write_sample_dataset


def test_sample_dataset_is_deterministic() -> None:
    first = generate_sample_dataset(seed=123)
    second = generate_sample_dataset(seed=123)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_sample_dataset_contains_required_downtime_follow_up_scenarios() -> None:
    dataset = generate_sample_dataset()
    scenario_keys = {
        scenario["scenario_key"]
        for scenario in dataset["manifest"]["scenarios"]
    }

    assert {
        "completed_crac_fan_replacement",
        "ups_module_triage_delay",
        "pdu_breaker_assignment_delay",
        "chiller_spare_waiting_delay",
        "cdu_repair_in_progress_delay",
        "thermal_validation_delay",
        "generator_vendor_waiting_delay",
        "repeated_crah_fan_failure",
        "gpu_zone_temperature_assignment_delay",
        "epms_telemetry_follow_up",
    }.issubset(scenario_keys)


def test_sample_dataset_contains_seeded_quality_issue_records() -> None:
    dataset = generate_sample_dataset()
    expected_checks = {
        issue["check_name"]
        for issue in dataset["manifest"]["expected_quality_issues"]
    }
    source_ids = [
        record["source_record_id"]
        for record in dataset["infrastructure_incidents"]
    ]

    assert {
        "duplicate_source_record",
        "missing_required_fields",
        "infrastructure_incident_without_stage_event",
        "stage_event_timestamp_out_of_order",
        "spare_waiting_without_required_spare",
        "validation_without_completed_work",
    } == expected_checks
    assert len(source_ids) != len(set(source_ids))


def test_critical_downtime_follow_up_requests_are_open() -> None:
    dataset = generate_sample_dataset()
    requests_by_scenario = {
        record["payload"]["scenario_key"]: record["payload"]
        for record in dataset["infrastructure_incidents"]
        if "scenario_key" in record["payload"]
    }

    spare_waiting = requests_by_scenario["chiller_spare_waiting_delay"]
    critical = requests_by_scenario["generator_vendor_waiting_delay"]
    engineer_delay = requests_by_scenario["pdu_breaker_assignment_delay"]

    assert spare_waiting["priority_level"] == "CRITICAL"
    assert spare_waiting["current_stage"] == "SPARE_VENDOR_WAITING"
    assert spare_waiting["current_status"] == "IN_PROGRESS"
    assert critical["current_stage"] == "SPARE_VENDOR_WAITING"
    assert engineer_delay["current_stage"] == "ENGINEER_ASSIGNED"


def test_sample_dataset_contains_ai_infrastructure_impact_context() -> None:
    dataset = generate_sample_dataset()
    impacts_by_incident = {
        record["payload"]["incident_id"]: record["payload"]
        for record in dataset["infrastructure_impact_snapshots"]
    }
    expected_trust_issues = {
        (issue["incident_id"], issue["issue_type"])
        for issue in dataset["manifest"]["expected_impact_trust_issues"]
    }
    evidence_event_types = {
        record["payload"]["event_type"]
        for record in dataset["incident_stage_events"]
    }

    assert len(impacts_by_incident) == 10
    assert impacts_by_incident["INC-0007"]["redundancy_state"] == "N-1"
    assert impacts_by_incident["INC-0007"]["vendor_status"] == "ETA_MISSED"
    assert impacts_by_incident["INC-0007"]["affected_gpu_count"] == 320
    assert impacts_by_incident["INC-0004"]["mitigation_status"] == "LOAD_SHIFTED"
    assert {
        "REDUNDANCY_LOST",
        "VENDOR_ETA_MISSED",
        "VENDOR_ETA_UPDATED",
        "LOAD_SHIFTED",
        "MITIGATION_APPLIED",
    }.issubset(evidence_event_types)
    assert {
        ("INC-0003", "impact_mitigation_without_event_evidence"),
        ("INC-0004", "impact_vendor_eta_past_not_missed"),
        ("INC-0007", "impact_mitigation_without_event_evidence"),
    } == expected_trust_issues


def test_write_sample_dataset_creates_expected_files(tmp_path) -> None:
    dataset = generate_sample_dataset()
    written = write_sample_dataset(dataset, tmp_path)

    assert {path.name for path in written} == {
        "manifest.json",
        "infrastructure_zones.json",
        "infrastructure_assets.json",
        "facilities_engineers.json",
        "critical_spares.json",
        "infrastructure_incidents.json",
        "incident_stage_events.json",
        "facility_work_orders.json",
        "validation_results.json",
        "telemetry_alerts.json",
        "infrastructure_impact_snapshots.json",
    }
    assert json.loads((tmp_path / "manifest.json").read_text())["source_system"] == "sample_ai_data_center_infrastructure_system"
