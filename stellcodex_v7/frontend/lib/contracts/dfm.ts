export type RiskSummary = {
  id: string;
  severity: "low" | "medium" | "high" | "critical" | "unknown";
  category?: string | null;
  title: string;
  description?: string | null;
  recommendation?: string | null;
  approvalRequired?: boolean;
};

export type DfmReportSummary = {
  status: "not_ready" | "ready" | "failed" | "unknown";
  createdAt?: string | null;
  summary?: string | null;
  pdfUrl?: string | null;
};
