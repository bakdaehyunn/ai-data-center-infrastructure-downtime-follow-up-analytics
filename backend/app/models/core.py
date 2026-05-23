from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    department_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    department_type: Mapped[str] = mapped_column(String(80), nullable=False)
    cost_center: Mapped[str] = mapped_column(String(80), nullable=False)

    requesters: Mapped[list["Requester"]] = relationship(back_populates="department")
    purchase_requests: Mapped[list["PurchaseRequest"]] = relationship(back_populates="department")


class Requester(TimestampMixin, Base):
    __tablename__ = "requesters"
    __table_args__ = (Index("ix_requesters_department_id", "department_id"),)

    requester_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requester_name: Mapped[str] = mapped_column(String(160), nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.department_id"), nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)

    department: Mapped[Department] = relationship(back_populates="requesters")
    purchase_requests: Mapped[list["PurchaseRequest"]] = relationship(back_populates="requester")


class Item(TimestampMixin, Base):
    __tablename__ = "items"
    __table_args__ = (Index("ix_items_category_critical", "item_category", "is_critical_item"),)

    item_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_category: Mapped[str] = mapped_column(String(80), nullable=False)
    is_critical_item: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    standard_lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)

    purchase_requests: Mapped[list["PurchaseRequest"]] = relationship(back_populates="item")


class Vendor(TimestampMixin, Base):
    __tablename__ = "vendors"
    __table_args__ = (Index("ix_vendors_reliability_tier", "reliability_tier"),)

    vendor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    vendor_type: Mapped[str] = mapped_column(String(80), nullable=False)
    reliability_tier: Mapped[str] = mapped_column(String(40), nullable=False)
    default_lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)

    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="vendor")


class PurchaseRequest(TimestampMixin, Base):
    __tablename__ = "purchase_requests"
    __table_args__ = (
        UniqueConstraint("request_number", name="uq_purchase_requests_request_number"),
        Index("ix_purchase_requests_current_stage", "current_stage"),
        Index("ix_purchase_requests_criticality_needed_by", "criticality_level", "needed_by_date"),
        Index("ix_purchase_requests_department_status", "department_id", "current_status"),
    )

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_number: Mapped[str] = mapped_column(String(80), nullable=False)
    request_title: Mapped[str] = mapped_column(String(240), nullable=False)
    request_type: Mapped[str] = mapped_column(String(80), nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.department_id"), nullable=False)
    requester_id: Mapped[str] = mapped_column(ForeignKey("requesters.requester_id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.item_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    criticality_level: Mapped[str] = mapped_column(String(20), nullable=False)
    business_impact: Mapped[str] = mapped_column(String(80), nullable=False)
    needed_by_date: Mapped[date] = mapped_column(Date, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(60), nullable=False)
    current_status: Mapped[str] = mapped_column(String(60), nullable=False)

    department: Mapped[Department] = relationship(back_populates="purchase_requests")
    requester: Mapped[Requester] = relationship(back_populates="purchase_requests")
    item: Mapped[Item] = relationship(back_populates="purchase_requests")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="purchase_request")
    stage_events: Mapped[list["ProcurementStageEvent"]] = relationship(back_populates="purchase_request")


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", name="uq_purchase_orders_po_number"),
        Index("ix_purchase_orders_request_id", "request_id"),
        Index("ix_purchase_orders_vendor_status", "vendor_id", "po_status"),
    )

    po_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    po_number: Mapped[str] = mapped_column(String(80), nullable=False)
    request_id: Mapped[str] = mapped_column(ForeignKey("purchase_requests.request_id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.vendor_id"), nullable=False)
    po_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    vendor_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    po_status: Mapped[str] = mapped_column(String(60), nullable=False)

    purchase_request: Mapped[PurchaseRequest] = relationship(back_populates="purchase_orders")
    vendor: Mapped[Vendor] = relationship(back_populates="purchase_orders")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="purchase_order")


class Receipt(TimestampMixin, Base):
    __tablename__ = "receipts"
    __table_args__ = (Index("ix_receipts_po_inspection", "po_id", "inspection_status"),)

    receipt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    po_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.po_id"), nullable=False)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    inspection_status: Mapped[str] = mapped_column(String(60), nullable=False)
    inspection_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="receipts")


class ProcurementStageEvent(TimestampMixin, Base):
    __tablename__ = "procurement_stage_events"
    __table_args__ = (
        Index("ix_procurement_stage_events_request_time", "request_id", "occurred_at"),
        Index("ix_procurement_stage_events_stage_time", "stage", "occurred_at"),
        Index("ix_procurement_stage_events_type_status", "event_type", "event_status"),
    )

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("purchase_requests.request_id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(60), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_status: Mapped[str] = mapped_column(String(60), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(60), nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    reason_code: Mapped[Optional[str]] = mapped_column(String(80))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)

    purchase_request: Mapped[PurchaseRequest] = relationship(back_populates="stage_events")
