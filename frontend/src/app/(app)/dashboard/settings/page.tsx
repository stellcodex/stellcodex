import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function DashboardSettingsPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Profile & Settings"
        description="Account, security, and preferences."
        crumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Settings" },
        ]}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <EmptyState
          title="Profile"
          description="Profile fields will appear once account endpoints are connected."
        />
        <EmptyState
          title="Security"
          description="Security settings will appear once auth integrations are enabled."
        />
        <EmptyState
          title="Preferences"
          description="Viewer preferences will appear once settings are defined."
        />
      </div>
    </div>
  );
}
