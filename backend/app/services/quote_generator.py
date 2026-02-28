"""
app/services/quote_generator.py

Quotation Generator.

Takes a cost estimate + geometry + file metadata and produces a structured
quotation document. Generates human-readable text for WhatsApp delivery
and a structured dict for JSON/PDF rendering.

Quote ID format: Q-YYYYMMDD-NNNN (e.g. Q-20260227-0001)
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

QUOTE_VALIDITY_DAYS  = int(os.getenv("QUOTE_VALIDITY_DAYS", "14"))
PAYMENT_TERMS        = os.getenv("QUOTE_PAYMENT_TERMS", "50% advance, 50% before shipment")
COMPANY_NAME         = os.getenv("COMPANY_NAME", "STELLCODEX Manufacturing")
COMPANY_EMAIL        = os.getenv("COMPANY_EMAIL", "quotes@stellcodex.com")
COMPANY_PHONE        = os.getenv("COMPANY_PHONE", "+90 xxx xxx xx xx")
COMPANY_CURRENCY     = os.getenv("QUOTE_CURRENCY", "EUR")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class QuoteLineItem:
    qty: int
    unit_price_eur: float
    total_eur: float
    lead_days: int
    discount_pct: float


@dataclass
class QuoteDocument:
    quote_id: str
    quote_number: str
    file_id: str
    filename: str
    issued_date: str        # ISO
    valid_until: str        # ISO
    process: str
    process_label: str
    material_id: str
    material_label: str
    currency: str
    payment_terms: str
    line_items: list[QuoteLineItem]
    breakdown: dict         # detailed cost breakdown for qty=1
    geometry_summary: dict  # bounding box, holes, surfaces
    dfm_notes: list[str]
    technical_notes: list[str]
    status: str             # pending | sent | approved | rejected | expired

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def to_whatsapp_text(self) -> str:
        """Return a short, human-readable WhatsApp message."""
        lines = [
            f"📋 *QUOTATION {self.quote_number}*",
            f"{'─' * 30}",
            f"*Part:* {self.filename}",
            f"*Process:* {self.process_label}",
            f"*Material:* {self.material_label}",
            f"",
            f"*Price Options:*",
        ]
        for li in self.line_items:
            lines.append(
                f"  • Qty {li.qty:3d}: {self.currency} {li.unit_price_eur:,.2f}/pc  "
                f"(Total: {self.currency} {li.total_eur:,.2f})  "
                f"Lead: {li.lead_days} days"
            )
        lines += [
            f"",
            f"*Payment:* {self.payment_terms}",
            f"*Valid until:* {self.valid_until}",
            f"",
            f"Reply *APPROVE [qty]* to confirm order.",
            f"Reply *QUESTION* for technical support.",
            f"",
            f"{COMPANY_NAME}",
            f"{COMPANY_EMAIL} | {COMPANY_PHONE}",
        ]
        if self.dfm_notes:
            lines += ["", "⚠️ *DFM Notes:*"]
            for note in self.dfm_notes[:3]:
                lines.append(f"  – {note}")
        return "\n".join(lines)

    def to_email_html(self) -> str:
        """Return basic HTML for email delivery."""
        rows = "".join(
            f"<tr><td>{li.qty}</td><td>{self.currency} {li.unit_price_eur:,.2f}</td>"
            f"<td>{self.currency} {li.total_eur:,.2f}</td><td>{li.lead_days} days</td></tr>"
            for li in self.line_items
        )
        dfm_html = (
            "<ul>" + "".join(f"<li>{n}</li>" for n in self.dfm_notes) + "</ul>"
            if self.dfm_notes else ""
        )
        return f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#1a1a2e;color:white}}.header{{background:#1a1a2e;color:white;padding:20px;border-radius:6px}}
.badge{{background:#16213e;color:#e94560;padding:4px 8px;border-radius:4px;font-size:12px}}</style>
</head><body>
<div class="header"><h2>📋 {COMPANY_NAME}</h2><p>Quotation: <strong>{self.quote_number}</strong></p></div>
<br>
<table><tr><th>Part</th><td>{self.filename}</td></tr>
<tr><th>Process</th><td>{self.process_label}</td></tr>
<tr><th>Material</th><td>{self.material_label}</td></tr>
<tr><th>Issued</th><td>{self.issued_date}</td></tr>
<tr><th>Valid Until</th><td>{self.valid_until}</td></tr>
<tr><th>Payment Terms</th><td>{self.payment_terms}</td></tr></table>
<br><h3>Price Options</h3>
<table><tr><th>Qty</th><th>Unit Price</th><th>Total</th><th>Lead Time</th></tr>
{rows}</table>
{f'<br><h3>DFM Notes</h3>{dfm_html}' if dfm_html else ''}
<br><p>To approve this quotation, reply to this email with: <strong>APPROVE [qty]</strong></p>
<p style="color:#666;font-size:12px">{COMPANY_NAME} &bull; {COMPANY_EMAIL} &bull; {COMPANY_PHONE}</p>
</body></html>"""


