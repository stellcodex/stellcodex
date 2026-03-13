import type { DfmReportSummary } from "@/lib/contracts/dfm";
import { Button } from "@/components/primitives/Button";
import { Panel } from "@/components/primitives/Panel";

export interface DfmReportPanelProps {
  report: DfmReportSummary | null;
  onRerun: () => void;
  running?: boolean;
}

export function DfmReportPanel({ report, onRerun, running = false }: DfmReportPanelProps) {
  return (
    <Panel
      title="DFM report"
      actions={
        <Button variant="ghost" onClick={onRerun} loading={running}>
          Run DFM
        </Button>
      }
    >
      <div className="sc-stack">
        <span>{report?.summary || "DFM report not generated yet"}</span>
        {report?.pdfUrl ? (
          <a href={report.pdfUrl} target="_blank" rel="noreferrer">
            Open PDF
          </a>
        ) : null}
      </div>
    </Panel>
  );
}
