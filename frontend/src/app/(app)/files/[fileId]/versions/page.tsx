import { VersionsTable } from "@/components/files/VersionsTable";
import { PageHeader } from "@/components/shell/PageHeader";

export default async function FileVersionsPage({ params }: { params: Promise<{ fileId: string }> }) {
  const { fileId } = await params;
  return (
    <div className="space-y-6">
      <PageHeader
        subtitle="The versions route is present, but it remains fail-closed until the backend exposes version history."
        title={`Versions · ${fileId}`}
      />
      <VersionsTable supported={false} />
    </div>
  );
}
