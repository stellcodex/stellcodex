import { Panel } from "@/components/primitives/Panel";

export interface HealthSummaryProps {
  data: Record<string, unknown> | null;
}

export function HealthSummary({ data }: HealthSummaryProps) {
  return (
    <Panel title="Health summary">
      <dl className="sc-kv">
        {Object.entries(data || {}).map(([key, value]) => (
          <>
            <dt key={`${key}-dt`}>{key}</dt>
            <dd key={`${key}-dd`}>{String(value)}</dd>
          </>
        ))}
      </dl>
    </Panel>
  );
}
