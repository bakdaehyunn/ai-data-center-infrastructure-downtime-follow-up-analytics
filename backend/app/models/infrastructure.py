from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class InfrastructureZone(TimestampMixin, Base):
    __tablename__ = "infrastructure_zones"
    __table_args__ = (
        UniqueConstraint("zone_code", name="uq_infrastructure_zones_zone_code"),
        Index("ix_infrastructure_zones_priority_status", "zone_priority", "current_status"),
    )

    zone_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_code: Mapped[str] = mapped_column(String(80), nullable=False)
    zone_name: Mapped[str] = mapped_column(String(160), nullable=False)
    facility_area: Mapped[str] = mapped_column(String(120), nullable=False)
    zone_priority: Mapped[str] = mapped_column(String(40), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)

    assets: Mapped[list["InfrastructureAsset"]] = relationship(back_populates="infrastructure_zone")
    infrastructure_incidents: Mapped[list["InfrastructureIncident"]] = relationship(back_populates="infrastructure_zone")
    impact_snapshots: Mapped[list["InfrastructureImpactSnapshot"]] = relationship(back_populates="infrastructure_zone")


class InfrastructureAsset(TimestampMixin, Base):
    __tablename__ = "infrastructure_assets"
    __table_args__ = (
        UniqueConstraint("asset_code", name="uq_infrastructure_assets_asset_code"),
        Index("ix_infrastructure_assets_zone_criticality", "zone_id", "criticality_level"),
        Index("ix_asset_type_status", "asset_type", "current_status"),
    )

    asset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_code: Mapped[str] = mapped_column(String(80), nullable=False)
    asset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(80), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), nullable=False)
    criticality_level: Mapped[str] = mapped_column(String(20), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    model_number: Mapped[str] = mapped_column(String(120), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)

    infrastructure_zone: Mapped[InfrastructureZone] = relationship(back_populates="assets")
    infrastructure_incidents: Mapped[list["InfrastructureIncident"]] = relationship(back_populates="asset")
    telemetry_alerts: Mapped[list["TelemetryAlert"]] = relationship(back_populates="asset")
    impact_snapshots: Mapped[list["InfrastructureImpactSnapshot"]] = relationship(back_populates="asset")


class FacilitiesEngineer(TimestampMixin, Base):
    __tablename__ = "facilities_engineers"
    __table_args__ = (
        Index("ix_facilities_engineers_team_shift", "team_name", "shift"),
        Index("ix_facilities_engineers_skill_status", "skill_group", "active_status"),
    )

    engineer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    engineer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    team_name: Mapped[str] = mapped_column(String(120), nullable=False)
    skill_group: Mapped[str] = mapped_column(String(80), nullable=False)
    shift: Mapped[str] = mapped_column(String(40), nullable=False)
    active_status: Mapped[str] = mapped_column(String(40), nullable=False)

    work_orders: Mapped[list["FacilityWorkOrder"]] = relationship(back_populates="assigned_engineer")
    validations: Mapped[list["ValidationResult"]] = relationship(back_populates="validator")


class CriticalSpare(TimestampMixin, Base):
    __tablename__ = "critical_spares"
    __table_args__ = (
        UniqueConstraint("spare_number", name="uq_critical_spares_spare_number"),
        Index("ix_critical_spares_category_stock", "spare_category", "stock_status"),
        Index("ix_critical_spares_critical_spare", "critical_spare"),
    )

    spare_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    spare_number: Mapped[str] = mapped_column(String(80), nullable=False)
    spare_name: Mapped[str] = mapped_column(String(200), nullable=False)
    spare_category: Mapped[str] = mapped_column(String(80), nullable=False)
    stock_status: Mapped[str] = mapped_column(String(60), nullable=False)
    lead_time_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    critical_spare: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    work_orders: Mapped[list["FacilityWorkOrder"]] = relationship(back_populates="required_spare")


class InfrastructureIncident(TimestampMixin, Base):
    __tablename__ = "infrastructure_incidents"
    __table_args__ = (
        UniqueConstraint("request_number", name="uq_infrastructure_incidents_request_number"),
        Index("ix_infrastructure_incidents_asset_status", "asset_id", "current_status"),
        Index("ix_infrastructure_incidents_zone_stage", "zone_id", "current_stage"),
        Index("ix_infrastructure_incidents_priority_needed", "priority_level", "needed_by_at"),
        Index("ix_infrastructure_incidents_type_failure", "request_type", "failure_mode"),
    )

    incident_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_number: Mapped[str] = mapped_column(String(80), nullable=False)
    asset_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_assets.asset_id"), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), nullable=False)
    request_title: Mapped[str] = mapped_column(String(240), nullable=False)
    request_type: Mapped[str] = mapped_column(String(80), nullable=False)
    priority_level: Mapped[str] = mapped_column(String(20), nullable=False)
    failure_mode: Mapped[str] = mapped_column(String(80), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    needed_by_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(80), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)
    business_impact: Mapped[str] = mapped_column(String(100), nullable=False)
    estimated_downtime_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    actual_downtime_hours: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    asset: Mapped[InfrastructureAsset] = relationship(back_populates="infrastructure_incidents")
    infrastructure_zone: Mapped[InfrastructureZone] = relationship(back_populates="infrastructure_incidents")
    stage_events: Mapped[list["IncidentStageEvent"]] = relationship(back_populates="incident")
    work_orders: Mapped[list["FacilityWorkOrder"]] = relationship(back_populates="incident")
    validation_results: Mapped[list["ValidationResult"]] = relationship(back_populates="incident")
    telemetry_alerts: Mapped[list["TelemetryAlert"]] = relationship(back_populates="linked_incident")
    impact_snapshots: Mapped[list["InfrastructureImpactSnapshot"]] = relationship(back_populates="incident")


class InfrastructureImpactSnapshot(TimestampMixin, Base):
    __tablename__ = "infrastructure_impact_snapshots"
    __table_args__ = (
        Index("ix_infrastructure_impact_incident_snapshot", "incident_id", "snapshot_at"),
        Index("ix_infrastructure_impact_asset_snapshot", "asset_id", "snapshot_at"),
        Index("ix_infrastructure_impact_redundancy", "redundancy_state"),
        Index("ix_infrastructure_impact_vendor_status", "vendor_status"),
        Index("ix_infrastructure_impact_mitigation", "mitigation_status"),
    )

    impact_snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        nullable=False,
    )
    asset_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_assets.asset_id"), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    redundancy_state: Mapped[str] = mapped_column(String(40), nullable=False)
    affected_rack_count: Mapped[int] = mapped_column(Integer, nullable=False)
    affected_gpu_count: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_capacity_risk_kw: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_gpu_capacity_risk_pct: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    thermal_breach_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    power_redundancy_lost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cooling_redundancy_lost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mitigation_status: Mapped[str] = mapped_column(String(60), nullable=False)
    vendor_eta_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    vendor_status: Mapped[str] = mapped_column(String(80), nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    telemetry_readings_json: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON)

    incident: Mapped[InfrastructureIncident] = relationship(back_populates="impact_snapshots")
    asset: Mapped[InfrastructureAsset] = relationship(back_populates="impact_snapshots")
    infrastructure_zone: Mapped[InfrastructureZone] = relationship(back_populates="impact_snapshots")


