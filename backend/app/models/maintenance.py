from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ProductionLine(TimestampMixin, Base):
    __tablename__ = "production_lines"
    __table_args__ = (
        UniqueConstraint("line_code", name="uq_production_lines_line_code"),
        Index("ix_production_lines_priority_status", "line_priority", "current_status"),
    )

    line_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    line_code: Mapped[str] = mapped_column(String(80), nullable=False)
    line_name: Mapped[str] = mapped_column(String(160), nullable=False)
    plant_area: Mapped[str] = mapped_column(String(120), nullable=False)
    line_priority: Mapped[str] = mapped_column(String(40), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)

    equipment: Mapped[list["Equipment"]] = relationship(back_populates="production_line")
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(back_populates="production_line")


class Equipment(TimestampMixin, Base):
    __tablename__ = "equipment"
    __table_args__ = (
        UniqueConstraint("equipment_code", name="uq_equipment_equipment_code"),
        Index("ix_equipment_line_criticality", "line_id", "criticality_level"),
        Index("ix_equipment_type_status", "equipment_type", "current_status"),
    )

    equipment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    equipment_code: Mapped[str] = mapped_column(String(80), nullable=False)
    equipment_name: Mapped[str] = mapped_column(String(200), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(80), nullable=False)
    line_id: Mapped[str] = mapped_column(ForeignKey("production_lines.line_id"), nullable=False)
    criticality_level: Mapped[str] = mapped_column(String(20), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(120), nullable=False)
    model_number: Mapped[str] = mapped_column(String(120), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)

    production_line: Mapped[ProductionLine] = relationship(back_populates="equipment")
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(back_populates="equipment")
    sensor_alerts: Mapped[list["SensorAlert"]] = relationship(back_populates="equipment")


class Technician(TimestampMixin, Base):
    __tablename__ = "technicians"
    __table_args__ = (
        Index("ix_technicians_team_shift", "team_name", "shift"),
        Index("ix_technicians_skill_status", "skill_group", "active_status"),
    )

    technician_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    technician_name: Mapped[str] = mapped_column(String(160), nullable=False)
    team_name: Mapped[str] = mapped_column(String(120), nullable=False)
    skill_group: Mapped[str] = mapped_column(String(80), nullable=False)
    shift: Mapped[str] = mapped_column(String(40), nullable=False)
    active_status: Mapped[str] = mapped_column(String(40), nullable=False)

    work_orders: Mapped[list["MaintenanceWorkOrder"]] = relationship(back_populates="assigned_technician")
    inspections: Mapped[list["InspectionResult"]] = relationship(back_populates="inspector")


class Part(TimestampMixin, Base):
    __tablename__ = "parts"
    __table_args__ = (
        UniqueConstraint("part_number", name="uq_parts_part_number"),
        Index("ix_parts_category_stock", "part_category", "stock_status"),
        Index("ix_parts_critical_spare", "critical_spare"),
    )

    part_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    part_number: Mapped[str] = mapped_column(String(80), nullable=False)
    part_name: Mapped[str] = mapped_column(String(200), nullable=False)
    part_category: Mapped[str] = mapped_column(String(80), nullable=False)
    stock_status: Mapped[str] = mapped_column(String(60), nullable=False)
    lead_time_days: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    critical_spare: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    work_orders: Mapped[list["MaintenanceWorkOrder"]] = relationship(back_populates="required_part")


