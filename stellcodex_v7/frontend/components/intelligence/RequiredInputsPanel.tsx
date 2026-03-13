import type { RequiredInputField } from "@/lib/contracts/orchestrator";
import { Panel } from "@/components/primitives/Panel";
import { RequiredInputsForm } from "@/components/intelligence/RequiredInputsForm";

export interface RequiredInputsPanelProps {
  fields: RequiredInputField[];
  onChange: (key: string, value: RequiredInputField["value"]) => void;
  onSubmit: () => void;
}

export function RequiredInputsPanel({ fields, onChange, onSubmit }: RequiredInputsPanelProps) {
  return (
    <Panel title="Required inputs">
      {fields.length > 0 ? (
        <RequiredInputsForm fields={fields} onChange={onChange} onSubmit={onSubmit} />
      ) : (
        <span className="sc-muted">No required inputs</span>
      )}
    </Panel>
  );
}
