import { EmptyState } from "@/components/primitives/EmptyState";
import { Panel } from "@/components/primitives/Panel";
import type { DfmRecord } from "@/lib/contracts/ui";

export interface DfmReportPanelProps {
  report: DfmRecord | null;
  rerunSupported: boolean;
}

export function DfmReportPanel({ report, rerunSupported }: DfmReportPanelProps) {
  return (
    <Panel title="DFM Report">
      {!report ? (
        <EmptyState description="No DFM report exists for this file yet." title="DFM report unavailable" />
      ) : (
        <div className="space-y-4 text-sm">
          <div className="flex justify-between">
            <span className="text-[var(--foreground-soft)]">Status gate</span>
            <span className="font-medium">{report.statusGate}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[var(--foreground-soft)]">Rerun support</span>
            <span className="font-medium">{rerunSupported ? "Available" : "Not exposed by backend"}</span>
          </div>
          <div className="rounded-[12px] border border-[#eeeeee] px-3 py-3">
            <div className="text-sm font-medium text-[var(--foreground-strong)]">Geometry report</div>
            <pre className="mt-2 whitespace-pre-wrap text-sm text-[var(--foreground-muted)]">{JSON.stringify(report.geometryReport, null, 2)}</pre>
          </div>
        </div>
      )}
    </Panel>
  );
}
