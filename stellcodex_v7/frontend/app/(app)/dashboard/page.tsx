import { WorkspaceRedirect } from "@/components/workspace/WorkspaceRedirect";

export default function DashboardPage() {
  // Legacy dashboard now resolves into the canonical suite home.
  return <WorkspaceRedirect />;
}