class MaintenanceRequest(TimestampMixin, Base):
    __tablename__ = "maintenance_requests"
    __table_args__ = (
        UniqueConstraint("request_number", name="uq_maintenance_requests_request_number"),
        Index("ix_maintenance_requests_equipment_status", "equipment_id", "current_status"),
        Index("ix_maintenance_requests_line_stage", "line_id", "current_stage"),
        Index("ix_maintenance_requests_priority_needed", "priority_level", "needed_by_at"),
        Index("ix_maintenance_requests_type_failure", "request_type", "failure_mode"),
    )

    maintenance_request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_number: Mapped[str] = mapped_column(String(80), nullable=False)
    equipment_id: Mapped[str] = mapped_column(ForeignKey("equipment.equipment_id"), nullable=False)
    line_id: Mapped[str] = mapped_column(ForeignKey("production_lines.line_id"), nullable=False)
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

    equipment: Mapped[Equipment] = relationship(back_populates="maintenance_requests")
    production_line: Mapped[ProductionLine] = relationship(back_populates="maintenance_requests")
    stage_events: Mapped[list["MaintenanceStageEvent"]] = relationship(back_populates="maintenance_request")
    work_orders: Mapped[list["MaintenanceWorkOrder"]] = relationship(back_populates="maintenance_request")
    inspection_results: Mapped[list["InspectionResult"]] = relationship(back_populates="maintenance_request")
    sensor_alerts: Mapped[list["SensorAlert"]] = relationship(back_populates="linked_maintenance_request")


class MaintenanceStageEvent(TimestampMixin, Base):
    __tablename__ = "maintenance_stage_events"
    __table_args__ = (
        Index("ix_maintenance_stage_events_request_time", "maintenance_request_id", "occurred_at"),
        Index("ix_maintenance_stage_events_stage_time", "stage", "occurred_at"),
        Index("ix_maintenance_stage_events_type_status", "event_type", "event_status"),
    )

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    maintenance_request_id: Mapped[str] = mapped_column(
        ForeignKey("maintenance_requests.maintenance_request_id"),
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

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="stage_events")


class MaintenanceWorkOrder(TimestampMixin, Base):
    __tablename__ = "maintenance_work_orders"
    __table_args__ = (
        Index("ix_maintenance_work_orders_request_status", "maintenance_request_id", "work_order_status"),
        Index("ix_maintenance_work_orders_team_status", "assigned_team", "work_order_status"),
        Index("ix_maintenance_work_orders_part_status", "required_part_id", "work_order_status"),
    )

    work_order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    maintenance_request_id: Mapped[str] = mapped_column(
        ForeignKey("maintenance_requests.maintenance_request_id"),
        nullable=False,
    )
    assigned_team: Mapped[str] = mapped_column(String(120), nullable=False)
    assigned_technician_id: Mapped[Optional[str]] = mapped_column(ForeignKey("technicians.technician_id"))
    work_order_status: Mapped[str] = mapped_column(String(60), nullable=False)
    planned_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    required_part_id: Mapped[Optional[str]] = mapped_column(ForeignKey("parts.part_id"))

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="work_orders")
    assigned_technician: Mapped[Optional[Technician]] = relationship(back_populates="work_orders")
    required_part: Mapped[Optional[Part]] = relationship(back_populates="work_orders")


class InspectionResult(TimestampMixin, Base):
    __tablename__ = "inspection_results"
    __table_args__ = (
        Index("ix_inspection_results_request_status", "maintenance_request_id", "inspection_status"),
        Index("ix_inspection_results_inspector_status", "inspector_id", "inspection_status"),
    )

    inspection_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    maintenance_request_id: Mapped[str] = mapped_column(
        ForeignKey("maintenance_requests.maintenance_request_id"),
        nullable=False,
    )
    inspection_status: Mapped[str] = mapped_column(String(60), nullable=False)
    inspector_id: Mapped[Optional[str]] = mapped_column(ForeignKey("technicians.technician_id"))
    inspection_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    inspection_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="inspection_results")
    inspector: Mapped[Optional[Technician]] = relationship(back_populates="inspections")


class SensorAlert(TimestampMixin, Base):
    __tablename__ = "sensor_alerts"
    __table_args__ = (
        Index("ix_sensor_alerts_equipment_triggered", "equipment_id", "triggered_at"),
        Index("ix_sensor_alerts_severity_status", "severity", "resolved_at"),
        Index("ix_sensor_alerts_linked_request", "linked_maintenance_request_id"),
    )

    sensor_alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(ForeignKey("equipment.equipment_id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    linked_maintenance_request_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("maintenance_requests.maintenance_request_id")
    )
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    equipment: Mapped[Equipment] = relationship(back_populates="sensor_alerts")
    linked_maintenance_request: Mapped[Optional[MaintenanceRequest]] = relationship(back_populates="sensor_alerts")
