from __future__ import annotations

from dataclasses import dataclass


MAINTENANCE_SOURCE_SYSTEM = "sample_industrial_maintenance_system"

MAINTENANCE_STAGE_FLOW = [
    "MAINTENANCE_REQUEST_SUBMITTED",
    "MAINTENANCE_REVIEW",
    "TECHNICIAN_ASSIGNED",
    "PARTS_WAITING",
    "MAINTENANCE_IN_PROGRESS",
    "INSPECTION",
    "COMPLETED",
]

MAINTENANCE_STAGE_THRESHOLDS_HOURS = {
    "MAINTENANCE_REQUEST_SUBMITTED": 2,
    "MAINTENANCE_REVIEW": 12,
    "TECHNICIAN_ASSIGNED": 8,
    "PARTS_WAITING": 24,
    "MAINTENANCE_IN_PROGRESS": 36,
    "INSPECTION": 12,
}

MAINTENANCE_EXIT_EVENT_BY_STAGE = {
    "MAINTENANCE_REQUEST_SUBMITTED": "REQUEST_SUBMITTED",
    "MAINTENANCE_REVIEW": "REVIEW_APPROVED",
    "TECHNICIAN_ASSIGNED": "TECHNICIAN_ASSIGNED",
    "PARTS_WAITING": "PARTS_RESERVED",
    "MAINTENANCE_IN_PROGRESS": "WORK_COMPLETED",
    "INSPECTION": "INSPECTION_PASSED",
}


@dataclass(frozen=True)
class MaintenanceScenarioProfile:
    scenario_key: str
    title: str
    equipment_id: str
    required_part_id: str | None
    assigned_technician_id: str | None
    request_type: str
    priority_level: str
    failure_mode: str
    business_impact: str
    needed_by_offset_hours: int
    estimated_downtime_hours: int
    stage_durations_hours: dict[str, int]
    stop_stage: str | None = None
    inspection_failed_once: bool = False
    sensor_alert_type: str | None = None


