import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function AdminApprovalsPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Approval Queue"
        description="Review critical actions before execution."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Approvals" }]}
      />
      <EmptyState
        title="The approval queue is empty"
        description="Approvals will appear here once the endpoint is connected."
      />
    </div>
  );
}
