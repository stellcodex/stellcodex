from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Quote(Base):
    __tablename__ = "quotes"

    quote_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    quote_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    owner_sub: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    filename: Mapped[str] = mapped_column(Text, nullable=False)
    process: Mapped[str] = mapped_column(String(32), nullable=False)
    process_label: Mapped[str] = mapped_column(Text, nullable=False)
    material_id: Mapped[str] = mapped_column(String(32), nullable=False)
    material_label: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="EUR")
    payment_terms: Mapped[str] = mapped_column(Text, nullable=False)
    issued_date: Mapped[str] = mapped_column(String(10), nullable=False)
    valid_until: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)

    # Full document stored as JSON
    document_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Geometry snapshot
    geometry_summary: Mapped[dict | None] = mapped_column(JSON)
    # Cost breakdown for qty=1
    breakdown_json: Mapped[dict | None] = mapped_column(JSON)
    # Quantity price breaks
    qty_breaks_json: Mapped[list | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    order_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    order_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quote_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    owner_sub: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_eur: Mapped[float] = mapped_column(Float, nullable=False)
    total_eur: Mapped[float] = mapped_column(Float, nullable=False)
    lead_days: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="EUR")

    status: Mapped[str] = mapped_column(
        String(24), default="queued", index=True
    )
    # queued → material_check → in_production → quality_check → shipped → delivered → invoiced

    notes: Mapped[str | None] = mapped_column(Text)
    customer_po: Mapped[str | None] = mapped_column(Text)  # customer's PO reference

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