MAINTENANCE_SCENARIO_PROFILES = [
    MaintenanceScenarioProfile(
        scenario_key="normal_completed_maintenance",
        title="Routine conveyor bearing replacement",
        equipment_id="EQ-CNV-001",
        required_part_id="PART-BEARING-6205",
        assigned_technician_id="TECH-MECH-01",
        request_type="PREVENTIVE",
        priority_level="MEDIUM",
        failure_mode="BEARING_WEAR",
        business_impact="PLANNED_MAINTENANCE",
        needed_by_offset_hours=120,
        estimated_downtime_hours=4,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 4,
            "TECHNICIAN_ASSIGNED": 3,
            "PARTS_WAITING": 2,
            "MAINTENANCE_IN_PROGRESS": 5,
            "INSPECTION": 2,
        },
    ),
    MaintenanceScenarioProfile(
        scenario_key="maintenance_review_delay",
        title="Hydraulic press abnormal vibration review",
        equipment_id="EQ-PRS-001",
        required_part_id="PART-HYD-SEAL",
        assigned_technician_id=None,
        request_type="CORRECTIVE",
        priority_level="HIGH",
        failure_mode="ABNORMAL_VIBRATION",
        business_impact="QUALITY_RISK",
        needed_by_offset_hours=36,
        estimated_downtime_hours=10,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 38,
        },
        stop_stage="MAINTENANCE_REVIEW",
        sensor_alert_type="VIBRATION",
    ),
    MaintenanceScenarioProfile(
        scenario_key="technician_assignment_delay",
        title="Robot arm encoder fault assignment",
        equipment_id="EQ-RBT-001",
        required_part_id="PART-ENCODER-RBT",
        assigned_technician_id=None,
        request_type="BREAKDOWN",
        priority_level="HIGH",
        failure_mode="ENCODER_FAULT",
        business_impact="LINE_THROUGHPUT_RISK",
        needed_by_offset_hours=24,
        estimated_downtime_hours=14,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 5,
            "TECHNICIAN_ASSIGNED": 29,
        },
        stop_stage="TECHNICIAN_ASSIGNED",
        sensor_alert_type="POSITION_ERROR",
    ),
    MaintenanceScenarioProfile(
        scenario_key="parts_waiting_delay",
        title="Packaging line servo motor replacement",
        equipment_id="EQ-PKG-001",
        required_part_id="PART-SERVO-7KW",
        assigned_technician_id="TECH-ELEC-01",
        request_type="BREAKDOWN",
        priority_level="CRITICAL",
        failure_mode="MOTOR_FAILURE",
        business_impact="LINE_STOPPED",
        needed_by_offset_hours=12,
        estimated_downtime_hours=22,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 3,
            "TECHNICIAN_ASSIGNED": 4,
            "PARTS_WAITING": 86,
        },
        stop_stage="PARTS_WAITING",
        sensor_alert_type="DRIVE_FAULT",
    ),
    MaintenanceScenarioProfile(
        scenario_key="maintenance_in_progress_delay",
        title="Filler pump seal corrective repair",
        equipment_id="EQ-FIL-001",
        required_part_id="PART-PUMP-SEAL",
        assigned_technician_id="TECH-MECH-02",
        request_type="CORRECTIVE",
        priority_level="HIGH",
        failure_mode="LEAKAGE",
        business_impact="SCRAP_RISK",
        needed_by_offset_hours=48,
        estimated_downtime_hours=16,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 4,
            "TECHNICIAN_ASSIGNED": 3,
            "PARTS_WAITING": 4,
            "MAINTENANCE_IN_PROGRESS": 72,
        },
        stop_stage="MAINTENANCE_IN_PROGRESS",
    ),
    MaintenanceScenarioProfile(
        scenario_key="inspection_delay",
        title="Safety interlock repair inspection",
        equipment_id="EQ-SAFE-001",
        required_part_id="PART-SAFETY-RELAY",
        assigned_technician_id="TECH-ELEC-02",
        request_type="INSPECTION_FINDING",
        priority_level="HIGH",
        failure_mode="INTERLOCK_FAILURE",
        business_impact="SAFETY_RISK",
        needed_by_offset_hours=30,
        estimated_downtime_hours=8,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 3,
            "TECHNICIAN_ASSIGNED": 2,
            "PARTS_WAITING": 3,
            "MAINTENANCE_IN_PROGRESS": 10,
            "INSPECTION": 44,
        },
        stop_stage="INSPECTION",
        inspection_failed_once=True,
    ),
    MaintenanceScenarioProfile(
        scenario_key="critical_equipment_delayed",
        title="Main compressor overheating",
        equipment_id="EQ-CMP-001",
        required_part_id="PART-FILTER-CMP",
        assigned_technician_id="TECH-MECH-03",
        request_type="BREAKDOWN",
        priority_level="CRITICAL",
        failure_mode="OVERHEATING",
        business_impact="PLANT_AIR_RISK",
        needed_by_offset_hours=8,
        estimated_downtime_hours=30,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 2,
            "TECHNICIAN_ASSIGNED": 4,
            "PARTS_WAITING": 58,
        },
        stop_stage="PARTS_WAITING",
        sensor_alert_type="TEMPERATURE",
    ),
    MaintenanceScenarioProfile(
        scenario_key="repeat_failure_equipment",
        title="Conveyor belt tracking repeated failure",
        equipment_id="EQ-CNV-001",
        required_part_id="PART-BELT-GUIDE",
        assigned_technician_id="TECH-MECH-01",
        request_type="CORRECTIVE",
        priority_level="HIGH",
        failure_mode="BELT_MISTRACKING",
        business_impact="LINE_THROUGHPUT_RISK",
        needed_by_offset_hours=40,
        estimated_downtime_hours=12,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 4,
            "TECHNICIAN_ASSIGNED": 4,
            "PARTS_WAITING": 3,
            "MAINTENANCE_IN_PROGRESS": 18,
            "INSPECTION": 4,
        },
    ),
    MaintenanceScenarioProfile(
        scenario_key="line_delay_concentration",
        title="Packaging labeler intermittent stop",
        equipment_id="EQ-PKG-002",
        required_part_id="PART-LABEL-SENSOR",
        assigned_technician_id="TECH-ELEC-01",
        request_type="CORRECTIVE",
        priority_level="MEDIUM",
        failure_mode="SENSOR_MISREAD",
        business_impact="PACKAGING_DELAY",
        needed_by_offset_hours=56,
        estimated_downtime_hours=9,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 5,
            "TECHNICIAN_ASSIGNED": 12,
        },
        stop_stage="TECHNICIAN_ASSIGNED",
        sensor_alert_type="PHOTOEYE_SIGNAL_LOSS",
    ),
    MaintenanceScenarioProfile(
        scenario_key="sensor_triggered_maintenance",
        title="Mixer motor vibration alert follow-up",
        equipment_id="EQ-MIX-001",
        required_part_id="PART-MOTOR-MOUNT",
        assigned_technician_id="TECH-MECH-02",
        request_type="SENSOR_TRIGGERED",
        priority_level="MEDIUM",
        failure_mode="VIBRATION_TREND",
        business_impact="PREDICTED_FAILURE_RISK",
        needed_by_offset_hours=72,
        estimated_downtime_hours=6,
        stage_durations_hours={
            "MAINTENANCE_REQUEST_SUBMITTED": 1,
            "MAINTENANCE_REVIEW": 5,
            "TECHNICIAN_ASSIGNED": 4,
            "PARTS_WAITING": 5,
            "MAINTENANCE_IN_PROGRESS": 8,
            "INSPECTION": 3,
        },
        sensor_alert_type="VIBRATION",
    ),
]
