import type { FileTimelineEvent } from "@/lib/contracts/files";
import { Panel } from "@/components/primitives/Panel";

export interface FileStatusTimelineProps {
  events: FileTimelineEvent[];
}

export function FileStatusTimeline({ events }: FileStatusTimelineProps) {
  return (
    <Panel title="Status timeline">
      <div className="sc-stack">
        {events.length > 0 ? (
          events.map((event) => (
            <div key={event.id} className="sc-inline" style={{ justifyContent: "space-between" }}>
              <span>{event.label}</span>
              <span className="sc-muted">{event.timestamp || event.status}</span>
            </div>
          ))
        ) : (
          <span className="sc-muted">No status events yet</span>
        )}
      </div>
    </Panel>
  );
}
