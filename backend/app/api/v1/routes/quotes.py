"""
app/api/v1/routes/quotes.py

Quote generation, retrieval, and approval endpoints.

Pipeline Stages: 07 (library match) → 08 (mfg planning) → 09 (cost) → 11 (quote) → 13 (approve)

Endpoints:
  POST   /api/v1/quotes/generate             Generate a quote for a file
  GET    /api/v1/quotes/{quote_id}           Retrieve a quote
  GET    /api/v1/quotes                      List quotes (for owner)
  POST   /api/v1/quotes/{quote_id}/approve   Approve → create production order
  POST   /api/v1/quotes/{quote_id}/reject    Reject quote
  GET    /api/v1/orders                      List production orders
  GET    /api/v1/orders/{order_id}           Get order status
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import tempfile
import os

from app.core.config import settings
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.quote import Quote, ProductionOrder
from app.security.deps import Principal, get_current_principal
from app.services.cost_estimator import MATERIAL_DB, DEFAULT_MATERIAL, estimate_cost
from app.services.mfg_classifier import classify_manufacturing_process
from app.services.quote_generator import generate_quote

router = APIRouter(tags=["quotes"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class GenerateQuoteRequest(BaseModel):
    file_id: str
    material_id: str = DEFAULT_MATERIAL
    quantities: list[int] = Field(default=[1, 5, 10, 25, 50])
    override_process: str | None = None
    customer_email: str | None = None
    customer_name: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "scx_00be2ea4-4572-46af-beff-25fe881bd85c",
                "material_id": "steel_1018",
                "quantities": [1, 5, 10, 25, 50],
            }
        }


class ApproveQuoteRequest(BaseModel):
    qty: int
    customer_po: str | None = None
    notes: str | None = None


class QuoteOut(BaseModel):
    quote_id: str
    quote_number: str
    file_id: str
    filename: str
    process: str
    process_label: str
    material_id: str
    material_label: str
    currency: str
    issued_date: str
    valid_until: str
    status: str
    qty_breaks: list[dict]
    geometry_summary: dict | None
    breakdown_qty1: dict | None
    dfm_notes: list[str]
    technical_notes: list[str]
    whatsapp_text: str
    created_at: str


class OrderOut(BaseModel):
    order_id: str
    order_number: str
    quote_id: str
    file_id: str
    qty: int
    unit_price_eur: float
    total_eur: float
    lead_days: int
    currency: str
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _owner_key(principal: Principal) -> str:
    if principal.typ == "user" and principal.user_id:
        return f"user:{principal.user_id}"
    if principal.owner_sub:
        return f"guest:{principal.owner_sub}"
    raise HTTPException(status_code=401, detail="Unauthorized")


def _get_file(db: Session, file_id: str, principal: Principal) -> UploadFileModel:
    """Resolve file_id (canonical scx_ or plain UUID) and check access."""
    # Try canonical format first
    f = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        # Try with scx_ prefix
        for prefix in ("scx_", ""):
            candidate = f"{prefix}{file_id}" if not file_id.startswith("scx_") else file_id
            f = db.query(UploadFileModel).filter(UploadFileModel.file_id == candidate).first()
            if f:
                break
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.status != "ready":
        raise HTTPException(status_code=422, detail=f"File not ready for quoting (status: {f.status})")
    return f


def _is_rich_geometry(geo: dict) -> bool:
    """Return True if geometry has detailed features (holes, surfaces, volume)."""
    if not geo:
        return False
    holes = geo.get("holes")
    surfaces = geo.get("surfaces")
    volume = geo.get("volume")
    return bool(
        (isinstance(holes, list) and len(holes) > 0)
        or (isinstance(surfaces, dict) and any(surfaces.values()))
        or (volume and float(volume) > 0)
    )


def _extract_geometry_from_file(f: UploadFileModel) -> dict | None:
    """
    Download the original file from S3 and run step_extractor to get
    rich geometry data. Only runs for STEP/STP files.
    Returns None if extraction fails or file is not STEP.
    """
    filename = f.original_filename or ""
    ext = (os.path.splitext(filename)[-1] or "").lower().lstrip(".")
    if ext not in ("step", "stp"):
        return None
    try:
        from app.services.step_extractor import geometry_meta_from_step
        s3 = get_s3_client(settings)
        with tempfile.TemporaryDirectory() as tmp:
            local = os.path.join(tmp, f"input.{ext}")
            s3.download_file(f.bucket, f.object_key, local)
            return geometry_meta_from_step(local)
    except Exception:
        return None


def _extract_geometry_meta(f: UploadFileModel) -> dict:
    """
    Extract the richest available geometry_meta from file metadata.
    Falls back to live re-extraction if stored data is insufficient.
    """
    meta = f.meta if isinstance(f.meta, dict) else {}

    # Check stored geometry_meta_json
    geo_meta = meta.get("geometry_meta_json")
    if isinstance(geo_meta, dict) and _is_rich_geometry(geo_meta):
        return geo_meta

    # Try live extraction (re-run step_extractor on the actual file)
    live_geo = _extract_geometry_from_file(f)
    if live_geo and _is_rich_geometry(live_geo):
        return live_geo

    # Use stored data even if limited
    if isinstance(geo_meta, dict) and geo_meta.get("bbox"):
        return geo_meta

    # Fall back to artifacts
    artifacts = meta.get("artifacts", {})
    if isinstance(artifacts, dict):
        geo_report = artifacts.get("geometry_report", {})
        if isinstance(geo_report, dict):
            geom = geo_report.get("geometry", {})
            return {"bbox": geom, "units": geom.get("units", "mm"), "part_count": geom.get("part_count", 1)}

    return {}


def _order_number(quote_number: str, order_seq: int) -> str:
    return f"ORD-{quote_number.replace('Q-', '')}-{order_seq:03d}"


def _quote_to_out(q: Quote) -> QuoteOut:
    doc = q.document_json or {}
    return QuoteOut(
        quote_id       = q.quote_id,
        quote_number   = q.quote_number,
        file_id        = q.file_id,
        filename       = q.filename,
        process        = q.process,
        process_label  = q.process_label,
        material_id    = q.material_id,
        material_label = q.material_label,
        currency       = q.currency,
        issued_date    = q.issued_date,
        valid_until    = q.valid_until,
        status         = q.status,
        qty_breaks     = q.qty_breaks_json or [],
        geometry_summary = q.geometry_summary,
        breakdown_qty1 = q.breakdown_json,
        dfm_notes      = doc.get("dfm_notes", []),
        technical_notes = doc.get("technical_notes", []),
        whatsapp_text  = doc.get("whatsapp_text", ""),
        created_at     = q.created_at.isoformat() if q.created_at else "",
    )


def _order_to_out(o: ProductionOrder) -> OrderOut:
    return OrderOut(
        order_id       = o.order_id,
        order_number   = o.order_number,
        quote_id       = o.quote_id,
        file_id        = o.file_id,
        qty            = o.qty,
        unit_price_eur = o.unit_price_eur,
        total_eur      = o.total_eur,
        lead_days      = o.lead_days,
        currency       = o.currency,
        status         = o.status,
        created_at     = o.created_at.isoformat() if o.created_at else "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/materials", summary="List available materials for quoting")
def list_materials() -> dict:
    """Return all materials available for cost estimation."""
    return {
        "materials": [
            {"id": k, "label": v["label"], "density_g_cm3": v["density"], "eur_per_kg": v["eur_per_kg"]}
            for k, v in MATERIAL_DB.items()
        ]
    }


@router.post("/generate", response_model=QuoteOut, summary="Generate a manufacturing quotation")
def generate_quote_endpoint(
    body: GenerateQuoteRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> QuoteOut:
    """
    Generate an automated manufacturing quotation for an uploaded file.

    Pipeline: geometry_meta → mfg_classifier → cost_estimator → quote_generator → store → return
    """
    owner = _owner_key(principal)
    f = _get_file(db, body.file_id, principal)
    geometry_meta = _extract_geometry_meta(f)

    if not geometry_meta or not geometry_meta.get("bbox"):
        raise HTTPException(
            status_code=422,
            detail=(
                "Geometry data not available for this file. "
                "Only STEP/STP files produce automated quotes. "
                "Re-upload as STEP to enable quoting."
            ),
        )

    # Classify manufacturing process
    process_result = classify_manufacturing_process(
        geometry_meta,
        override_process=body.override_process,
    )

    # Estimate cost
    qty_list = sorted(set(max(1, q) for q in body.quantities))[:10]
    estimate = estimate_cost(
        geometry_meta   = geometry_meta,
        process         = process_result.process,
        process_label   = process_result.process_label,
        setup_count     = process_result.setup_count,
        material_id     = body.material_id,
        quantities      = qty_list,
    )

    # Generate quote document
    doc = generate_quote(
        file_id          = f.file_id,
        filename         = f.original_filename,
        quote_estimate   = estimate,
        process_result   = process_result,
        geometry_meta    = geometry_meta,
    )

    # Persist to DB
    doc_dict = doc.to_dict()
    doc_dict["whatsapp_text"] = doc.to_whatsapp_text()

    quote = Quote(
        quote_id        = doc.quote_id,
        quote_number    = doc.quote_number,
        file_id         = f.file_id,
        owner_sub       = owner,
        filename        = f.original_filename,
        process         = doc.process,
        process_label   = doc.process_label,
        material_id     = doc.material_id,
        material_label  = doc.material_label,
        currency        = doc.currency,
        payment_terms   = doc.payment_terms,
        issued_date     = doc.issued_date,
        valid_until     = doc.valid_until,
        status          = "pending",
        document_json   = doc_dict,
        geometry_summary = doc.geometry_summary,
        breakdown_json  = doc.breakdown,
        qty_breaks_json = [asdict(li) for li in doc.line_items],
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    return _quote_to_out(quote)


@router.get("", response_model=list[QuoteOut], summary="List my quotations")
def list_quotes(
    file_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[QuoteOut]:
    owner = _owner_key(principal)
    q = db.query(Quote).filter(Quote.owner_sub == owner)
    if file_id:
        q = q.filter(Quote.file_id == file_id)
    if status:
        q = q.filter(Quote.status == status)
    quotes = q.order_by(Quote.created_at.desc()).limit(limit).all()
    return [_quote_to_out(qr) for qr in quotes]


@router.get("/{quote_id}", response_model=QuoteOut, summary="Get a quotation")
def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> QuoteOut:
    owner = _owner_key(principal)
    quote = db.query(Quote).filter(Quote.quote_id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.owner_sub != owner:
        raise HTTPException(status_code=403, detail="Access denied")
    return _quote_to_out(quote)


@router.post("/{quote_id}/approve", response_model=OrderOut, summary="Approve quote → create production order")
def approve_quote(
    quote_id: str,
    body: ApproveQuoteRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> OrderOut:
    """
    Approve a quotation for a specific quantity.
    Creates a production order and marks the quote as approved.
    """
    owner = _owner_key(principal)
    quote = db.query(Quote).filter(Quote.quote_id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.owner_sub != owner:
        raise HTTPException(status_code=403, detail="Access denied")
    if quote.status not in ("pending", "sent"):
        raise HTTPException(
            status_code=422,
            detail=f"Quote cannot be approved (status: {quote.status})"
        )

    # Find the matching qty break
    qty_breaks = quote.qty_breaks_json or []
    matched = next((qb for qb in qty_breaks if qb["qty"] == body.qty), None)
    if not matched:
        # If not exact match, use closest qty above
        above = [qb for qb in qty_breaks if qb["qty"] >= body.qty]
        if above:
            matched = min(above, key=lambda x: x["qty"])
        elif qty_breaks:
            matched = qty_breaks[-1]
        else:
            raise HTTPException(status_code=422, detail="No price available for this quantity")

    order_seq = db.query(ProductionOrder).filter(
        ProductionOrder.quote_id == quote_id
    ).count() + 1

    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    order = ProductionOrder(
        order_id       = order_id,
        order_number   = _order_number(quote.quote_number, order_seq),
        quote_id       = quote_id,
        file_id        = quote.file_id,
        owner_sub      = owner,
        qty            = body.qty,
        unit_price_eur = matched["unit_price_eur"],
        total_eur      = matched["unit_price_eur"] * body.qty,
        lead_days      = matched.get("lead_days", 10),
        currency       = quote.currency,
        status         = "queued",
        notes          = body.notes,
        customer_po    = body.customer_po,
    )
    quote.status = "approved"
    db.add(order)
    db.add(quote)
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.post("/{quote_id}/reject", summary="Reject a quotation")
def reject_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> dict:
    owner = _owner_key(principal)
    quote = db.query(Quote).filter(Quote.quote_id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.owner_sub != owner:
        raise HTTPException(status_code=403, detail="Access denied")
    quote.status = "rejected"
    db.add(quote)
    db.commit()
    return {"status": "rejected", "quote_id": quote_id}


# ---------------------------------------------------------------------------
# Production order endpoints
# ---------------------------------------------------------------------------

@router.get("/orders/list", response_model=list[OrderOut], summary="List my production orders")
def list_orders(
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> list[OrderOut]:
    owner = _owner_key(principal)
    q = db.query(ProductionOrder).filter(ProductionOrder.owner_sub == owner)
    if status:
        q = q.filter(ProductionOrder.status == status)
    orders = q.order_by(ProductionOrder.created_at.desc()).limit(limit).all()
    return [_order_to_out(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderOut, summary="Get production order status")
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> OrderOut:
    owner = _owner_key(principal)
    order = db.query(ProductionOrder).filter(ProductionOrder.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.owner_sub != owner:
        raise HTTPException(status_code=403, detail="Access denied")
    return _order_to_out(order)
