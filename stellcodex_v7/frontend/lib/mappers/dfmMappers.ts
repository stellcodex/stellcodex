import type { DfmReportSummary, RiskSummary } from "@/lib/contracts/dfm";

type RawRecord = Record<string, unknown>;

function normalizeSeverity(value: unknown): RiskSummary["severity"] {
  const token = String(value || "").toLowerCase();
  if (token === "critical") return "critical";
  if (token === "high") return "high";
  if (token === "medium") return "medium";
  if (token === "low") return "low";
  return "unknown";
}

function riskFromList(list: unknown, category: string): RiskSummary[] {
  if (!Array.isArray(list)) return [];
  return list.map((item, index) => {
    const row = (item && typeof item === "object" ? item : {}) as RawRecord;
    return {
      id: `${category}-${index}`,
      severity: normalizeSeverity(row.severity || row.level || (index === 0 ? "high" : "medium")),
      category,
      title:
        (typeof row.title === "string" && row.title) ||
        (typeof row.label === "string" && row.label) ||
        `${category} risk ${index + 1}`,
      description: typeof row.description === "string" ? row.description : null,
      recommendation: typeof row.recommendation === "string" ? row.recommendation : null,
      approvalRequired: Boolean(row.approval_required),
    };
  });
}

export function mapDfmReport(input: unknown): DfmReportSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const hasPayload =
    Boolean(row.dfm_findings) ||
    Array.isArray(row.wall_risks) ||
    Array.isArray(row.draft_risks) ||
    Array.isArray(row.undercut_risks) ||
    Array.isArray(row.shrinkage_warnings);
  return {
    status: hasPayload ? "ready" : "not_ready",
    createdAt: null,
    summary: hasPayload ? "Deterministic DFM findings are available." : "DFM report not generated yet",
    pdfUrl: typeof row.pdf_url === "string" ? row.pdf_url : null,
  };
}

export function mapRisks(input: unknown): RiskSummary[] {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const risks = [
    ...riskFromList(row.wall_risks, "wall"),
    ...riskFromList(row.draft_risks, "draft"),
    ...riskFromList(row.undercut_risks, "undercut"),
    ...riskFromList(row.shrinkage_warnings, "shrinkage"),
  ];
  const weight = { critical: 4, high: 3, medium: 2, low: 1, unknown: 0 };
  return risks.sort((a, b) => weight[b.severity] - weight[a.severity]);
}