class IncidentStageEvent(TimestampMixin, Base):
    __tablename__ = "incident_stage_events"
    __table_args__ = (
        Index("ix_incident_stage_events_request_time", "incident_id", "occurred_at"),
        Index("ix_incident_stage_events_stage_time", "stage", "occurred_at"),
        Index("ix_incident_stage_events_type_status", "event_type", "event_status"),
    )

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_status: Mapped[str] = mapped_column(String(60), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(60), nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    reason_code: Mapped[Optional[str]] = mapped_column(String(80))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)

    incident: Mapped[InfrastructureIncident] = relationship(back_populates="stage_events")


class FacilityWorkOrder(TimestampMixin, Base):
    __tablename__ = "facility_work_orders"
    __table_args__ = (
        Index("ix_facility_work_orders_request_status", "incident_id", "work_order_status"),
        Index("ix_facility_work_orders_team_status", "assigned_team", "work_order_status"),
        Index("ix_facility_work_orders_part_status", "required_spare_id", "work_order_status"),
    )

    work_order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        nullable=False,
    )
    assigned_team: Mapped[str] = mapped_column(String(120), nullable=False)
    assigned_engineer_id: Mapped[Optional[str]] = mapped_column(ForeignKey("facilities_engineers.engineer_id"))
    work_order_status: Mapped[str] = mapped_column(String(60), nullable=False)
    planned_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    required_spare_id: Mapped[Optional[str]] = mapped_column(ForeignKey("critical_spares.spare_id"))

    incident: Mapped[InfrastructureIncident] = relationship(back_populates="work_orders")
    assigned_engineer: Mapped[Optional[FacilitiesEngineer]] = relationship(back_populates="work_orders")
    required_spare: Mapped[Optional[CriticalSpare]] = relationship(back_populates="work_orders")


class ValidationResult(TimestampMixin, Base):
    __tablename__ = "validation_results"
    __table_args__ = (
        Index("ix_validation_results_request_status", "incident_id", "validation_status"),
        Index("ix_validation_results_validator_status", "validator_id", "validation_status"),
    )

    validation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        nullable=False,
    )
    validation_status: Mapped[str] = mapped_column(String(60), nullable=False)
    validator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("facilities_engineers.engineer_id"))
    validation_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    validation_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    incident: Mapped[InfrastructureIncident] = relationship(back_populates="validation_results")
    validator: Mapped[Optional[FacilitiesEngineer]] = relationship(back_populates="validations")


class TelemetryAlert(TimestampMixin, Base):
    __tablename__ = "telemetry_alerts"
    __table_args__ = (
        Index("ix_telemetry_alerts_asset_triggered", "asset_id", "triggered_at"),
        Index("ix_telemetry_alerts_severity_status", "severity", "resolved_at"),
        Index("ix_telemetry_alerts_linked_request", "linked_incident_id"),
    )

    telemetry_alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_assets.asset_id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    linked_incident_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id")
    )
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    asset: Mapped[InfrastructureAsset] = relationship(back_populates="telemetry_alerts")
    linked_incident: Mapped[Optional[InfrastructureIncident]] = relationship(back_populates="telemetry_alerts")
