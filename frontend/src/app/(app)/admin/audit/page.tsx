import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function AdminAuditPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Audit Logs"
        description="All critical actions are recorded."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Audit" }]}
      />
      <EmptyState
        title="Audit logs not wired"
        description="Audit entries will appear once the audit endpoint is connected."
      />
    </div>
  );
}
