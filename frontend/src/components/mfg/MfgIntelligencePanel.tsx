"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch, getApiBase } from "@/lib/apiClient";

const API_BASE = getApiBase();

// ─── Types ────────────────────────────────────────────────────────────────

type QtyBreak = {
  qty: number;
  unit_price_eur: number;
  total_eur: number;
  lead_days: number;
  discount_pct: number;
};

type Breakdown = {
  material_kg: number;
  material_cost_eur: number;
  setup_hr: number;
  setup_cost_eur: number;
  cycle_hr: number;
  cycle_cost_eur: number;
  overhead_eur: number;
  unit_price_eur: number;
  minimum_applied: boolean;
};

type GeometrySummary = {
  bbox_mm: { x: number; y: number; z: number };
  diagonal_mm: number;
  volume_cm3: number;
  hole_count: number;
  has_threads: boolean;
  surfaces: { plane: number; cylindrical: number; conical: number };
  face_count: number;
  complexity: string;
  part_count: number;
};

type Quote = {
  quote_id: string;
  quote_number: string;
  process: string;
  process_label: string;
  material_id: string;
  material_label: string;
  currency: string;
  issued_date: string;
  valid_until: string;
  status: string;
  qty_breaks: QtyBreak[];
  geometry_summary: GeometrySummary | null;
  breakdown_qty1: Breakdown | null;
  dfm_notes: string[];
  technical_notes: string[];
  whatsapp_text: string;
};

type Material = {
  id: string;
  label: string;
  density_g_cm3: number;
  eur_per_kg: number;
};

type MfgPanelProps = {
  fileId: string;
  filename: string;
};

// ─── API helpers ──────────────────────────────────────────────────────────

