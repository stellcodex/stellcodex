import { SectionHeader } from "@/components/layout/SectionHeader";
import { EmptyState } from "@/components/ui/StateBlocks";

export default function AdminFilesPage() {
  return (
    <div className="space-y-6">
      <SectionHeader
        title="Files"
        description="Moderation and compliance."
        crumbs={[{ label: "Admin", href: "/admin" }, { label: "Files" }]}
      />
      <EmptyState
        title="Moderation not wired"
        description="Connect the admin files endpoint to populate moderation data."
      />
    </div>
  );
}
