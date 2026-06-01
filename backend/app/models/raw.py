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


class RawPurchaseRequest(RawIngestionMixin, Base):
    __tablename__ = "raw_purchase_requests"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_pr_source_record"),
        Index("ix_raw_pr_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawPurchaseOrder(RawIngestionMixin, Base):
    __tablename__ = "raw_purchase_orders"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_po_source_record"),
        Index("ix_raw_po_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawVendorUpdate(RawIngestionMixin, Base):
    __tablename__ = "raw_vendor_updates"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_vendor_update_source_record"),
        Index("ix_raw_vendor_update_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawReceipt(RawIngestionMixin, Base):
    __tablename__ = "raw_receipts"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_receipt_source_record"),
        Index("ix_raw_receipt_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawStageEvent(RawIngestionMixin, Base):
    __tablename__ = "raw_stage_events"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_stage_event_source_record"),
        Index("ix_raw_stage_event_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawMaintenanceRequest(RawIngestionMixin, Base):
    __tablename__ = "raw_maintenance_requests"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_maintenance_request_source_record"),
        Index("ix_raw_maintenance_request_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawMaintenanceStageEvent(RawIngestionMixin, Base):
    __tablename__ = "raw_maintenance_stage_events"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_maintenance_stage_event_source_record"),
        Index("ix_raw_maintenance_stage_event_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawMaintenanceWorkOrder(RawIngestionMixin, Base):
    __tablename__ = "raw_maintenance_work_orders"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_maintenance_work_order_source_record"),
        Index("ix_raw_maintenance_work_order_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawInspectionResult(RawIngestionMixin, Base):
    __tablename__ = "raw_inspection_results"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_inspection_result_source_record"),
        Index("ix_raw_inspection_result_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class RawSensorAlert(RawIngestionMixin, Base):
    __tablename__ = "raw_sensor_alerts"
    __table_args__ = (
        UniqueConstraint("source_system", "source_record_id", name="uq_raw_sensor_alert_source_record"),
        Index("ix_raw_sensor_alert_pipeline_source", "pipeline_run_id", "source_system"),
    )

    raw_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