async function fetchMaterials(): Promise<Material[]> {
  const res = await apiFetch(`${API_BASE}/quotes/materials`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.materials ?? [];
}

async function generateQuote(
  fileId: string,
  materialId: string,
  quantities: number[],
): Promise<Quote> {
  const res = await apiFetch(`${API_BASE}/quotes/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, material_id: materialId, quantities }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Quote generation failed");
  }
  return res.json();
}

async function approveQuote(quoteId: string, qty: number, customerPo?: string): Promise<{ order_id: string; order_number: string; status: string }> {
  const res = await apiFetch(`${API_BASE}/quotes/${quoteId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ qty, customer_po: customerPo }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Approval failed");
  }
  return res.json();
}

// ─── Sub-components ───────────────────────────────────────────────────────

function ComplexityBadge({ label }: { label: string }) {
  const colors: Record<string, string> = {
    LOW: "bg-emerald-900/30 text-emerald-400 border-emerald-700",
    MED: "bg-yellow-900/30 text-yellow-400 border-yellow-700",
    HIGH: "bg-red-900/30 text-red-400 border-red-700",
    UNKNOWN: "bg-slate-800 text-slate-400 border-slate-700",
  };
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium border ${colors[label] ?? colors.UNKNOWN}`}>
      {label}
    </span>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-slate-500 uppercase tracking-wide">{label}</span>
      <span className="text-sm font-medium text-slate-200">{value}</span>
    </div>
  );
}

function GeometrySection({ geo }: { geo: GeometrySummary }) {
  const { bbox_mm, diagonal_mm, volume_cm3, hole_count, has_threads, surfaces, face_count, complexity, part_count } = geo;
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Geometry</span>
        <ComplexityBadge label={complexity} />
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        <Stat
          label="Bounding Box"
          value={`${bbox_mm.x.toFixed(1)} × ${bbox_mm.y.toFixed(1)} × ${bbox_mm.z.toFixed(1)} mm`}
        />
        <Stat label="Diagonal" value={`${diagonal_mm.toFixed(1)} mm`} />
        {volume_cm3 > 0 && <Stat label="Volume" value={`${volume_cm3.toFixed(1)} cm³`} />}
        <Stat label="Parts" value={part_count} />
        <Stat label="Faces" value={face_count} />
        <Stat label="Holes" value={hole_count} />
        {surfaces.cylindrical > 0 && <Stat label="Cylindrical Surfs" value={surfaces.cylindrical} />}
        {surfaces.plane > 0 && <Stat label="Plane Surfs" value={surfaces.plane} />}
        {has_threads && <Stat label="Threads" value="Detected" />}
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────

export function MfgIntelligencePanel({ fileId, filename }: MfgPanelProps) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [selectedMaterial, setSelectedMaterial] = useState("steel_1018");
  const [quantities] = useState([1, 5, 10, 25, 50]);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [selectedQty, setSelectedQty] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderResult, setOrderResult] = useState<{ order_number: string } | null>(null);
  const [customerPo, setCustomerPo] = useState("");

  useEffect(() => {
    fetchMaterials().then(setMaterials).catch(() => {});
  }, []);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    setError(null);
    setQuote(null);
    setOrderResult(null);
    try {
      const q = await generateQuote(fileId, selectedMaterial, quantities);
      setQuote(q);
      setSelectedQty(q.qty_breaks[0]?.qty ?? 1);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [fileId, selectedMaterial, quantities]);

  const handleApprove = useCallback(async () => {
    if (!quote) return;
    setApproving(true);
    setError(null);
    try {
      const result = await approveQuote(quote.quote_id, selectedQty, customerPo || undefined);
      setOrderResult({ order_number: result.order_number });
      setQuote((q) => q ? { ...q, status: "approved" } : q);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setApproving(false);
    }
  }, [quote, selectedQty, customerPo]);

  const selectedBreak = quote?.qty_breaks.find((qb) => qb.qty === selectedQty) ?? quote?.qty_breaks[0];

  return (
    <div className="flex flex-col gap-3 text-slate-100">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Manufacturing Intelligence
        </span>
      </div>

      {/* Material selector */}
      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-400">Material</label>
        <select
          value={selectedMaterial}
          onChange={(e) => setSelectedMaterial(e.target.value)}
          className="h-9 rounded-lg border border-slate-600 bg-slate-800 px-3 text-sm text-slate-200 focus:border-blue-500 focus:outline-none"
          disabled={loading}
        >
          {materials.length === 0 && (
            <option value="steel_1018">Carbon Steel 1018</option>
          )}
          {materials.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      {/* Generate button */}
      {!quote && (
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex h-9 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Extracting geometry & pricing…
            </>
          ) : (
            <>⚡ Generate Quote</>
          )}
        </button>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-700 bg-red-900/20 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Quote result */}
      {quote && (
        <div className="flex flex-col gap-3">
          {/* Process badge */}
          <div className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/50 p-3">
            <div>
              <div className="text-xs text-slate-400">Process</div>
              <div className="text-sm font-semibold text-white">{quote.process_label}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400">Quote {quote.quote_number}</div>
              <div className="text-xs text-slate-500">Valid until {quote.valid_until}</div>
            </div>
          </div>

          {/* Geometry */}
          {quote.geometry_summary && <GeometrySection geo={quote.geometry_summary} />}

          {/* Pricing grid */}
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              Pricing ({quote.currency})
            </div>
            <div className="overflow-hidden rounded border border-slate-700">
              <table className="w-full text-xs">
                <thead className="bg-slate-700/60">
                  <tr>
                    <th className="px-2 py-1.5 text-left font-medium text-slate-400">Qty</th>
                    <th className="px-2 py-1.5 text-right font-medium text-slate-400">Unit</th>
                    <th className="px-2 py-1.5 text-right font-medium text-slate-400">Total</th>
                    <th className="px-2 py-1.5 text-right font-medium text-slate-400">Lead</th>
                  </tr>
                </thead>
                <tbody>
                  {quote.qty_breaks.map((qb) => (
                    <tr
                      key={qb.qty}
                      onClick={() => setSelectedQty(qb.qty)}
                      className={`cursor-pointer border-t border-slate-700 transition-colors ${
                        selectedQty === qb.qty ? "bg-blue-600/20" : "hover:bg-slate-700/30"
                      }`}
                    >
                      <td className="px-2 py-1.5 font-medium text-slate-200">
                        {qb.qty}
                        {qb.discount_pct > 0 && (
                          <span className="ml-1 text-emerald-400">-{qb.discount_pct}%</span>
                        )}
                      </td>
                      <td className="px-2 py-1.5 text-right text-slate-200">
                        {qb.unit_price_eur.toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-2 py-1.5 text-right font-semibold text-white">
                        {qb.total_eur.toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-2 py-1.5 text-right text-slate-400">{qb.lead_days}d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Cost breakdown for qty=1 */}
            {quote.breakdown_qty1 && (
              <details className="mt-2">
                <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-400">
                  Cost breakdown (qty=1)
                </summary>
                <div className="mt-1.5 grid grid-cols-2 gap-1 text-xs text-slate-400">
                  <span>Material ({quote.breakdown_qty1.material_kg.toFixed(2)} kg)</span>
                  <span className="text-right">€{quote.breakdown_qty1.material_cost_eur.toFixed(2)}</span>
                  <span>Setup ({quote.breakdown_qty1.setup_hr.toFixed(1)} hr)</span>
                  <span className="text-right">€{quote.breakdown_qty1.setup_cost_eur.toFixed(2)}</span>
                  <span>Cycle ({quote.breakdown_qty1.cycle_hr.toFixed(2)} hr)</span>
                  <span className="text-right">€{quote.breakdown_qty1.cycle_cost_eur.toFixed(2)}</span>
                  <span>Overhead + Margin</span>
                  <span className="text-right">€{(quote.breakdown_qty1.overhead_eur + (quote.breakdown_qty1.unit_price_eur - (quote.breakdown_qty1.material_cost_eur + quote.breakdown_qty1.setup_cost_eur + quote.breakdown_qty1.cycle_cost_eur + quote.breakdown_qty1.overhead_eur))).toFixed(2)}</span>
                  <span className="font-semibold text-white">Total</span>
                  <span className="text-right font-semibold text-white">€{quote.breakdown_qty1.unit_price_eur.toFixed(2)}</span>
                </div>
              </details>
            )}
          </div>

          {/* DFM notes */}
          {quote.dfm_notes.length > 0 && (
            <div className="rounded-lg border border-yellow-700/50 bg-yellow-900/10 p-3">
              <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-yellow-400">
                ⚠ DFM Notes
              </div>
              <ul className="flex flex-col gap-1">
                {quote.dfm_notes.map((note, i) => (
                  <li key={i} className="text-xs text-yellow-300/80">• {note}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Approval section */}
          {orderResult ? (
            <div className="rounded-lg border border-emerald-700 bg-emerald-900/20 p-3 text-center">
              <div className="text-sm font-semibold text-emerald-400">✓ Order Created</div>
              <div className="mt-1 text-xs text-emerald-300">{orderResult.order_number}</div>
            </div>
          ) : quote.status === "approved" ? (
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-2 text-center text-xs text-slate-400">
              Quote approved
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <input
                type="text"
                placeholder="Your PO# (optional)"
                value={customerPo}
                onChange={(e) => setCustomerPo(e.target.value)}
                className="h-8 rounded-lg border border-slate-600 bg-slate-800 px-3 text-xs text-slate-200 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
              />
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex h-9 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
              >
                {approving ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Placing Order…
                  </>
                ) : (
                  <>✓ Approve — Qty {selectedQty} @ €{(selectedBreak?.unit_price_eur ?? 0).toFixed(2)}/pc</>
                )}
              </button>
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="text-xs text-slate-500 hover:text-slate-400 transition-colors"
              >
                Re-generate with different material
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
