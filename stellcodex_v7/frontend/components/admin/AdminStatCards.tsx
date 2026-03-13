import { Panel } from "@/components/primitives/Panel";

export interface AdminStatCardsProps {
  queues: number;
  failedJobs: number;
  files: number;
  users: number;
}

export function AdminStatCards({ queues, failedJobs, files, users }: AdminStatCardsProps) {
  return (
    <div className="sc-grid sc-grid-2">
      <Panel title="Queues"><strong>{queues}</strong></Panel>
      <Panel title="Failed jobs"><strong>{failedJobs}</strong></Panel>
      <Panel title="Files"><strong>{files}</strong></Panel>
      <Panel title="Users"><strong>{users}</strong></Panel>
    </div>
  );
}
