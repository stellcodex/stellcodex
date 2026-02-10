import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function AdminSystemPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="System"
        description="Settings, workers, and operational visibility."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "System" }]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          title="System settings"
          description="Connect system settings endpoints to populate this section."
        />
        <EmptyState
          title="Workers & queues"
          description="Worker status and queue metrics will appear once wired."
        />
      </div>

      <EmptyState
        title="Error summary"
        description="Error summaries will appear once aggregation is configured."
      />
    </div>
  );
}
