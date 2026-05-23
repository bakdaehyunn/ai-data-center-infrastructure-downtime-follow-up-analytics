from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class RequestCurrentStatus(TimestampMixin, Base):
    __tablename__ = "request_current_status"
    __table_args__ = (
        Index("ix_request_current_status_stage_delayed", "current_stage", "is_delayed"),
        Index("ix_request_current_status_criticality_delay", "criticality_level", "delay_days"),
    )

    request_id: Mapped[str] = mapped_column(ForeignKey("purchase_requests.request_id"), primary_key=True)
    current_stage: Mapped[str] = mapped_column(String(60), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    days_in_current_stage: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_delayed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delay_days: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    needed_by_date: Mapped[date] = mapped_column(Date, nullable=False)
    criticality_level: Mapped[str] = mapped_column(String(20), nullable=False)
    business_impact: Mapped[str] = mapped_column(String(80), nullable=False)
    next_owner_type: Mapped[Optional[str]] = mapped_column(String(60))
    next_owner_id: Mapped[Optional[str]] = mapped_column(String(64))


class RequestStageLeadTime(TimestampMixin, Base):
    __tablename__ = "request_stage_lead_times"
    __table_args__ = (
        Index("ix_request_stage_lead_times_request_stage", "request_id", "stage"),
        Index("ix_request_stage_lead_times_stage_bottleneck", "stage", "is_bottleneck"),
    )

    lead_time_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("purchase_requests.request_id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(60), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    threshold_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_bottleneck: Mapped[bool] = mapped_column(Boolean, nullable=False)
    delay_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class CriticalRequestQueue(TimestampMixin, Base):
    __tablename__ = "critical_request_queue"
    __table_args__ = (
        Index("ix_critical_request_queue_rank", "priority_rank"),
        Index("ix_critical_request_queue_score", "total_priority_score"),
    )

    request_id: Mapped[str] = mapped_column(ForeignKey("purchase_requests.request_id"), primary_key=True)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    criticality_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    delay_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    business_impact_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    needed_by_urgency_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    vendor_risk_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    total_priority_score: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(240), nullable=False)
    reason_summary: Mapped[str] = mapped_column(Text, nullable=False)


class BottleneckSummary(TimestampMixin, Base):
    __tablename__ = "bottleneck_summary"
    __table_args__ = (
        Index("ix_bottleneck_summary_date_dimension", "summary_date", "dimension_type", "dimension_id"),
        Index("ix_bottleneck_summary_stage_delay", "stage", "total_delay_hours"),
    )

    summary_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)
    dimension_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dimension_id: Mapped[str] = mapped_column(String(80), nullable=False)
    stage: Mapped[str] = mapped_column(String(60), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delayed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    p90_duration_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_delay_hours: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)


class VendorDelaySummary(TimestampMixin, Base):
    __tablename__ = "vendor_delay_summary"
    __table_args__ = (Index("ix_vendor_delay_summary_delay_rate", "delay_rate"),)

    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.vendor_id"), primary_key=True)
    total_po_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delayed_po_count: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    avg_confirmation_hours: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    avg_delivery_delay_days: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reliability_tier: Mapped[str] = mapped_column(String(40), nullable=False)
