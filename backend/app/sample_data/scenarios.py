from __future__ import annotations

from dataclasses import dataclass


SOURCE_SYSTEM = "sample_procurement_system"

STAGE_FLOW = [
    "REQUEST_SUBMITTED",
    "BUDGET_REVIEW",
    "PROCUREMENT_REVIEW",
    "PO_CREATION",
    "VENDOR_CONFIRMATION",
    "DELIVERY",
    "RECEIVING",
    "INSPECTION",
    "CLOSED",
]

STAGE_THRESHOLDS_HOURS = {
    "REQUEST_SUBMITTED": 2,
    "BUDGET_REVIEW": 24,
    "PROCUREMENT_REVIEW": 48,
    "PO_CREATION": 24,
    "VENDOR_CONFIRMATION": 72,
    "DELIVERY": 168,
    "RECEIVING": 24,
    "INSPECTION": 48,
}

EXIT_EVENT_BY_STAGE = {
    "REQUEST_SUBMITTED": "SUBMITTED",
    "BUDGET_REVIEW": "APPROVED",
    "PROCUREMENT_REVIEW": "APPROVED",
    "PO_CREATION": "PO_CREATED",
    "VENDOR_CONFIRMATION": "VENDOR_CONFIRMED",
    "DELIVERY": "DELIVERED",
    "RECEIVING": "GOODS_RECEIVED",
    "INSPECTION": "INSPECTION_PASSED",
}


@dataclass(frozen=True)
class ScenarioProfile:
    scenario_key: str
    title: str
    department_id: str
    requester_id: str
    item_id: str
    vendor_id: str
    quantity: int
    estimated_amount: int
    criticality_level: str
    business_impact: str
    needed_by_offset_days: int
    stage_durations_hours: dict[str, int]
    stop_stage: str | None = None
    correction_in_procurement_review: bool = False
    inspection_failed_once: bool = False


