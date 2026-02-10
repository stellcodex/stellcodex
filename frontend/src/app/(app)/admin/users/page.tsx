import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="User Management"
        description="Roles, status, and security actions."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Users" }]}
      />
      <EmptyState
        title="Users table not wired"
        description="Connect the admin users endpoint to populate this table."
      />
    </div>
  );
}