def _geometry_summary(geometry_meta: dict) -> dict:
    """Extract a compact geometry summary for display."""
    bbox = geometry_meta.get("bbox") or {}
    holes = geometry_meta.get("holes") or []
    surfaces = geometry_meta.get("surfaces") or {}
    complexity = geometry_meta.get("complexity") or {}
    return {
        "bbox_mm": {
            "x": round(float(bbox.get("x") or 0), 2),
            "y": round(float(bbox.get("y") or 0), 2),
            "z": round(float(bbox.get("z") or 0), 2),
        },
        "diagonal_mm": round(float(geometry_meta.get("diagonal") or 0), 2),
        "volume_cm3":  round(float(geometry_meta.get("volume") or 0) / 1000.0, 2),
        "hole_count":  len(holes),
        "has_threads": bool(geometry_meta.get("has_threads", False)),
        "surfaces": {
            "plane":       int(surfaces.get("plane", 0)),
            "cylindrical": int(surfaces.get("cylindrical", 0)),
            "conical":     int(surfaces.get("conical", 0)),
        },
        "face_count":   int(complexity.get("face_count", 0)),
        "complexity":   str(complexity.get("label", "UNKNOWN")),
        "part_count":   int(geometry_meta.get("part_count") or 1),
    }


def _quote_number(file_id: str) -> str:
    """Generate a deterministic but short quote number from file_id + date."""
    today = date.today().strftime("%Y%m%d")
    short = hashlib.md5(f"{file_id}{today}".encode()).hexdigest()[:4].upper()
    return f"Q-{today}-{short}"


def generate_quote(
    *,
    file_id: str,
    filename: str,
    quote_estimate: Any,        # QuoteEstimate from cost_estimator
    process_result: Any,        # ProcessResult from mfg_classifier
    geometry_meta: dict,
    additional_technical_notes: list[str] | None = None,
) -> QuoteDocument:
    """
    Generate a complete QuoteDocument.

    Parameters
    ----------
    file_id              : file identifier string
    filename             : original filename
    quote_estimate       : QuoteEstimate from cost_estimator.estimate_cost()
    process_result       : ProcessResult from mfg_classifier.classify_manufacturing_process()
    geometry_meta        : full geometry_meta dict
    additional_technical_notes : any extra notes to add

    Returns
    -------
    QuoteDocument — call .to_dict() to serialise, .to_whatsapp_text() for messaging
    """
    now = datetime.now(timezone.utc)
    issued   = now.date().isoformat()
    valid_until = (now + timedelta(days=QUOTE_VALIDITY_DAYS)).date().isoformat()

    line_items = [
        QuoteLineItem(
            qty            = qb["qty"],
            unit_price_eur = qb["unit_price_eur"],
            total_eur      = qb["total_eur"],
            lead_days      = qb["lead_days"],
            discount_pct   = qb.get("discount_pct", 0.0),
        )
        for qb in quote_estimate.qty_breaks
    ]

    technical_notes: list[str] = list(quote_estimate.notes)
    if additional_technical_notes:
        technical_notes.extend(additional_technical_notes)

    return QuoteDocument(
        quote_id       = f"quote_{file_id}_{now.strftime('%Y%m%d%H%M%S')}",
        quote_number   = _quote_number(file_id),
        file_id        = file_id,
        filename       = filename,
        issued_date    = issued,
        valid_until    = valid_until,
        process        = process_result.process,
        process_label  = process_result.process_label,
        material_id    = quote_estimate.material_id,
        material_label = quote_estimate.material_label,
        currency       = quote_estimate.currency,
        payment_terms  = PAYMENT_TERMS,
        line_items     = line_items,
        breakdown      = quote_estimate.breakdown_qty1.to_dict(),
        geometry_summary = _geometry_summary(geometry_meta),
        dfm_notes      = process_result.dfm_notes,
        technical_notes = technical_notes,
        status         = "pending",
    )
