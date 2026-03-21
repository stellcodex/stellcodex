import { Button } from "@/components/primitives/Button";
import { EmptyState } from "@/components/primitives/EmptyState";
import { Input } from "@/components/primitives/Input";
import { Panel } from "@/components/primitives/Panel";
import type { RequiredInputRecord } from "@/lib/contracts/ui";

export interface RequiredInputsPanelProps {
  fields: RequiredInputRecord[];
  values: Record<string, string>;
  error: string | null;
  onChange: (key: string, value: string) => void;
  onSubmit: () => Promise<boolean>;
}

export function RequiredInputsPanel({ error, fields, onChange, onSubmit, values }: RequiredInputsPanelProps) {
  return (
    <Panel title="Required Inputs">
      {fields.length === 0 ? (
        <EmptyState description="No required inputs are currently pending for this session." title="No pending inputs" />
      ) : (
        <div className="space-y-4">
          {fields.map((field) => (
            <div className="space-y-2" key={field.key}>
              <label className="text-sm font-medium">{field.label}</label>
              <Input onChange={(event) => onChange(field.key, event.target.value)} value={values[field.key] || ""} />
            </div>
          ))}
          {error ? <div className="text-sm text-[var(--status-danger-fg)]">{error}</div> : null}
          <Button onClick={() => void onSubmit()} variant="primary">
            Submit inputs
          </Button>
        </div>
      )}
    </Panel>
  );
}