SCENARIO_PROFILES = [
    ScenarioProfile(
        scenario_key="normal_completed",
        title="Standard monitor replacement",
        department_id="DEPT-IT",
        requester_id="USR-IT-01",
        item_id="ITEM-MONITOR",
        vendor_id="VEN-NOVA",
        quantity=8,
        estimated_amount=2400,
        criticality_level="LOW",
        business_impact="TEAM_PRODUCTIVITY",
        needed_by_offset_days=14,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 8,
            "PROCUREMENT_REVIEW": 20,
            "PO_CREATION": 5,
            "VENDOR_CONFIRMATION": 18,
            "DELIVERY": 72,
            "RECEIVING": 8,
            "INSPECTION": 10,
        },
    ),
    ScenarioProfile(
        scenario_key="budget_review_delay",
        title="Emergency safety cabinet purchase",
        department_id="DEPT-SAFETY",
        requester_id="USR-SAF-01",
        item_id="ITEM-SAFETY-CABINET",
        vendor_id="VEN-APEX",
        quantity=3,
        estimated_amount=18000,
        criticality_level="HIGH",
        business_impact="SAFETY_RISK",
        needed_by_offset_days=5,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 78,
        },
        stop_stage="BUDGET_REVIEW",
    ),
    ScenarioProfile(
        scenario_key="procurement_review_correction",
        title="Production sensor calibration kit",
        department_id="DEPT-MFG",
        requester_id="USR-MFG-01",
        item_id="ITEM-CALIBRATION-KIT",
        vendor_id="VEN-ORBIT",
        quantity=5,
        estimated_amount=12500,
        criticality_level="MEDIUM",
        business_impact="PRODUCTION_RISK",
        needed_by_offset_days=9,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 12,
            "PROCUREMENT_REVIEW": 90,
            "PO_CREATION": 8,
            "VENDOR_CONFIRMATION": 24,
            "DELIVERY": 96,
            "RECEIVING": 10,
            "INSPECTION": 24,
        },
        correction_in_procurement_review=True,
    ),
    ScenarioProfile(
        scenario_key="po_creation_delay",
        title="Network switch expansion",
        department_id="DEPT-INFRA",
        requester_id="USR-INF-01",
        item_id="ITEM-NETWORK-SWITCH",
        vendor_id="VEN-NOVA",
        quantity=4,
        estimated_amount=32000,
        criticality_level="HIGH",
        business_impact="PROJECT_DELAY",
        needed_by_offset_days=7,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 14,
            "PROCUREMENT_REVIEW": 22,
            "PO_CREATION": 60,
            "VENDOR_CONFIRMATION": 18,
            "DELIVERY": 120,
            "RECEIVING": 12,
            "INSPECTION": 18,
        },
    ),
    ScenarioProfile(
        scenario_key="vendor_confirmation_delay",
        title="Security scanner license renewal",
        department_id="DEPT-SEC",
        requester_id="USR-SEC-01",
        item_id="ITEM-SECURITY-LICENSE",
        vendor_id="VEN-SIGNAL",
        quantity=1,
        estimated_amount=45000,
        criticality_level="CRITICAL",
        business_impact="SECURITY_RISK",
        needed_by_offset_days=4,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 6,
            "PROCUREMENT_REVIEW": 16,
            "PO_CREATION": 5,
            "VENDOR_CONFIRMATION": 132,
        },
        stop_stage="VENDOR_CONFIRMATION",
    ),
    ScenarioProfile(
        scenario_key="delivery_delay",
        title="Replacement motor for packaging line",
        department_id="DEPT-MFG",
        requester_id="USR-MFG-02",
        item_id="ITEM-REPLACEMENT-MOTOR",
        vendor_id="VEN-ORBIT",
        quantity=2,
        estimated_amount=56000,
        criticality_level="CRITICAL",
        business_impact="MAINTENANCE_DELAY",
        needed_by_offset_days=3,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 5,
            "PROCUREMENT_REVIEW": 18,
            "PO_CREATION": 6,
            "VENDOR_CONFIRMATION": 20,
            "DELIVERY": 260,
        },
        stop_stage="DELIVERY",
    ),
    ScenarioProfile(
        scenario_key="receiving_delay",
        title="Warehouse handheld scanners",
        department_id="DEPT-OPS",
        requester_id="USR-OPS-01",
        item_id="ITEM-HANDHELD-SCANNER",
        vendor_id="VEN-HARBOR",
        quantity=12,
        estimated_amount=30000,
        criticality_level="MEDIUM",
        business_impact="OPERATIONS_DELAY",
        needed_by_offset_days=8,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 10,
            "PROCUREMENT_REVIEW": 18,
            "PO_CREATION": 6,
            "VENDOR_CONFIRMATION": 30,
            "DELIVERY": 90,
            "RECEIVING": 72,
        },
        stop_stage="RECEIVING",
    ),
    ScenarioProfile(
        scenario_key="inspection_delay",
        title="Fire suppression replacement valves",
        department_id="DEPT-SAFETY",
        requester_id="USR-SAF-02",
        item_id="ITEM-SAFETY-VALVE",
        vendor_id="VEN-APEX",
        quantity=20,
        estimated_amount=22000,
        criticality_level="HIGH",
        business_impact="SAFETY_RISK",
        needed_by_offset_days=6,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 9,
            "PROCUREMENT_REVIEW": 24,
            "PO_CREATION": 5,
            "VENDOR_CONFIRMATION": 22,
            "DELIVERY": 84,
            "RECEIVING": 10,
            "INSPECTION": 104,
        },
        stop_stage="INSPECTION",
        inspection_failed_once=True,
    ),
    ScenarioProfile(
        scenario_key="critical_request_delayed",
        title="Database backup appliance replacement",
        department_id="DEPT-INFRA",
        requester_id="USR-INF-02",
        item_id="ITEM-BACKUP-APPLIANCE",
        vendor_id="VEN-SIGNAL",
        quantity=1,
        estimated_amount=88000,
        criticality_level="CRITICAL",
        business_impact="SERVICE_CONTINUITY_RISK",
        needed_by_offset_days=2,
        stage_durations_hours={
            "REQUEST_SUBMITTED": 1,
            "BUDGET_REVIEW": 8,
            "PROCUREMENT_REVIEW": 20,
            "PO_CREATION": 5,
            "VENDOR_CONFIRMATION": 96,
        },
        stop_stage="VENDOR_CONFIRMATION",
    ),
]
