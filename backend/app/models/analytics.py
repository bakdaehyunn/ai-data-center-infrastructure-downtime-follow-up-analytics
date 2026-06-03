from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class IncidentCurrentStatus(TimestampMixin, Base):
    __tablename__ = "incident_current_status"
    __table_args__ = (
        Index("ix_incident_current_status_stage_delayed", "current_stage", "is_delayed"),
        Index("ix_incident_current_status_priority_delay", "priority_level", "delay_hours"),
        Index("ix_incident_current_status_asset_zone", "asset_id", "zone_id"),
    )

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        primary_key=True,
    )
    asset_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_assets.asset_id"), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(80), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hours_in_current_stage: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_delayed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delay_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    needed_by_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority_level: Mapped[str] = mapped_column(String(20), nullable=False)
    business_impact: Mapped[str] = mapped_column(String(100), nullable=False)
    next_owner_type: Mapped[Optional[str]] = mapped_column(String(60))
    next_owner_id: Mapped[Optional[str]] = mapped_column(String(64))


class IncidentStageLeadTime(TimestampMixin, Base):
    __tablename__ = "incident_stage_lead_times"
    __table_args__ = (
        Index("ix_incident_stage_lead_times_request_stage", "incident_id", "stage"),
        Index("ix_incident_stage_lead_times_stage_bottleneck", "stage", "is_bottleneck"),
    )

    lead_time_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    threshold_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_bottleneck: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delay_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class DowntimeFollowUpQueue(TimestampMixin, Base):
    __tablename__ = "downtime_follow_up_queue"
    __table_args__ = (
        Index("ix_downtime_follow_up_queue_rank", "priority_rank"),
        Index("ix_downtime_follow_up_queue_score", "total_priority_score"),
        Index("ix_downtime_follow_up_queue_stage", "current_stage"),
    )

    incident_id: Mapped[str] = mapped_column(
        ForeignKey("infrastructure_incidents.incident_id"),
        primary_key=True,
    )
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    asset_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_assets.asset_id"), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(80), nullable=False)
    asset_criticality_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    downtime_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    stage_delay_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    infrastructure_zone_impact_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    needed_by_urgency_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    repeat_failure_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    spare_risk_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    total_priority_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(240), nullable=False)
    reason_summary: Mapped[str] = mapped_column(Text, nullable=False)


class InfrastructureBottleneckSummary(TimestampMixin, Base):
    __tablename__ = "infrastructure_bottleneck_summary"
    __table_args__ = (
        Index(
            "ix_infrastructure_bottleneck_summary_date_dimension",
            "summary_date",
            "dimension_type",
            "dimension_id",
        ),
        Index("ix_infrastructure_bottleneck_summary_stage_delay", "stage", "total_delay_hours"),
    )

    summary_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)
    dimension_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dimension_id: Mapped[str] = mapped_column(String(80), nullable=False)
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delayed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    avg_duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    p90_duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_delay_hours: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)


class AssetDelaySummary(TimestampMixin, Base):
    __tablename__ = "asset_delay_summary"
    __table_args__ = (
        Index("ix_asset_delay_summary_delayed", "delayed_request_count"),
        Index("ix_asset_delay_summary_downtime", "total_downtime_hours"),
    )

    asset_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_assets.asset_id"), primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), nullable=False)
    zone_name: Mapped[str] = mapped_column(String(160), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delayed_request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    repeat_failure_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_downtime_hours: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    avg_repair_duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    top_failure_mode: Mapped[str] = mapped_column(String(80), nullable=False)


class ZoneDelaySummary(TimestampMixin, Base):
    __tablename__ = "zone_delay_summary"
    __table_args__ = (
        Index("ix_zone_delay_summary_delayed", "delayed_request_count"),
        Index("ix_zone_delay_summary_downtime", "total_downtime_hours"),
    )

    zone_id: Mapped[str] = mapped_column(ForeignKey("infrastructure_zones.zone_id"), primary_key=True)
    zone_name: Mapped[str] = mapped_column(String(160), nullable=False)
    open_request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delayed_request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_asset_delayed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_downtime_hours: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    top_bottleneck_stage: Mapped[str] = mapped_column(String(80), nullable=False)


class SpareWaitingSummary(TimestampMixin, Base):
    __tablename__ = "spare_waiting_summary"
    __table_args__ = (
        Index("ix_spare_waiting_summary_wait_hours", "total_wait_hours"),
        Index("ix_spare_waiting_summary_category_stock", "spare_category", "stock_status"),
    )

    spare_id: Mapped[str] = mapped_column(ForeignKey("critical_spares.spare_id"), primary_key=True)
    spare_name: Mapped[str] = mapped_column(String(200), nullable=False)
    spare_category: Mapped[str] = mapped_column(String(80), nullable=False)
    waiting_request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_wait_hours: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    avg_wait_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    critical_spare: Mapped[bool] = mapped_column(Boolean, nullable=False)
    stock_status: Mapped[str] = mapped_column(String(60), nullable=False)
