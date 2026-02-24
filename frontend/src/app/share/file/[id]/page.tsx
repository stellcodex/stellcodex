import { AppShell } from "@/components/layout/AppShell";
import { FileDetail } from "@/components/share/FileDetail";

export default async function ShareFilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <FileDetail fileId={id} />
    </AppShell>
  );
}

