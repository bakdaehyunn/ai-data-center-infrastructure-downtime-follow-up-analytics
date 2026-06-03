from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawIngestionMixin:
    source_record_id: Mapped[str] = mapped_column(String(120), nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    pipeline_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class RawInfrastructureIncident(RawIngestionMixin, Base):
    __tablename__ = "raw_infrastructure_incidents"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_infrastructure_request_source_record"),
        Index("ix_raw_infrastructure_request_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawIncidentStageEvent(RawIngestionMixin, Base):
    __tablename__ = "raw_incident_stage_events"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_infrastructure_stage_event_source_record"),
        Index("ix_raw_infrastructure_stage_event_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawFacilityWorkOrder(RawIngestionMixin, Base):
    __tablename__ = "raw_facility_work_orders"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_infrastructure_work_order_source_record"),
        Index("ix_raw_infrastructure_work_order_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawValidationResult(RawIngestionMixin, Base):
    __tablename__ = "raw_validation_results"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_validation_result_source_record"),
        Index("ix_raw_validation_result_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawTelemetryAlert(RawIngestionMixin, Base):
    __tablename__ = "raw_telemetry_alerts"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_telemetry_alert_source_record"),
        Index("ix_raw_telemetry_alert_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
