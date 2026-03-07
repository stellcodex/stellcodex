"""
app/services/cost_estimator.py

Manufacturing Cost Estimator.

Calculates cost from geometry + process + material for a given quantity.

Pricing is configurable via environment variables so the founder can tune margins
without touching code.

All costs are in EUR by default.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# Material catalogue (density g/cm³, raw material cost EUR/kg)
# ---------------------------------------------------------------------------

MATERIAL_DB: dict[str, dict] = {
    # Steels
    "steel_1018":    {"label": "Carbon Steel 1018",          "density": 7.87, "eur_per_kg": 2.5,  "machinability": 1.0},
    "steel_4140":    {"label": "Steel 42CrMo4 (4140)",       "density": 7.85, "eur_per_kg": 3.5,  "machinability": 0.85},
    "steel_1.2344":  {"label": "Tool Steel H13 (1.2344)",    "density": 7.80, "eur_per_kg": 8.0,  "machinability": 0.60},
    "steel_304":     {"label": "Stainless Steel 304",        "density": 7.93, "eur_per_kg": 6.0,  "machinability": 0.70},
    "steel_316l":    {"label": "Stainless Steel 316L",       "density": 7.99, "eur_per_kg": 7.5,  "machinability": 0.65},
    # Aluminium
    "alu_6061":      {"label": "Aluminium 6061-T6",          "density": 2.70, "eur_per_kg": 5.5,  "machinability": 2.0},
    "alu_7075":      {"label": "Aluminium 7075-T6",          "density": 2.81, "eur_per_kg": 8.0,  "machinability": 1.8},
    "alu_5083":      {"label": "Aluminium 5083",             "density": 2.66, "eur_per_kg": 5.0,  "machinability": 1.7},
    # Brass / Bronze
    "brass_360":     {"label": "Brass C360 (Free Machining)", "density": 8.50, "eur_per_kg": 9.0, "machinability": 3.0},
    "bronze_c93200": {"label": "Bronze C93200 (SAE 660)",    "density": 8.91, "eur_per_kg": 12.0, "machinability": 2.5},
    # Copper
    "copper_c110":   {"label": "Copper C110 (ETP)",          "density": 8.94, "eur_per_kg": 14.0, "machinability": 2.0},
    # Titanium
    "titanium_gr2":  {"label": "Titanium Grade 2 (CP Ti)",   "density": 4.50, "eur_per_kg": 35.0, "machinability": 0.35},
    "titanium_gr5":  {"label": "Titanium Grade 5 (Ti-6Al-4V)","density": 4.43, "eur_per_kg": 55.0,"machinability": 0.30},
    # Plastics
    "abs":           {"label": "ABS",                         "density": 1.05, "eur_per_kg": 4.0, "machinability": 3.0},
    "pom":           {"label": "POM (Delrin/Acetal)",         "density": 1.41, "eur_per_kg": 5.5, "machinability": 3.5},
    "pa6":           {"label": "Nylon PA6",                   "density": 1.14, "eur_per_kg": 5.0, "machinability": 3.0},
    "peek":          {"label": "PEEK",                        "density": 1.31, "eur_per_kg": 90.0, "machinability": 1.5},
    "ptfe":          {"label": "PTFE (Teflon)",               "density": 2.17, "eur_per_kg": 35.0, "machinability": 2.5},
}

# Default material if nothing is specified
DEFAULT_MATERIAL = "steel_1018"

# ---------------------------------------------------------------------------
# Machine rates (EUR / hour) and setup times (hours) by process
# ---------------------------------------------------------------------------

MACHINE_RATES: dict[str, dict] = {
    "cnc_turning":   {"rate_eur_hr": float(os.getenv("RATE_CNC_TURNING",   "75")),  "setup_hr": 1.5},
    "cnc_milling":   {"rate_eur_hr": float(os.getenv("RATE_CNC_MILLING",   "90")),  "setup_hr": 2.0},
    "sheet_metal":   {"rate_eur_hr": float(os.getenv("RATE_SHEET_METAL",   "60")),  "setup_hr": 0.5},
    "laser_cutting": {"rate_eur_hr": float(os.getenv("RATE_LASER",         "50")),  "setup_hr": 0.25},
    "waterjet":      {"rate_eur_hr": float(os.getenv("RATE_WATERJET",      "55")),  "setup_hr": 0.25},
    "3d_printing":   {"rate_eur_hr": float(os.getenv("RATE_3DPRINT",       "25")),  "setup_hr": 0.5},
    "casting":       {"rate_eur_hr": float(os.getenv("RATE_CASTING",       "80")),  "setup_hr": 4.0},
    "welding":       {"rate_eur_hr": float(os.getenv("RATE_WELDING",       "55")),  "setup_hr": 1.0},
    "unknown":       {"rate_eur_hr": float(os.getenv("RATE_UNKNOWN",       "80")),  "setup_hr": 2.0},
}

OVERHEAD_RATE  = float(os.getenv("OVERHEAD_RATE", "0.30"))   # 30% overhead on direct costs
TARGET_MARGIN  = float(os.getenv("TARGET_MARGIN", "0.35"))   # 35% gross margin
MIN_ORDER_EUR  = float(os.getenv("MIN_ORDER_EUR",  "150"))   # minimum order value
CURRENCY       = os.getenv("QUOTE_CURRENCY", "EUR")

# Quantity discount tiers (beyond qty_min, discount_pct off unit price)
QTY_DISCOUNT_TIERS: list[tuple[int, float]] = [
    (5,   0.05),
    (10,  0.10),
    (25,  0.15),
    (50,  0.20),
    (100, 0.25),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CostBreakdown:
    material_kg: float
    material_cost_eur: float
    setup_hr: float
    setup_cost_eur: float
    cycle_hr: float
    cycle_cost_eur: float
    overhead_eur: float
    total_direct_eur: float
    unit_cost_eur: float
    margin_eur: float
    unit_price_eur: float
    minimum_applied: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class QuoteEstimate:
    material_id: str
    material_label: str
    process: str
    process_label: str
    currency: str
    qty_breaks: list[dict]          # [{qty, unit_price, total_price, lead_days}]
    breakdown_qty1: CostBreakdown   # detailed breakdown for qty=1
    notes: list[str]

    def to_dict(self) -> dict:
        d = asdict(self)
        # convert nested dataclass
        d["breakdown_qty1"] = self.breakdown_qty1.to_dict()
        return d


# ---------------------------------------------------------------------------
# Estimation helpers
# ---------------------------------------------------------------------------

def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _cycle_time_hours(
    bbox: dict,
    volume_mm3: float,
    process: str,
    setup_count: int,
    face_count: int,
    n_holes: int,
    complexity_label: str,
    machinability: float,
    quantity: int,
) -> float:
    """
    Estimate cycle time per part in hours.
    Returns pure cycle time (not including setup which is amortised separately).
    """
    bx = _safe_float(bbox.get("x"), 50.0)
    by = _safe_float(bbox.get("y"), 50.0)
    bz = _safe_float(bbox.get("z"), 50.0)

    dim_max = max(bx, by, bz)
    dim_vol = bx * by * bz

    complexity_mult = {"LOW": 0.7, "MED": 1.0, "HIGH": 1.5}.get(complexity_label, 1.0)

    if process == "cnc_turning":
        # Empirical: base ~0.5 hr for 100mm part, scales with length and complexity
        base = 0.5 + dim_max / 400.0
        hole_add = n_holes * 0.03
        t = (base + hole_add) * complexity_mult / machinability
        return round(max(0.25, t), 3)

    elif process == "cnc_milling":
        base = 1.0 + face_count / 150.0
        hole_add = n_holes * 0.05
        t = (base + hole_add) * complexity_mult / machinability
        return round(max(0.5, t), 3)

    elif process in ("sheet_metal",):
        # Mostly laser / punching + bending
        t = 0.25 + face_count / 200.0
        return round(max(0.1, t), 3)

    elif process in ("laser_cutting", "waterjet"):
        # Fast: estimate from perimeter (approximate from max dims)
        perimeter = 2 * (bx + by) / 1000.0  # meters
        t = perimeter * 0.05 + 0.05          # ~5 min/meter + 5min load
        return round(max(0.05, t), 3)

    elif process == "3d_printing":
        # Volume-based: ~15 cm³/hr for FDM, ~5 cm³/hr for SLA
        vol_cm3 = volume_mm3 / 1000.0
        t = vol_cm3 / 12.0 + 0.5
        return round(max(0.5, t), 3)

    elif process == "casting":
        return round(max(1.0, volume_mm3 / 500_000.0), 3)

    elif process == "welding":
        # Estimate from diagonal
        diag_m = math.sqrt(bx**2 + by**2 + bz**2) / 1000.0
        t = diag_m * 2.0 + 0.5
        return round(max(0.5, t * complexity_mult), 3)

    return round(max(0.5, dim_vol / 2_000_000.0 * complexity_mult), 3)


def _lead_days(process: str, qty: int, complexity_label: str) -> int:
    """Estimate standard lead time in working days."""
    base: dict[str, int] = {
        "cnc_turning":   5,
        "cnc_milling":   7,
        "sheet_metal":   5,
        "laser_cutting": 3,
        "waterjet":      3,
        "3d_printing":   3,
        "casting":       15,
        "welding":       7,
        "unknown":       10,
    }
    days = base.get(process, 10)
    # Quantity scaling
    days += int(math.log10(max(1, qty)) * 2)
    # Complexity scaling
    if complexity_label == "HIGH":
        days += 3
    return max(days, 2)


def _qty_discount(qty: int) -> float:
    """Return discount fraction for a given quantity."""
    discount = 0.0
    for min_qty, pct in QTY_DISCOUNT_TIERS:
        if qty >= min_qty:
            discount = pct
    return discount


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def estimate_cost(
    geometry_meta: dict[str, Any],
    process: str,
    process_label: str,
    setup_count: int,
    *,
    material_id: str = DEFAULT_MATERIAL,
    quantities: list[int] | None = None,
) -> QuoteEstimate:
    """
    Estimate manufacturing cost for a part.

    Parameters
    ----------
    geometry_meta   : dict from step_extractor / geometry_meta_json
    process         : snake_case process from ProcessResult.process
    process_label   : human-readable process label
    setup_count     : number of CNC setups estimated by classifier
    material_id     : key from MATERIAL_DB (defaults to steel_1018)
    quantities      : list of quantities to price (default [1, 5, 10, 25, 50])

    Returns
    -------
    QuoteEstimate
    """
    if quantities is None:
        quantities = [1, 5, 10, 25, 50]

    # --- Resolve material ---
    mat = MATERIAL_DB.get(material_id) or MATERIAL_DB[DEFAULT_MATERIAL]
    density_g_cm3     = mat["density"]
    eur_per_kg        = mat["eur_per_kg"]
    machinability     = mat["machinability"]  # > 1 means faster, < 1 means slower

    # --- Geometry ---
    bbox = geometry_meta.get("bbox") or {}
    vol_mm3 = _safe_float(geometry_meta.get("volume"), 0)
    if vol_mm3 <= 0:
        bx = _safe_float(bbox.get("x"), 50.0)
        by = _safe_float(bbox.get("y"), 50.0)
        bz = _safe_float(bbox.get("z"), 50.0)
        vol_mm3 = bx * by * bz

    # Correction: actual part volume is typically 25-60% of bounding box for machined parts
    # Use a process-dependent fill factor
    fill_factors = {
        "cnc_turning":   0.55,  # turning = mostly solid cylinder
        "cnc_milling":   0.40,  # milling removes material
        "sheet_metal":   0.15,  # thin sheet
        "laser_cutting": 0.10,
        "waterjet":      0.10,
        "3d_printing":   0.30,
        "casting":       0.50,
        "welding":       0.25,
        "unknown":       0.35,
    }
    fill = fill_factors.get(process, 0.35)
    part_vol_mm3 = vol_mm3 * fill
    part_vol_cm3 = part_vol_mm3 / 1000.0
    # For raw material block we use bounding box volume (you buy the block)
    raw_vol_cm3  = vol_mm3 / 1000.0

    weight_kg = (raw_vol_cm3 * density_g_cm3) / 1000.0
    material_cost = weight_kg * eur_per_kg

    # --- Machine / process time for qty=1 ---
    complexity_d = geometry_meta.get("complexity") or {}
    complexity_lbl = str(complexity_d.get("label", "MED")).upper()
    face_count = _safe_int(complexity_d.get("face_count", 0))
    holes = geometry_meta.get("holes") or []
    n_holes = len(holes)

    machine_info = MACHINE_RATES.get(process, MACHINE_RATES["unknown"])
    rate_eur_hr  = machine_info["rate_eur_hr"]
    setup_hr     = machine_info["setup_hr"] * setup_count

    cycle_hr = _cycle_time_hours(
        bbox, vol_mm3, process, setup_count, face_count, n_holes, complexity_lbl, machinability, 1
    )

    setup_cost_eur = setup_hr * rate_eur_hr
    cycle_cost_eur = cycle_hr * rate_eur_hr

    direct_cost = material_cost + setup_cost_eur + cycle_cost_eur
    overhead    = direct_cost * OVERHEAD_RATE
    total_direct = direct_cost + overhead
    margin_eur  = total_direct * TARGET_MARGIN / (1.0 - TARGET_MARGIN)
    unit_price  = total_direct + margin_eur

    minimum_applied = False
    if unit_price < MIN_ORDER_EUR:
        unit_price = MIN_ORDER_EUR
        minimum_applied = True

    breakdown_qty1 = CostBreakdown(
        material_kg        = round(weight_kg, 4),
        material_cost_eur  = round(material_cost, 2),
        setup_hr           = round(setup_hr, 3),
        setup_cost_eur     = round(setup_cost_eur, 2),
        cycle_hr           = round(cycle_hr, 3),
        cycle_cost_eur     = round(cycle_cost_eur, 2),
        overhead_eur       = round(overhead, 2),
        total_direct_eur   = round(total_direct, 2),
        unit_cost_eur      = round(total_direct, 2),
        margin_eur         = round(margin_eur, 2),
        unit_price_eur     = round(unit_price, 2),
        minimum_applied    = minimum_applied,
    )

    # --- Quantity breaks ---
    qty_breaks: list[dict] = []
    for qty in quantities:
        discount = _qty_discount(qty)
        # Setup amortised over qty
        amortised_setup = setup_cost_eur / max(1, qty)
        unit_direct = material_cost + amortised_setup + cycle_cost_eur
        unit_overhead = unit_direct * OVERHEAD_RATE
        unit_total = unit_direct + unit_overhead
        unit_margin = unit_total * TARGET_MARGIN / (1.0 - TARGET_MARGIN)
        up = (unit_total + unit_margin) * (1.0 - discount)
        if up < MIN_ORDER_EUR / qty:
            up = MIN_ORDER_EUR / qty

        qty_breaks.append({
            "qty":           qty,
            "discount_pct":  round(discount * 100, 1),
            "unit_price_eur": round(up, 2),
            "total_eur":     round(up * qty, 2),
            "lead_days":     _lead_days(process, qty, complexity_lbl),
        })

    notes: list[str] = []
    if minimum_applied:
        notes.append(f"Minimum order value of {CURRENCY} {MIN_ORDER_EUR:.0f} applied.")
    if material_id not in MATERIAL_DB:
        notes.append(f"Material '{material_id}' not in catalogue; defaulted to {mat['label']}.")
    notes.append(
        f"Estimate is based on {process_label} with {setup_count} setup(s). "
        f"Actual cost depends on final drawing tolerances and surface finish."
    )

    return QuoteEstimate(
        material_id     = material_id,
        material_label  = mat["label"],
        process         = process,
        process_label   = process_label,
        currency        = CURRENCY,
        qty_breaks      = qty_breaks,
        breakdown_qty1  = breakdown_qty1,
        notes           = notes,
    )
